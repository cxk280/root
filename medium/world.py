"""The autopoiesis ladder's medium — Rungs 1 and 2.

An organism is a flat machine-code body resident in a decaying arena. It runs
continuously; after each window of T fuel-ticks the medium applies a decay law:

  - "solvent" (Rung 1): zero every arena byte not written since the last sweep.
    Survival demands continuous re-laying of one's own bytes. Deterministic.
  - "bitrot"  (Rung 2): flip a Poisson(λ) number of random bits within the
    organism's footprint, with no sweep. Survival demands error *correction* —
    detecting and repairing damage, which an identity-copy refresh cannot do.
    Seeded per trial; vary the seed for survival statistics.

There is no external master copy in either mode (the medium maps no immortal
data region), so persistence is genuine organizational closure in the
computational medium (see AUTOPOIESIS.md). The medium produces a TRACE and
renders no verdict; the assay (medium/assay.py) does that.
"""

import random
from dataclasses import dataclass, field

from harness import config
from harness.uc import CONST, Uc, UcError, reg


def _poisson(rng: random.Random, lam: float) -> int:
    """Knuth's algorithm — number of bit flips this window (mean λ)."""
    if lam <= 0:
        return 0
    import math
    el, k, p = math.exp(-lam), 0, 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= el:
            return k - 1

ARENA_BASE = config.CODE_BASE          # 0x10000, RWX — code that writes code is the point
ARENA_SIZE = config.CODE_SIZE
DECAY_BYTES = 0x800                    # the solvent acts on the first 2 KiB of the arena
STACK_BASE = config.STACK_BASE
STACK_SIZE = config.STACK_SIZE
STACK_TOP = config.STACK_TOP


@dataclass
class Cycle:
    idx: int
    writes: int                       # distinct arena bytes written this window
    self_reads: int                   # reads that landed in the organism footprint
    integrity: float                  # fraction of birth-image bytes preserved
    rip_in_body: bool
    alive: bool
    cause: str = ""                   # death cause, when alive flips to False


@dataclass
class Life:
    organism: str
    T: int                            # sweep period, in instructions
    footprint: int                    # birth-image length (bytes)
    lifespan: int                     # cycles survived
    survived: bool                    # reached the requested lifetime
    cause: str
    cycles: list = field(default_factory=list)
    # provenance (populated when live(..., probe=True)), as arena offsets:
    exec_offsets: set = field(default_factory=set)   # bytes executed as code
    read_offsets: set = field(default_factory=set)   # bytes read as data
    write_offsets: set = field(default_factory=set)  # bytes written
    external_reads: int = 0           # reads outside the decay zone (scaffold use)

    @property
    def mean_turnover(self) -> float:
        live = [c.writes for c in self.cycles if c.alive]
        return sum(live) / len(live) if live else 0.0

    @property
    def mean_integrity(self) -> float:
        live = [c.integrity for c in self.cycles if c.alive]
        return sum(live) / len(live) if live else 0.0

    @property
    def used_boundary(self) -> bool:
        return any(c.self_reads > 0 for c in self.cycles[:8])


