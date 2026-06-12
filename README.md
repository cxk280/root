# Living Software

An attempt to build software that is **alive** in a precise, non-metaphorical
sense — machine code that continuously produces the very components that
constitute it, maintains its own boundary, and persists only by remaking itself
against decay. The standard is Maturana & Varela's *autopoiesis*, and we hold
ourselves to it literally (`AUTOPOIESIS.md`), not as a vibe.

## ELI5

Almost every program ever written is like a **statue**: you carve it once and it
just sits there. Turn the computer off and on, it's the same statue. It never has
to *do* anything to keep existing.

We're trying to make software that's more like a **tiny living cell**. A real
cell is never finished — it's constantly rebuilding its own parts, because if it
ever stopped, it would fall apart. Being alive isn't a thing you *are*, it's a
thing you *keep doing*.

So we built a tiny sealed "world" inside the computer where that's literally
true. In this world, anything a program doesn't keep actively rewriting **dissolves
away** — like writing in sand while the tide keeps washing over it. A normal
program dropped in here dies in an instant: it just sits there, the tide erases
it, gone. But we wrote a tiny organism whose whole job is to **redraw its own body,
over and over, faster than the tide can erase it.** As long as it keeps up, it
lives. If the tide comes too fast, it dies — and there's an exact speed where it
flips from alive to dead, which is basically its heartbeat.

