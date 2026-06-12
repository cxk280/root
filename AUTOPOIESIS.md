# Autopoiesis — the organizing commitment

This project is an attempt to build **autopoietic software** in the strict sense
of Humberto Maturana and Francisco Varela, not a loose metaphor. This document
fixes what that means, what it rules out, and how we will tell — operationally,
in the same falsifiable spirit as `HYPOTHESES.md` — whether we have actually
done it.

## The definition we are bound by

> *An autopoietic machine is a machine organized (defined as a unity) as a
> network of processes of production (transformation and destruction) of
> components that produces the components which: (i) through their interactions
> and transformations continuously regenerate and realize the network of
> processes (relations) that produced them; and (ii) constitute it (the machine)
> as a concrete unity in the space in which they exist by specifying the
> topological domain of its realization as such a network.*
> — Maturana & Varela, *Autopoiesis and Cognition* (1980), p. 78

Three load-bearing consequences:

- **Organizational closure, thermodynamic openness.** The network of productions
  is *operationally closed* — its product is itself — while remaining open to a
  flow of matter/energy it must metabolize. A flame is open and self-sustaining
  but produces no boundary; a crystal has a boundary but produces nothing; a
  cell does both. We are aiming for the cell.
- **Organization vs. structure.** *Organization* is the set of relations that
  make the unity the kind of thing it is; *structure* is the actual components
  realizing it right now. Autopoiesis is **organizational invariance under
  structural plasticity**: the components turn over constantly, the identity does
  not. A program that merely persists in memory is the opposite of this.
- **The boundary is produced from within.** The membrane is not a wall we draw
  around the system; it is synthesized and repaired by the very productions it
  encloses, and it in turn conditions where those productions can occur. That
  loop — components produce boundary, boundary localizes the production of
  components — is the heart of the thing.

## What autopoiesis is NOT (and what we therefore will not build)

- **Not self-replication.** Langton's loops, quines, von Neumann replicators copy
  a pattern. Copying is not self-production; a unity can be autopoietic and never
  reproduce (a single non-dividing cell still lives).
- **Not evolution, and not an imposed fitness function.** This is the correction
  that reorganized the project. Darwinian evolution needs an *external* selector
  and reproduction-with-variation. For M&V, reproduction and evolution are
  **secondary** phenomena that presuppose an autopoietic unity already exists.
  A population + mutation + fitness loop is **allopoietic** — it produces
  *something other than itself* (a sorted list, a high score), like a factory
  produces cars. We refuse to lead with it.
- **Not goal-seeking autonomy.** The unity has no objective beyond continued
  self-production. "Survival" is not a reward signal we maximize; it is the
  tautological consequence of the organization persisting or not.
- **Not a simulation that depicts a membrane.** We want the closure to be
  *literal in the computational medium*: the bytes really do produce the bytes
  that produce them. See "The honesty problem" below.

## Translating the chemistry into machine code

