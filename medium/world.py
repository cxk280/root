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
         decay: str = "solvent", lam: float = 0.0, seed: int = 0) -> Life:
    """Run one organism for up to `lifetime` windows under decay law `decay`.

    `code` is the birth image placed at ARENA_BASE; `body_hint` is its nominal
    footprint for integrity accounting (defaults to len(code)). With probe=True,
    accumulate execution/read/write provenance (offset sets) for the assay.
    For decay="bitrot", `lam` is the mean bit flips per window and `seed` makes
    the corruption stream reproducible."""
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

    def on_write(addr, size, _value):
        off = addr - ARENA_BASE
        for k in range(size):
            o = off + k
            if 0 <= o < DECAY_BYTES and not fresh[o]:
                fresh[o] = 1
                writes_window[0] += 1
            if probe and 0 <= o < DECAY_BYTES:
                write_off.add(o)

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
        mu.hook_mem_write(on_write)
        mu.hook_mem_read(on_read)
        if probe:
            mu.hook_code(on_exec)

        cycles, cause = [], ""
        rip = ARENA_BASE
        for i in range(lifetime):
            writes_window[0] = 0
            reads_self_window[0] = 0
            # run one inter-sweep window of T instructions
            try:
                mu.emu_start(rip, ARENA_BASE + ARENA_SIZE, 5_000_000, T)
            except UcError as e:
                cause = f"fault:{e}"
            rip = mu.reg_read(reg("RIP"))

            # the medium's decay law acts
            if not cause and decay == "solvent":
                blank = bytearray(mu.mem_read(ARENA_BASE, DECAY_BYTES))
                for o in range(DECAY_BYTES):
                    if not fresh[o]:
                        blank[o] = 0
                mu.mem_write(ARENA_BASE, bytes(blank))
            elif not cause and decay == "bitrot":
                n = _poisson(rng, lam)
                if n:
                    region = bytearray(mu.mem_read(ARENA_BASE, footprint))
                    for _ in range(n):
                        o = rng.randrange(footprint)
                        region[o] ^= 1 << rng.randrange(8)   # flip one random bit
                    mu.mem_write(ARENA_BASE, bytes(region))
            for o in range(DECAY_BYTES):
                fresh[o] = 0

            body = mu.mem_read(ARENA_BASE, footprint)
            integ = sum(1 for a, b in zip(body, birth) if a == b) / footprint
            rip_in = ARENA_BASE <= rip < ARENA_BASE + DECAY_BYTES

            alive = True
            if cause:
                alive = False
            elif writes_window[0] == 0:
                alive, cause = False, "no_turnover"      # stopped metabolizing
            elif not rip_in:
                alive, cause = False, "rip_escaped"      # left its own body

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