It even has a "skin" (a boundary it draws around itself). It checks its own skin
every moment; if the tide eats through it, the organism *notices* and lets go,
dissolving on purpose instead of just glitching out. That self-checking skin is
part of what makes it count as genuinely alive rather than just a clever loop —
and we built a strict test (based on biologists' actual definition of life) that
tells the real thing apart from the fake. A blind "just redraw everything" program
survives the tide too, but our test correctly says it's *not* really alive,
because it has no skin and never checks itself.

One more piece: before any of that, we checked a stepping-stone question. Our
organisms are written in **assembly** — the rawest, most bare-metal computer
language, the stuff normal programmers avoid because it's so tedious. Could an AI
actually write good assembly, or only normal "high-level" code? We tested it
head-to-head against a top compiler. The AI's hand-written assembly was **correct
every time and often faster and smaller** than the compiler's output. That matters
because if the AI couldn't write competent raw machine code, it could never write
the self-rebuilding "metabolism" the living organisms need. It can.

**Why bother?** Because if software can be genuinely self-producing, it stops being
a statue we have to maintain and starts being something that maintains *itself* —
and that opens a very different way of making and growing programs. This repo is
the first few rungs of that ladder, built carefully and tested honestly.

## Status

- ✅ **Milestone 1 — the world + the synthesis test.** A sandboxed
  machine-code execution rig and a head-to-head benchmark: AI-written x86-64
  assembly vs. the same AI's C compiled at `clang -O3`, over 10 kernels.
  *Result:* one-shot assembly was **10/10 correct**, beat `-O3` on speed 6/10 and
  on size 8/10. Two of five pre-registered predictions falsified — in the
  *pro-assembly* direction. (`HYPOTHESES.md`, `results/RESULTS.md`.)
- ✅ **Phase 2, Rung 1 — the first living organism.** A *solvent* medium that
  dissolves any byte not rewritten within *T* ticks, and `protocell0`, the
  smallest organism that demonstrably lives in it. *Result:* an aliveness assay
  (Maturana & Varela's six-point key, applied by intervention) scores it **6/6**,
  ranks a degenerate look-alike at 2/6 and an inert control at 1/6, and measures a
  sharp metabolic phase transition at **T\* = 500**. (`results/protocell/RESULTS.md`.)
- ✅ **Phase 2, Rung 2 — error correction.** A *bit-rot* medium (seeded random
  bit flips at rate λ). Carried forward unchanged, `protocell0` dies at every λ —
  its identity copy propagates corruption. `protocell1` grows **triple modular
  redundancy** (three copies, per-byte bitwise-majority repair) and raises the
  error-catastrophe threshold λ\* **~4–5×**, capped by the executing copy's own
  code (the "who repairs the repairer" limit). (`results/protocell/RUNG2.md`.)
- ✅ **Phase 2, Rung 2.5 — lifting the cap with redundant execution.** Dilution
  (bigger redundant body) raises λ\* as the germ's share of the body falls; the
  real fix is a **colony** of several heads (independent program counters) over
  one shared genome — **2 heads survive corruption rates flatly lethal to a single
  head**, because a head whose code is corrupted is repaired by another before it
  runs. Two heads beat three: a spontaneous **division of labor** (executing heads
  + a quiescent reference copy). (`results/protocell/RUNG2B.md`.)
- ✅ **Safety hardening.** Containment is first-class: privileged instructions
  trap (C1), all organism emulation runs in an isolated resource-capped worker
  (C2), the toolchain is pinned/recorded (C5), and the whole rig runs inside a
  **no-network, read-only, capability-dropped container** (C4) verified to hold
  its walls. (`SECURITY.md`.)
- ⬜ **Next — Phase 4 on-ramp.** A colony is a minimal multicellular unity; natural
  drift over many heads sharing and repairing genomes is the next medium. (Plus
  Rung 2.5 foraging: metabolism that must capture fuel from the medium.)

## Repository layout

```
AUTOPOIESIS.md          the binding charter: what "alive" means here, what it rules
                        out, the six-point assay, and the rung-by-rung roadmap
HYPOTHESES.md           Milestone 1's pre-registered, falsifiable predictions
SECURITY.md             threat model + containment controls (C1..C6)
CLAUDE.md               project rules (incl. keeping this README current)

harness/                the sandbox + benchmark rig + containment (Milestone 1)
  abi.md                the contract every code blob follows
  uc.py                 ctypes binding to libunicorn (provenance hooks + insn traps)
  sandbox.py            one-shot execution with exact instruction accounting
  elfobj.py  assemble.py  clang -> bare-metal ELF -> flat blob pipeline
  isolation.py          run emulation in a resource-capped worker process (C2)
  containment.py        self-test: the sandbox walls hold (C1)
  runner.py  selftest.py  isolation_selftest.py
kernels/<name>/         spec + public/holdout test vectors for 10 micro-kernels
candidates/<kernel>/    AI-written C and assembly sources (built blobs are gitignored)

medium/                 the living medium (Phase 2)
  world.py              solvent + bit-rot decay; live() single + live_colony() heads
  assay.py              the six-point aliveness key, applied by intervention
  build.py  selftest.py
organisms/<name>/       organism.s + membrane.json. rock, blind, protocell0;
                        protocell1/2 = TMR error correction (byte / word vote)

scripts/                score.py (benchmark), report.py, life.py, redundancy.py
results/                RESULTS.md; protocell/RESULTS.md, RUNG2.md, RUNG2B.md
```

## Quick start

Unicorn and Capstone are used as C libraries via a small in-repo `ctypes` shim
(`harness/uc.py`) — the PyPI bindings are not required.

```sh
python3 -m venv .venv
brew install unicorn capstone          # the C libraries the shim binds

# Milestone 1 — the synthesis benchmark
.venv/bin/python -m harness.selftest   # 9 rig self-tests (incl. self-modifying code)
.venv/bin/python kernels/genvectors.py # (re)generate test vectors from oracles
.venv/bin/python scripts/score.py --all && .venv/bin/python scripts/report.py

# Phase 2 — the living organisms
.venv/bin/python -m medium.selftest    # 16 medium self-tests (the aliveness assay)
.venv/bin/python scripts/life.py       # run the assay; writes results/protocell/

# Safety / containment
.venv/bin/python -m harness.containment        # the sandbox walls hold (C1)
.venv/bin/python -m harness.isolation_selftest # the worker contains failures (C2)
```

## Safety & containment

Containment is first-class — see `SECURITY.md` for the full threat model. The
principle is **contain the box, don't shrink the organism**: the organism keeps
total freedom *inside* the sandbox (full x86, self-modification, real decay), and
we make the walls around it unbreakable and the room empty.

- **Brain in a vat.** All organism code executes **only inside the Unicorn
  emulator — never natively** — with a tiny fixed memory map, hard fuel/time/
  lifetime caps, and no syscall path, so it has no actuators.
- **C1 — privileged instructions trap.** `syscall`/`sysenter`/`cpuid` fault by
  construction; `harness/containment.py` asserts the memory and control-flow
  walls hold.
- **C2 — isolated execution.** All organism emulation runs in a resource-capped
  worker process (`harness/isolation.py`), so even a hypothetical emulator escape
  lands somewhere that can do nothing.
- **C4 — locked-down container.** `containment/run.sh` runs the whole rig with
  `--network none`, a read-only root filesystem, `--cap-drop ALL`, non-root user,
  and memory/cpu/pid caps; `containment/selftest_all.py` verifies inside that the
  science passes *and* the walls hold. Use it for autonomous/drift phases —
  never a networked or privileged host.

```sh
containment/run.sh                     # build + run the full suite, fully locked down
```

## The larger aim

The end goal is **autopoietic software** in Maturana & Varela's strict sense:
machine code that continuously produces its own components, maintains its own
self-produced boundary, and persists as a dynamic steady state against decay —
with **no external fitness function**. `AUTOPOIESIS.md` is the binding statement
of what that means and what it explicitly rules out (self-replication, imposed
evolution, goal-seeking autonomy). Evolution is allowed to re-enter only as
*natural drift* — an emergent consequence of self-production under finite fuel,
never the engine we start.

## Roadmap

A single lineage walked up a ladder of increasingly lifelike decay, **assayed at
every rung**, carrying the same organism forward so that each death locates what
the next structure must grow:

1. ✅ **Solvent sweep** — forces continuous self-production; deterministic, so one
   run is a proof. *(protocell0, T\* = 500.)*
2. ⬜ **Stochastic bit-rot** — demands real error *correction*, not mere
   re-stamping; yields an integrity-vs-λ error-catastrophe threshold.
3. ⬜ **Starvation / foraging** — metabolism costs fuel that must be captured from
   the world; introduces outward *behavior* and structural coupling.
4. ⬜ **Layered** — all pressures under one fuel budget the organism must allocate.

Then Phase 3 (structural coupling at large, self-specializing metabolism) and
Phase 4 (natural drift among many unities → lineages without selection). See
`AUTOPOIESIS.md` for the full charter.
