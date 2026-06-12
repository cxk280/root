# Results — Phase 2, Rung 2.7: foraging & structural coupling

The first rung with **outward behavior**. Rungs 1–2.5 were about an organism
maintaining *itself* against decay; here survival depends on what the organism
*does to its world*. Reproduce: `.venv/bin/python scripts/forage.py` →
`results/protocell/forage.json`; invariants in `medium/selftest.py`.

## The medium

A fuel economy (`medium/world.py::live_forage`): every window costs `cost` fuel,
and the organism regains `reward` only when its position sits on a **nutrient**
that drifts through a 1-D world. Fuel ≤ 0 is **starvation death**. The organism is
invoked once per window as an *agent function* (sense → one step → return); the
medium writes a **chemical gradient** — the signal strength at the organism's
left (pos-1), here, and right (pos+1) — into its sensor cells. To eat, the
organism must read that gradient and steer toward food.

This is deliberately **Maturana & Varela's chemotaxing bacterium** — their
canonical example of the cognitive domain of a living system — rendered in
machine code. Foraging is characterized here *alone* (no decay); Rung 3 layers it
onto self-production.

## Two organisms

- **`forager0` (chemotaxis):** compares its two flanking gradient sensors and
  steps toward the stronger — climbing to food. ~50 bytes.
- **`forager_sweep` (control):** ignores the gradient and sweeps right (wrapping).
  It passes over food periodically but never *tracks* it — the foraging analogue
  of `rock`/`blind`.

## Result — behavior must track the world

Nutrient drifts ballistically (constant velocity, occasional reversal, bounce at
walls). Survival/12 vs drift speed (steps/window); `track_error` = mean distance
the chemotactic forager keeps from the food:

| drift speed | chemotaxis | sweep | chemo track-error |
|---|:--:|:--:|:--:|
| 0.0 | 12/12 | 0/12 | 0.0 |
| 0.5 | 12/12 | 0/12 | 0.5 |
| 0.8 | 12/12 | 0/12 | 0.8 |
| 1.0 | 12/12 | 0/12 | 1.0 |
| 1.2 | 11/12 | 0/12 | 2.3 |
| 1.5 | 0/12 | 0/12 | 4.2 |
| 2.0 | 0/12 | 0/12 | 6.5 |

Two readings, both clean:

- **A foraging bandwidth v\* ≈ 1.2 steps/window.** Below it the chemotactic forager
  stays locked to the nutrient (track-error ≈ the drift speed) and never starves;
  above it the food outruns its one-step-per-window gait, track-error jumps
  (1.0 → 2.3 → 4.2), it falls behind, and it starves. This is the third member of
  the family **T\* (Rung 1) · λ\* (Rung 2) · v\* (Rung 2.7)** — each a sharp
  threshold where a vital rate exceeds the organism's capacity.
- **Sensing is what makes it foraging.** The sweep control **starves at every
  speed, including 0** — motion without sensing harvests only by accident. The
  difference between living and starving here is not movement but *coupling*:
  behavior conditioned on a signal from the world.

## Why this rung matters

For Maturana & Varela, **living is cognitive**: the domain of interactions a unity
can undergo while conserving its organization *is* its cognitive domain. `forager0`
is the smallest thing in this project that "knows" its world in that strict,
enactive sense — it has no model and no goal, only a gradient it must climb to
keep being itself. The contrast with `forager_sweep` is the contrast M&V draw
between a system that is merely *moved* and one whose conduct is *coupled* to its
medium. v\* is the quantitative edge of that coupling.

## Next

Rung 3 layers the rungs: a self-producing organism (solvent and/or bit-rot) that
must *also* forage for the fuel its metabolism spends — membrane upkeep, error
correction, and foraging competing for one budget. The viability envelope over
(T, λ, v) is interpretable precisely because each axis was characterized alone.
