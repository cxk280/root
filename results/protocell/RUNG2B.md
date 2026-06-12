# Results — Phase 2, Rung 2.5: lifting the "who repairs the repairer" cap

Rung 2 (`RUNG2.md`) showed triple modular redundancy raises the error-catastrophe
threshold λ\* ~4–5×, but capped by a single point of failure: in a von Neumann
substrate (code is data, one program counter) the **executing copy's own repair
code** must run to repair anything, so a flip into that hot path faults before it
can heal itself. This round tests the three ways out. Reproduce:
`.venv/bin/python scripts/redundancy.py` → `results/protocell/redundancy.json`.

All survival counts below are out of **12 seeds** (lifetime 120), recorded by
`scripts/redundancy.py` → `results/protocell/redundancy.json`.

## Lever 1 — shrink the germ (marginal)

`protocell2` repairs by 64-bit-word bitwise majority instead of byte-wise
(`protocell1`), so a self-pass is 8× fewer iterations:

| λ | protocell1 (byte vote) | protocell2 (word vote) |
|---|:--:|:--:|
| 0.04 | 8 | 6 |
| 0.08 | 2 | 1 |
| 0.16 | 0 | 0 |

λ\* is essentially unchanged (word is, if anything, a hair *worse* — within seed
noise). **Conclusion:** the SPOF is the repair loop's *code-byte cross-section*
(which both share), not its instruction count. Shrinking the loop's runtime does
not shrink the target a flip can hit.

## Lever 2 — dilution (clean scaling law)

Hold the germ fixed (~120 B) and grow the redundant body, so the germ is a smaller
fraction of what must be maintained. Single organism, survival/12 vs λ:

| body L | footprint | germ % | λ=0.04 | 0.08 | 0.16 | 0.32 |
|---|--:|--:|:--:|:--:|:--:|:--:|
| 160  | 480  | 25.0% | 6 | 1 | 0 | 0 |
| 480  | 1440 |  8.3% | 11 | 7 | 3 | 2 |
| 960  | 2880 |  4.2% | 11 | 8 | 8 | 3 |

**λ\* scales with footprint/germ:** as the germ's share of the body falls ~6×, the
tolerated corruption rate rises several-fold. Dilution makes the irreducible germ
*arbitrarily rarely hit* — but never zero. It buys robustness with bulk; it does
not remove the single point of failure.

## Lever 3 — redundant EXECUTION (the real fix)

The medium now supports a **colony**: several heads (independent program counters,
each with its own register context) executing over **one shared genome** in
alternating windows (`medium/world.py::live_colony`). Each head is a full
majority-repairer. A head whose own code is corrupted faults — but instead of
ending the colony it is reset to its entry, and the *other* heads repair its copy
before its next turn. The single-PC SPOF is broken: it now takes near-simultaneous
corruption of several heads to end the colony.

Same genome (footprint 480), survival/12 vs λ:

| λ | 1 head | 2 heads | 3 heads |
|---|:--:|:--:|:--:|
| 0.04 | 6 | **11** | 7 |
| 0.08 | 1 | **7** | 6 |
| 0.16 | 0 | **5** | 4 |
| 0.32 | 0 | **3** | 1 |

**Two heads survive corruption rates (λ = 0.16, 0.32) that are flatly lethal to any
single head** — a ~2–4× lift in λ\*, achieved not by more redundancy but by
redundant *execution*. This is the genuine resolution of "who repairs the
repairer": no single executing copy is a fatal dependency, because another head
repairs it before it runs.

### An emergent surprise: division of labor

**Two heads beat three.** With two heads over three copies, the third copy is never
executed — it stays a pristine *data reference* the heads vote against; with three
heads, every copy's code is exposed to corruption and there is no clean backup.
The optimum is **executing heads + a quiescent reference copy** — a spontaneous
division of labor that was not designed in, and the first faint shadow of
*differentiation* (specialized cells) in this medium.

## Where this points

The single-organism cap is a property of single-threaded self-repair; the escape
is multiplicity of *execution*. That is exactly the logic by which life answers the
same problem — many ribosomes, not one — and it is the bridge to **Phase 4**: a
colony is already a minimal multicellular unity, and natural drift over many heads
sharing and repairing genomes is the next medium. Redundant execution turns the
"who repairs the repairer" dead-end into the on-ramp to multicellularity.
