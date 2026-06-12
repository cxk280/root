# Results — Phase 2, Rung 2: stochastic bit-rot

Medium: `decay="bitrot"` in `medium/world.py` — after each window, flip a
Poisson(λ) number of random bits within the organism's footprint, no sweep,
seeded per trial. Reproduce: `scripts/life.py` (bitrot section) / the sweeps below.

## Carrying protocell0 forward — the predicted death

`protocell0` (Rung 1's survivor) was dropped into bit-rot **unchanged**. It
survives the solvent control but dies under bit-rot at every λ tested:

| λ (mean flips/window) | protocell0 survival (200 cycles) |
|---|---|
| 0.05 | 0/8 |
| 0.10 | 0/8 |
| 0.20 | 0/8 |
| 0.40 | 0/8 |

Its identity-copy refresh **propagates** corruption rather than correcting it:
a flip is copied back verbatim, accumulates, and eventually lands on a critical
byte → fault. This is the cliff the ladder predicted ("death is the data") — and
it locates exactly what the next organism must grow: **error correction**.

## protocell1 — error correction by triple modular redundancy

`protocell1` keeps **three byte-identical copies** of its 160-byte body (built by
`replicate: 3`) and, each cycle, repairs by **bitwise majority** across them,
`m = (a&b)|(a&c)|(b&c)`, written back to all three. Any single-copy bit flip is
outvoted and healed.

Head-to-head survival (12 seeds, 150 cycles):

| λ | protocell0 | protocell1 |
|---|---|---|
| 0.01 | 5/12 | **11/12** |
| 0.02 | 2/12 | **9/12** |
| 0.04 | 0/12 | **6/12** |
| 0.08 | 0/12 | 1/12 |
| 0.15 | 0/12 | 0/12 |

**TMR raises the error-catastrophe threshold λ\* (50% survival) from ≈ 0.008 to
≈ 0.04 — roughly 4–5×.** Error correction demonstrably works: the redundant
organism tolerates a corruption rate that reliably kills the non-redundant one.

## The residual cap — "who repairs the repairer"

The gain is bounded, and the bound is the interesting finding. In a von Neumann
substrate (code is data, a single program counter) the **executing copy is a
single point of failure**: the repair loop's own machine code lives in copy 0 and
must run to repair anything, so a flip into that hot code path faults *before* it
can heal itself. Redundancy protects the data and the two non-executing copies,
but not the ~100-byte code path currently being executed. λ\* is therefore set by
the cross-section of that hot path, not by the vote — which is why it improves
several-fold but not unboundedly.

This is a genuine result about the difficulty of autopoietic self-repair when the
metabolism is made of the same corruptible stuff it repairs — the computational
echo of why cells maintain *many* ribosomes rather than one.

## Status and next step

Rung 2 demonstrates the predicted death and that error correction raises λ\*. The
SPOF cap is the open problem; the natural next organisms in the lineage are:

- **execution rotation** — run the repair from a different copy each cycle so no
  single code path is always exposed; the copy you migrate *to* was just
  majority-verified; or
- **a minimal primer** — a tiny bootstrap (≪ body) that restores the main code
  from the majority before jumping into it, shrinking the SPOF cross-section.

Both keep the organism fully self-producing and closed; both are deferred behind
the safety-hardening pass requested before further autonomous iteration.