def live(code: bytes, T: int, lifetime: int = 200,
         body_hint: int | None = None, probe: bool = False,
         decay: str = "solvent", lam: float = 0.0, seed: int = 0,
         on_frame=None) -> Life:
    """Run one organism for up to `lifetime` windows under decay law `decay`.

    `code` is the birth image placed at ARENA_BASE; `body_hint` is its nominal
    footprint for integrity accounting (defaults to len(code)). With probe=True,
    accumulate execution/read/write provenance (offset sets) for the assay.
    For decay="bitrot", `lam` is the mean bit flips per window and `seed` makes
    the corruption stream reproducible. `on_frame`, if given, is called once per
    window with a dict (body bytes, integrity, the offsets just decayed/written,
    the execution head) for the live visualizer — opt-in, no behavior change."""
    footprint = body_hint if body_hint is not None else len(code)
    birth = code
    rng = random.Random(seed)
    R, W, X = CONST["UC_PROT_READ"], CONST["UC_PROT_WRITE"], CONST["UC_PROT_EXEC"]

    mu = Uc()
    fresh = bytearray(DECAY_BYTES)      # 1 = written since last sweep
    writes_window = [0]
    reads_self_window = [0]
    exec_off, read_off, write_off = set(), set(), set()
    external_reads = [0]

    written_now = set()                 # offsets the organism wrote this window (viz)

    def on_write(addr, size, _value):
        off = addr - ARENA_BASE
        for k in range(size):
            o = off + k
            if 0 <= o < DECAY_BYTES and not fresh[o]:
                fresh[o] = 1
                writes_window[0] += 1
            if probe and 0 <= o < DECAY_BYTES:
                write_off.add(o)
            if on_frame is not None and 0 <= o < footprint:
                written_now.add(o)

    def on_read(addr, size):
        off = addr - ARENA_BASE
        if 0 <= off < footprint or (0 <= off + size - 1 < footprint):
            reads_self_window[0] += 1
        if not (ARENA_BASE <= addr < ARENA_BASE + ARENA_SIZE):
            external_reads[0] += 1     # consulting an immortal scaffold = not closed
        if probe:
            for k in range(size):
                o = off + k
                if 0 <= o < DECAY_BYTES:
                    read_off.add(o)

    def on_exec(addr, size):
        off = addr - ARENA_BASE
        if 0 <= off < DECAY_BYTES:
            for k in range(size):
                if off + k < DECAY_BYTES:
                    exec_off.add(off + k)

    try:
        mu.mem_map(ARENA_BASE, ARENA_SIZE, R | W | X)
        mu.mem_map(STACK_BASE, STACK_SIZE, R | W)
        mu.mem_write(ARENA_BASE, birth)
        mu.reg_write(reg("RSP"), STACK_TOP)
        # Per-access hooks are expensive (one Python callback per memory op). Only
        # the solvent law needs write tracking (freshness); only the assay needs
        # read/exec provenance. Bit-rot survival sweeps run hookless — a ~10x
        # speedup — detecting death by fault/escape, which is how these organisms
        # actually die.
        track_writes = decay == "solvent" or probe or on_frame is not None
        if track_writes:
            mu.hook_mem_write(on_write)
        if probe:
            mu.hook_mem_read(on_read)
            mu.hook_code(on_exec)

        cycles, cause = [], ""
        rip = ARENA_BASE
        for i in range(lifetime):
            writes_window[0] = 0
            reads_self_window[0] = 0
            written_now.clear()
            # run one inter-sweep window of T instructions
            try:
                mu.emu_start(rip, ARENA_BASE + ARENA_SIZE, 0, T)  # count-bounded; no timer thread
            except UcError as e:
                cause = f"fault:{e}"
            if not cause and mu.violation:    # guest ran a trapped instruction
                cause = f"fault:forbidden_{mu.violation}"
            rip = mu.reg_read(reg("RIP"))

            # the medium's decay law acts; `decayed` records what it touched (viz)
            decayed = []
            if not cause and decay == "solvent":
                blank = bytearray(mu.mem_read(ARENA_BASE, DECAY_BYTES))
                for o in range(DECAY_BYTES):
                    if not fresh[o]:
                        if on_frame is not None and o < footprint and blank[o]:
                            decayed.append(o)
                        blank[o] = 0
                mu.mem_write(ARENA_BASE, bytes(blank))
            elif not cause and decay == "bitrot":
                n = _poisson(rng, lam)
                if n:
                    region = bytearray(mu.mem_read(ARENA_BASE, footprint))
                    for _ in range(n):
                        o = rng.randrange(footprint)
                        region[o] ^= 1 << rng.randrange(8)   # flip one random bit
                        decayed.append(o)
                    mu.mem_write(ARENA_BASE, bytes(region))
            if track_writes:
                for o in range(DECAY_BYTES):
                    fresh[o] = 0

            body = mu.mem_read(ARENA_BASE, footprint)
            integ = sum(1 for a, b in zip(body, birth) if a == b) / footprint
            rip_in = ARENA_BASE <= rip < ARENA_BASE + DECAY_BYTES

            alive = True
            if cause:
                alive = False
            elif track_writes and writes_window[0] == 0:
                alive, cause = False, "no_turnover"      # stopped metabolizing
            elif not rip_in:
                alive, cause = False, "rip_escaped"      # left its own body

            if on_frame is not None:
                on_frame({"w": i, "bytes": list(body), "integrity": integ,
                          "turnover": writes_window[0],
                          "decayed": decayed,
                          "written": sorted(o for o in written_now if o < footprint),
                          "rip": rip - ARENA_BASE, "alive": alive, "cause": cause})

            cycles.append(Cycle(i, writes_window[0], reads_self_window[0],
                                 integ, rip_in, alive, cause if not alive else ""))
            if not alive:
                return Life(organism="", T=T, footprint=footprint, lifespan=i,
                            survived=False, cause=cause, cycles=cycles,
                            exec_offsets=exec_off, read_offsets=read_off,
                            write_offsets=write_off,
                            external_reads=external_reads[0])
        return Life(organism="", T=T, footprint=footprint, lifespan=lifetime,
                    survived=True, cause="", cycles=cycles,
                    exec_offsets=exec_off, read_offsets=read_off,
                    write_offsets=write_off, external_reads=external_reads[0])
    finally:
        mu.close()


