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
- ⬜ **Next — Rung 2 (bit-rot).** Carry `protocell0` unchanged into a medium of
  random corruption and watch it die: its identity-copy refresh can't fix damage
  it can't detect. That death locates the error-correcting structure the next
  organism must grow.

## Repository layout

```
AUTOPOIESIS.md          the binding charter: what "alive" means here, what it rules
                        out, the six-point assay, and the rung-by-rung roadmap
HYPOTHESES.md           Milestone 1's pre-registered, falsifiable predictions

harness/                the sandbox + benchmark rig (Milestone 1)
  abi.md                the contract every code blob follows
  uc.py                 ctypes binding to libunicorn (+ memory/exec provenance hooks)
  sandbox.py            one-shot execution with exact instruction accounting
  elfobj.py  assemble.py  clang -> bare-metal ELF -> flat blob pipeline
  runner.py  selftest.py
kernels/<name>/         spec + public/holdout test vectors for 10 micro-kernels
candidates/<kernel>/    AI-written C and assembly sources (built blobs are gitignored)

medium/                 the living medium (Phase 2)
  world.py              the solvent-sweep world: continuous execution + decay
  assay.py              the six-point aliveness key, applied by intervention
  build.py  selftest.py
organisms/<name>/       organism.s + membrane.json (rock, blind, protocell0)

scripts/                score.py (benchmark), report.py (table), life.py (assay)
results/                RESULTS.md + raw run JSON for both milestones
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

# Phase 2, Rung 1 — the living organism
.venv/bin/python -m medium.selftest    # 16 medium self-tests (the aliveness assay)
.venv/bin/python scripts/life.py       # run the assay; writes results/protocell/
```

## Safety invariant

All generated, self-modifying, and (later) evolved machine code executes **only
inside the Unicorn emulator — never natively on the host.** This is
non-negotiable and becomes essential once organisms rewrite themselves and drift.

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