The precedent is the **SCL model** (Substrate–Catalyst–Link) of Varela,
Maturana & Uribe, *BioSystems* 5 (1974) — the first computational autopoiesis,
later debugged and reconstructed by Barry McMullin ("Thirty Years of
Computational Autopoiesis", *Artificial Life* 10(3), 2004). SCL runs in an
abstract artificial chemistry on a lattice. **Our wager is to use real machine
code as the chemistry**: the molecules are x86-64 bytes, the reactions are
executions that read and write those bytes, and the medium is the Unicorn
address space with an instruction-budget economy standing in for free energy.

| Autopoietic concept | Realization in the rig |
|---|---|
| Medium / world | the sandbox address space + a **fuel economy** (instruction budget = the gradient the organism feeds on) — `harness/sandbox.py`, `abi.md` |
| Components ("molecules") | bytes, read dually as instructions and as data |
| Productions ("reactions") | an executed step that **writes bytes into the self-region** — code that writes code/data |
| Boundary ("membrane") | a self-maintained, self-produced demarcation of the live region (marker/guard invariant) that the organism repairs |
| Decay ("the second law") | the world continuously perturbs components — a background corruption rate λ and/or a solvent sweep reclaiming bytes not recently refreshed |
| Metabolism | repairing components and membrane **costs fuel**; fuel must be captured from "nutrient" regions of the medium; exhaustion = death |
| Structural coupling | the organism changes structure to compensate perturbations while preserving organization (*Tree of Knowledge*, 1987) |

The crux that separates this from any ordinary program: the **steady state is
dynamic self-production, not storage**. Stop the productions and the components
decay and the unity dissolves. Staying "alive" is continuously re-synthesizing
yourself faster than the world erases you. The RWX code region and exact
per-instruction fuel accounting already built in Milestone 1 are precisely the
substrate this requires — nothing there is wasted; it was the world all along.

## The aliveness assay (falsifiable, like the rest of the rig)

Maturana & Varela give a **six-point key** for deciding whether a unity is
autopoietic. We implement each as a predicate evaluated against a live execution
trace (write-provenance comes free from the Unicorn code/mem hooks), so the
claim "this is autopoietic" is a measurement, not an assertion:

1. **Identifiable boundary?** — at every step there is a connected self-region
   with a maintained membrane, distinguishable from the medium.
2. **Constitutive components?** — ablating membrane/synthase bytes changes the
   unity's identity or halts production (the parts are load-bearing).
3. **Mechanistic?** — satisfied by construction (deterministic emulator).
4. **Boundary self-produced?** — the membrane bytes were written by the
   organism's *own* executions (verified by write provenance), not placed by us.
5. **Boundary conditions the dynamics?** — productions occur scoped by the
   membrane, and medium perturbations are resisted at it.
6. **All components self-produced — closure?** — the "synthase" that writes
   components is itself maintained by productions; cut it and the whole network
   collapses, with nothing external sustaining it.

All six affirmative ⇒ autopoietic. To these we add one quantitative homeostasis
test, the real prize: under decay rate λ the organism holds component integrity
in a **dynamic steady state** (turnover > 0, integrity ≈ constant) and **dies
when λ exceeds its metabolic rate** — a measurable phase transition we can chart.
A thing that shows that transition is alive in a way a stored program can never
be.

## The honesty problem (stated up front)

Maturana was himself skeptical that a simulation is autopoietic rather than a
*simulation of* autopoiesis — is a depicted membrane a membrane? Our defensible
position, and the only claim we will make: in the **medium of computation** the
closure is **literal, not depicted** — the bytes genuinely produce the bytes that
produce them; the membrane genuinely constrains genuine writes. This is
autopoiesis *in the computational medium*, not a picture of chemical autopoiesis.
We will not overclaim past that line, and `RESULTS.md`-style write-ups must keep
to it. (cf. McMullin & Varela 1997; Beer's operational analyses of autopoiesis
and cognition in the Game of Life, 2004/2014, for how to make these predicates
honest.)

## Where evolution re-enters — through the back door, not the front

We do not forbid evolution; we refuse to *impose* it. Once self-producing unities
exist in a medium with finite fuel, those organizations that happen to maintain
themselves persist and the others dissolve — **natural drift** (Maturana &
Varela, *The Tree of Knowledge*, 1987), explicitly anti-adaptationist: no fitness
function, no objective, just differential persistence of organizations under a
shared resource. If lineages and variation emerge there, they are a *consequence*
of autopoiesis, exactly as M&V order it — not the engine we started.

## Cognition — the reason this matters beyond the demo

For M&V, **living = cognitive**: the domain of interactions a unity can undergo
while conserving its organization *is* its cognitive domain. An autopoietic
software unity, then, is the smallest honest example of software that "knows" its
world only in the enactive sense — by what it must do to keep being itself. That,
not any aesthetic of "naturalness," is the precise content of the intuition that
this software would be more in tune with the living: the kinship is
**organizational** (closure, structural coupling, natural drift), and we will
hold ourselves to that precise meaning rather than the romantic one.

## How this re-specifies the roadmap

- **Milestone 1 (complete) — the world + the synthesis capability.** The
  falsification rig is unchanged in code but reframed in purpose: the sandbox is
  the *medium*, the fuel economy is its *thermodynamics*, and the C-vs-asm
  benchmark answered the prerequisite question — *can an LLM author competent
  machine code at all?* It can (`results/RESULTS.md`: 10/10 one-shot-correct,
  competitive with `-O3`), so the gate to building a metabolism is open.

### Phase 2 — the ladder of media (each rung assayed before the next)

Phase 2 is **not** one organism; it is **one lineage walked up a ladder of
increasingly lifelike decay**, assayed at every rung. Two rules govern the climb:

1. **Carry the same organism forward — death is the data.** Each rung drops the
   *unchanged* survivor of the previous rung into the harsher medium. If it dies,
   the death *is* the measurement (it locates exactly what the new pressure
   demands), and we then let the organism grow the structure that survives —
   structural coupling made literal: structure changes so that organization is
   conserved.
2. **The stage-1 assay must enforce closure quality, not just survival.** The
   solvent sweep can be "passed" by a degenerate organism that blindly rewrites
   its whole body every tick — self-producing in the letter, brittle in spirit,
   and certain to fall off a cliff at rung 2. So rung 1's assay scores the
   six-point key (is the *boundary* doing work? is production *conditioned* on
   self-state?), not just "did it live." Detecting the degenerate strategy is a
   success of the assay, not a failure of the organism.

The rungs:

- **Rung 1 — solvent sweep (done).** A background process reclaims any byte not
  rewritten within the last *T* fuel-ticks. Forces continuous self-production with
  the least machinery; fully deterministic, so one run is a proof. **Result:**
  `protocell0` lives, 6/6 on the six-point key, sharp metabolic threshold *T\* =
  500* (`results/protocell/RESULTS.md`).
- **Rung 2 — stochastic bit-rot (done).** Random bit flips at rate λ; no sweep.
  Demands genuine **error correction**, not re-stamping. **Result:** `protocell0`
  dies as predicted; `protocell1`'s triple modular redundancy raises λ\* ~4–5×,
  capped by the "who repairs the repairer" single point of failure
  (`results/protocell/RUNG2.md`).
- **Rung 2.5 — lifting the SPOF with redundant execution (done).** The cap is a
  property of *single-threaded* self-repair. A **colony** of several heads
  (independent program counters) over one shared genome breaks it: a head whose
  code is corrupted is repaired by another before it runs. **Result:** 2 heads
  survive corruption rates lethal to a single head (~2–4× λ\*), and 2 heads beat 3
  — a spontaneous **division of labor** (executing heads + a quiescent reference
  copy). The colony is already a minimal multicellular unity
  (`results/protocell/RUNG2B.md`).
- **Rung 2.7 — starvation / foraging (next).** Orthogonal to corruption: running
  the metabolism *costs* fuel that must be **captured from the medium**, and
  exhaustion is death. Introduces *outward behavior* — the organism must act on
  its world to keep eating — the most direct route to structural coupling.
  **Assay:** does the unity forage and hold a fuel homeostasis.
- **Rung 3 — layered.** Solvent boundary-turnover + low-rate component bit-rot +
  starvation, under one fuel budget the organism must *allocate* across membrane
  upkeep, interior repair, and foraging. **Assay:** the 2-D+ viability envelope —
  interpretable only because each axis was characterized alone first.

### Phase 3 — structural coupling at large

Perturb a rung-3-viable organism's world (shifting nutrient fields, varying
λ and *T*) and ask whether it compensates structurally while conserving
organization — and whether a self-specializing metabolism does things a
compiler-frozen program cannot (the `memchr` result of Milestone 1 is the first
hint of that seam).

### Phase 4 — natural drift (now with an on-ramp)

Rung 2.5 arrived here early and from below: the **colony** (`live_colony`) is
already a minimal multicellular unity — several heads sharing and repairing one
genome, with an emergent division of labor. Phase 4 generalizes it: many heads
and many genomes, one finite fuel pool, decay; observe whether
persistence-*without*-selection yields lineages — evolution as a *consequence* of
autopoiesis, never an imposed engine. That redundant execution was *forced* by the
single-PC repair limit (not designed in) is the strongest sign yet that the
ladder's pressures, followed honestly, reproduce the logic of living organization.
Visualization at that point follows the global `VIEWS.md` + mock-approval rule.

Everything above is a commitment to a *standard*, not a promise of success: it is
entirely possible the assay never goes fully affirmative. That failure would be
informative and would be reported as plainly as a passing result.