@dataclass
class Colony:
    heads: int
    footprint: int
    lifespan: int
    survived: bool
    cause: str


def live_colony(code: bytes, T: int, footprint: int, heads: list[int],
                lifetime: int = 200, lam: float = 0.0, seed: int = 0,
                on_frame=None) -> Colony:
    """REDUNDANT EXECUTION (Rung 2.5): run several heads (independent program
    counters) over one shared, decaying genome, in alternating windows. Each head
    is a full majority-repairer; a head whose own code is corrupted FAULTS, but
    instead of killing the colony it is reset to its entry and the *other* heads
    repair its copy before its next turn. The single-PC "who repairs the
    repairer" SPOF is broken: it now takes near-simultaneous corruption of
    several heads' code to end the colony. `heads` are entry offsets into the
    shared genome (e.g. [0, L] = two heads executing copies 0 and 1).

    Death = a full round in which NO head completes a window (none left to
    repair). Pure bit-rot decay; seeded for reproducible trials.
    """
    rng = random.Random(seed)
    R, W, X = CONST["UC_PROT_READ"], CONST["UC_PROT_WRITE"], CONST["UC_PROT_EXEC"]
    # Each head is an independent execution context: its own program counter AND
    # its own register file (the engine has one set, so we save/restore on every
    # switch — otherwise heads clobber each other's loop state). A head gets its
    # own slice of stack too. `regs` None means "start clean at entry".
    GP = ("RAX", "RBX", "RCX", "RDX", "RSI", "RDI", "RBP", "R8", "R9", "R10",
          "R11", "R12", "R13", "R14", "R15", "EFLAGS")
    state = [{"entry": ARENA_BASE + off, "rip": ARENA_BASE + off, "regs": None,
              "rsp": STACK_TOP - k * 0x10000}
             for k, off in enumerate(heads)]

    def restore(h):
        if h["regs"] is None:                              # clean start at entry
            for name in GP:
                mu.reg_write(reg(name), 0)
        else:
            for name, val in h["regs"].items():
                mu.reg_write(reg(name), val)
        mu.reg_write(reg("RSP"), h["rsp"])

    def save(h):
        h["regs"] = {name: mu.reg_read(reg(name)) for name in GP}
        h["rsp"] = mu.reg_read(reg("RSP"))

    mu = Uc()
    try:
        mu.mem_map(ARENA_BASE, ARENA_SIZE, R | W | X)
        mu.mem_map(STACK_BASE, STACK_SIZE, R | W)
        mu.mem_write(ARENA_BASE, code)

        for i in range(lifetime):
            ran_ok = False
            for h in state:
                restore(h)
                try:
                    mu.emu_start(h["rip"], ARENA_BASE + ARENA_SIZE, 0, T)  # count-bounded
                    if mu.violation:
                        h["rip"], h["regs"] = h["entry"], None   # resurrect clean
                    else:
                        h["rip"] = mu.reg_read(reg("RIP"))
                        save(h)
                        ran_ok = True                       # a head repaired this window
                except UcError:
                    h["rip"], h["regs"] = h["entry"], None   # faulted -> resurrect
                # bit-rot acts once per window (per head turn)
                n = _poisson(rng, lam)
                if n:
                    region = bytearray(mu.mem_read(ARENA_BASE, footprint))
                    for _ in range(n):
                        o = rng.randrange(footprint)
                        region[o] ^= 1 << rng.randrange(8)
                    mu.mem_write(ARENA_BASE, bytes(region))
            if on_frame is not None:
                body = mu.mem_read(ARENA_BASE, footprint)
                integ = sum(1 for a, b in zip(body, code) if a == b) / footprint
                on_frame({"w": i, "bytes": list(body), "integrity": integ,
                          "rips": [h["rip"] - ARENA_BASE if h["regs"] is not None
                                   else h["entry"] - ARENA_BASE for h in state],
                          "alive": ran_ok, "cause": "" if ran_ok else "all_heads_down"})
            if not ran_ok:
                return Colony(len(heads), footprint, i, False, "all_heads_down")
        return Colony(len(heads), footprint, lifetime, True, "")
    finally:
        mu.close()


WORLD_N = 64           # size of the 1-D foraging world
POS_OFF = 64           # body offset where the organism stores its position byte
SENSE_OFF = 72         # body offset where the medium writes the 3-cell gradient


@dataclass
class Forage:
    survived: bool
    lifespan: int
    cause: str
    mean_fuel: float
    track_error: float       # mean |pos - food|; small = good chemotaxis
    harvests: int


