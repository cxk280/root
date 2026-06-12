# Results — Phase 2, Rung 3: the layered organism

The rungs so far isolated one pressure each: self-production against the solvent
(Rung 1, threshold T\*), error correction against bit-rot (Rung 2, λ\*), foraging
against starvation (Rung 2.7, v\*). Rung 3 puts them on **one organism, one
instruction budget**, and asks where it can live. Reproduce:
`.venv/bin/python scripts/layered.py` → `results/protocell/layered.json`;
invariants in `medium/selftest.py`.

## The hybrid organism (`protocell3`)

`protocell3` is a single continuous loop that, each pass:

1. **forages** — *if* the medium has set a `tick` flag, it takes one chemotaxis
   step toward the nutrient and clears the tick (world-triggered, event-driven
   behavior);
2. **checks its boundary** — dies if its membrane marker is gone;
3. **self-produces** — identity-refreshes its whole 256-byte body against the
   solvent (continuous, autonomous metabolism).

This is the **hybrid execution model** chosen for Rung 3: continuous autonomous
self-maintenance, plus discrete behavior the *world* triggers — which is how real
organisms work (metabolism runs nonstop; a bacterium tumbles when a receptor
*changes*). The forage is checked first so the organism keeps eating even when its
budget is tight.

## Fuel gates repair — the coupling that makes it one unity

The medium (`medium/world.py::live_layered`) ties the two pressures together: the
per-window instruction budget **shrinks with fuel** (below `starve_thresh`,
`T_eff = T · fuel/starve_thresh`). So **starvation impairs self-production** — a
hungry organism literally has less budget to re-lay its body, and the solvent eats
the parts it could not refresh (its membrane first). The three pressures are not
three bolted-together systems; they are one metabolism spending one budget.

## The viability envelope

Outcome over the self-production budget *T* (rows) and the nutrient drift speed
*v* (columns), 4 seeds per cell:

| | v=0.3 | v=0.6 | v=1.0 | v=1.4 | v=1.8 |
|---|:--:|:--:|:--:|:--:|:--:|
| **T=700** | dissolved | dissolved | dissolved | dissolved | dissolved |
| **T=1000** | dissolved | dissolved | dissolved | dissolved | dissolved |
| **T=2000** | **live** | **live** | **live** | starved | starved |
| **T=4000** | **live** | **live** | **live** | starved | starved |

A 2-D **viability envelope**, bounded on two sides by two different deaths:

- **Below** (small *T*): **dissolution** — the budget cannot self-produce the body
  at all, regardless of food. This is Rung 1's T\* floor, re-appearing inside the
  layered medium (here ≈ between 1000 and 2000 for the 256-byte body).
- **On the right** (fast *v*): **starvation** — the nutrient outruns the
  forager's one-step gait, fuel falls, the budget shrinks, and the impaired repair
  loses the membrane. This is Rung 2.7's v\* bandwidth (here ≈ between 1.0 and
  1.4), now expressed as a *dissolution* the organism dies of for lack of fuel.

The organism lives only in the interior — where it can afford **both** to maintain
itself and to keep eating. The envelope is interpretable precisely because each
edge was characterized alone first.

## What this completes, and what's next

Rung 3 is the autopoietic + cognitive unity in miniature: a self-producing
boundary-maintaining organism whose continued existence depends on *acting on its
world* (foraging) — Maturana & Varela's claim that **living is cognitive**, made
mechanical. The single most striking thing is that the same threshold structure
(T\* · λ\* · v\*) survives composition: the layered organism dies at the *same
edges*, now coupled through one budget.

Next is **Phase 4 — natural drift**: many such unities sharing and repairing
genomes under one finite fuel pool, where differential persistence (not an imposed
fitness function) is the only selection. The colony of Rung 2.5 is already the
seed of it.
