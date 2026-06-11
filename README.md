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

## Roadmap

Milestone 1 (this repo state) → Phase 2: evolutionary loop over blobs →
Phase 3: compiler-precluded behaviors (self-specializing code) → Phase 4:
long-running "living software" organism. See the project plan.