def _signal(p: int, food: int) -> int:
    """Chemical gradient: stronger (up to 255) the closer position p is to food."""
    return max(0, WORLD_N - abs(p - food))


def live_forage(code: bytes, T: int, lifetime: int = 300, *, food_speed: float = 1.0,
                turn: float = 0.12, seed: int = 0, fuel0: int = 800, cost: int = 10,
                reward: int = 25, harvest_radius: int = 1, on_frame=None) -> Forage:
    """STRUCTURAL COUPLING / FORAGING (Rung 2.7). The organism lives only by
    keeping its fuel above zero: every window costs `cost` fuel, and it regains
    `reward` only when its position sits within `harvest_radius` of a nutrient
    that drifts `food_speed` steps/window. The medium writes a local chemical
    gradient (signal at pos-1, pos, pos+1) into the organism's sensor cells; the
    organism must read it and steer toward food. Behavior must track the world —
    Maturana & Varela's chemotaxing bacterium, in machine code. Death = fuel <= 0
    (starvation) or fault. Foraging is characterized here ALONE (no decay);
    Rung 3 layers it onto self-production.
    """
    rng = random.Random(seed)
    R, W, X = CONST["UC_PROT_READ"], CONST["UC_PROT_WRITE"], CONST["UC_PROT_EXEC"]
    HALT = config.HALT_ADDR
    mu = Uc()
    try:
        mu.mem_map(ARENA_BASE, ARENA_SIZE, R | W | X)
        mu.mem_map(STACK_BASE, STACK_SIZE, R | W)
        mu.mem_map(HALT & ~0xFFF, 0x1000, R | X)
        mu.mem_write(ARENA_BASE, code)

        pos = food = WORLD_N // 2
        direction = 1 if seed % 2 == 0 else -1     # initial nutrient heading
        fuel, harvests = fuel0, 0
        mu.mem_write(ARENA_BASE + POS_OFF, bytes([pos]))
        for d in (-1, 0, 1):                       # prime the sensors
            mu.mem_write(ARENA_BASE + SENSE_OFF + d + 1, bytes([_signal(pos + d, food)]))

        errs = []
        for i in range(lifetime):
            # invoke the organism for ONE forage action (sense -> move -> ret)
            mu.reg_write(reg("RSP"), STACK_TOP)
            mu.mem_write(STACK_TOP, HALT.to_bytes(8, "little"))
            try:
                mu.emu_start(ARENA_BASE, HALT, 0, T)
            except UcError as e:
                return Forage(False, i, f"fault:{e}", _mean(errs), _mean(errs), harvests)
            if mu.violation:
                return Forage(False, i, f"fault:forbidden_{mu.violation}",
                              _mean(errs), _mean(errs), harvests)
            if mu.reg_read(reg("RIP")) != HALT:    # ran away instead of returning
                return Forage(False, i, "no_return", _mean(errs), _mean(errs), harvests)

            pos = mu.mem_read(ARENA_BASE + POS_OFF, 1)[0] % WORLD_N
            # nutrient drifts BALLISTICALLY (constant velocity, bounce at walls):
            # the organism steps 1/window, so food_speed > 1 genuinely outruns it.
            if rng.random() < turn:                # occasional reversal: a pure
                direction = -direction             # ballistic sweep can't re-acquire,
            steps = int(food_speed) + (1 if rng.random() < (food_speed % 1) else 0)
            for _ in range(steps):                 # but a gradient-sensor can
                food += direction
                if food < 0:
                    food, direction = 0, -direction
                elif food >= WORLD_N:
                    food, direction = WORLD_N - 1, -direction
            errs.append(abs(pos - food))
            harvested = abs(pos - food) <= harvest_radius
            if harvested:
                fuel += reward
                harvests += 1
            fuel -= cost
            sensors = [_signal(pos + d, food) for d in (-1, 0, 1)]
            for d in (-1, 0, 1):                   # update what the organism can sense
                mu.mem_write(ARENA_BASE + SENSE_OFF + d + 1, bytes([sensors[d + 1]]))
            dead = fuel <= 0
            if on_frame is not None:
                on_frame({"w": i, "pos": pos, "food": food, "sensors": sensors,
                          "fuel": fuel, "harvest": harvested,
                          "track_error": abs(pos - food), "harvests": harvests,
                          "alive": not dead, "cause": "starved" if dead else ""})
            if dead:
                return Forage(False, i, "starved", _mean(errs), _mean(errs), harvests)
        return Forage(True, lifetime, "", fuel0, _mean(errs), harvests)
    finally:
        mu.close()


def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0
