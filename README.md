# Living Software — Milestone 1: The Falsification Rig

Tests a load-bearing claim of the "living software" hypothesis: **can an LLM
write raw x86-64 machine code that is correct and competitive with the same
LLM writing C compiled at `clang -O3`?**

- `HYPOTHESES.md` — pre-registered predictions (written before any runs).
- `harness/abi.md` — the contract every candidate blob follows.
- `harness/` — Unicorn-based sandbox, ELF `.text` extraction, runner CLI,
  pluggable candidate-generator interface.
- `kernels/<name>/` — spec + public + holdout test vectors for 10 micro-kernels.
- `candidates/<kernel>/<condition>/` — generated C/asm sources and built blobs.
- `results/` — raw per-run metrics (`runs/*.json`) and the analysis (`RESULTS.md`).

## Quick start

```sh
python3 -m venv .venv && .venv/bin/pip install unicorn capstone
.venv/bin/python -m harness.selftest                  # harness self-tests
.venv/bin/python kernels/genvectors.py                # (re)generate test vectors
.venv/bin/python -m harness.runner --kernel popcount \
    --candidate candidates/popcount/c_O3/blob.bin --tests holdout
```

**Safety invariant:** generated/evolved machine code executes only inside the
Unicorn emulator — never natively on the host. This is non-negotiable and
becomes mandatory in later phases (self-modifying, evolved code).

## The larger aim: autopoietic software

The end goal is **autopoietic software** in the strict sense of Maturana &
Varela — machine code that continuously produces the very components that
constitute it, maintains its own boundary, and persists as a dynamic steady
state against decay, with no external fitness function. `AUTOPOIESIS.md` is the
binding statement of what that means, what it rules out (self-replication,
imposed evolution, goal-seeking), and the falsifiable six-point aliveness assay
we will hold ourselves to. This milestone's sandbox + fuel economy is precisely
the *medium* such an organism would live in.

## Roadmap

Milestone 1 (this repo state: the world + proof an LLM can synthesize machine
code) → Phase 2: the **protocell** — smallest unity passing the autopoiesis
assay and showing the homeostasis phase transition → Phase 3: structural
coupling / self-specializing metabolism → Phase 4: **natural drift** among many
unities under finite fuel (evolution as a *consequence*, not an engine). See
`AUTOPOIESIS.md` and the project plan.
