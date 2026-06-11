# Results — Phase 2, Rung 1: the solvent-sweep medium

Reproduced by `.venv/bin/python scripts/life.py`; invariants locked by
`.venv/bin/python -m medium.selftest`. Raw data: `results/protocell/assay.json`.

## What was built

A living medium (`medium/world.py`) in which a machine-code organism is resident
in a decaying arena and a **solvent sweep** zeroes every byte not rewritten
within the last *T* fuel-ticks. There is no external master copy — the medium
maps no immortal data region — so an organism persists only by continuously
re-laying its own bytes, the bytes that do the re-laying included. That is
organizational closure *literal in the computational medium*, the one claim
`AUTOPOIESIS.md` permits.

Three organisms, as a test of the **assay** as much as of the organisms:

| organism | what it is | expected |
|---|---|---|
| `rock` | inert spin loop, never writes itself | must die — proves decay has teeth |
| `blind` | refreshes its whole body each cycle, hardcoded extent, never consults itself | alive but **no genuine boundary** |
| `protocell0` | reads its membrane each cycle to gate life and bound production, then re-synthesizes its whole body | alive, **full closure** |

## The aliveness assay (Maturana & Varela's six-point key, by intervention)

The key is about intervention, not observation. Passive read-counting cannot
distinguish an organism consulting its boundary from one reading its body as copy
payload (the bug that first appeared here and forced the redesign). So an organism
**declares** its membrane (`organisms/<name>/membrane.json`) and the assay only
credits it if provenance + intervention confirm the membrane is (a) read during
life, (b) **never executed** (data, not code that merely faults when damaged),
(c) re-written every cycle (self-produced), and (d) such that **corrupting its
value kills** an otherwise-living organism. A false declaration fails (a)–(d).

| | rock | blind | protocell0 |
|---|:--:|:--:|:--:|
| survives (T=4000, 120 cycles) | ✗ | ✓ | ✓ |
| 1 identifiable boundary | ✗ | ✗ | ✓ |
| 2 constitutive components | ✗ | ✗ | ✓ |
| 3 mechanistic | ✓ | ✓ | ✓ |
| 4 boundary self-produced | ✗ | ✗ | ✓ |
| 5 boundary conditions dynamics | ✗ | ✗ | ✓ |
| 6 closure, no external scaffold | ✗ | ✓ | ✓ |
| **closure score** | **1/6** | **2/6** | **6/6** |
| metabolic threshold T\* | — (dead) | 500 | 500 |
| mean turnover (bytes/cycle) | 0 | 96 | 88 |
| mean integrity | 0.00 | 1.00 | 1.00 |

The assay ranks the three exactly as intended — **rock (1/6, dead) < blind
(2/6, alive but boundaryless) < protocell0 (6/6)** — and the discrimination is
earned by intervention: for `protocell0` all four membrane checks (read /
not-executed / rewritten / corruption-kills) hold; `blind` declares no membrane
and so collects only *mechanistic* and *closure-by-construction*. That `blind`
lives yet scores 2/6 is the point: surviving the solvent is not the same as being
autopoietic, and the assay says so.

## The homeostasis phase transition (the headline)

Sweeping *T* for `protocell0` (footprint 88 bytes; a full self-refresh is ~4
instructions/byte ≈ 350–500 instructions) gives a sharp threshold:

```
T = 200..450   dies (lifespan 1–4)   decay outruns metabolism
T = 500..1000  lives (lifespan 150)  steady-state self-production
```

`T* = 500`. Below it the solvent reclaims the far end of the body before the
refresh loop reaches it; the organism then executes or reads into the dissolved
region and faults. **This threshold is the organism's metabolic rate, read
directly off the medium** — the quantitative signature of a dynamic steady state
that a stored program does not have. Note the death mode just below threshold is
often the organism's *own* suicide path: as the solvent eats its membrane marker,
`protocell0` detects the lost sentinel and deliberately leaps out of its own body
(`UC_ERR_READ_UNMAPPED` at its `die` target) rather than merely crashing — the
boundary conditioning the dynamics, visible in how it dies.

## Honest limitations (and why they are the point)

- **The refresh is an identity copy** — it defeats neglect-decay but performs no
  error *correction*. This is the expected stage-1 shape, not a defect: it is
  exactly why `protocell0` is **predicted to die at Rung 2 (bit-rot)**, where a
  blind identity copy cannot repair damage it cannot detect. Carrying this same
  organism into Rung 2 and watching it die *is* the next measurement
  (`AUTOPOIESIS.md`, "death is the data").
- **Closure is literal but minimal.** `protocell0` is autopoietic in the
  computational medium by the six-point key, but it is a protocell: no
  metabolism-as-foraging yet (Rung 2.5), no structural plasticity under noise
  (Rung 2). It is the smallest thing that genuinely lives here, which is all
  Rung 1 set out to produce.
- **Determinism.** The solvent medium is fully deterministic, so each run is a
  proof, not a sample — appropriate for a first existence result. Rung 2's
  stochastic bit-rot will require seeded trials and survival statistics.

## Verdict and next rung

Rung 1 is met: the smallest organism that **demonstrably lives** under the
solvent, characterized honestly on the closure spectrum (6/6), with a measured
metabolic threshold and an assay that earns its discriminations by intervention.
**Go to Rung 2 — stochastic bit-rot — carrying `protocell0` forward unchanged**,
and let its predicted death locate exactly what error-correcting structure the
next organism in the lineage must grow.
