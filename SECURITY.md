# Security & containment model

This project grows **self-modifying machine code** and will later let it
**replicate and drift** under selection-like pressure. That is the whole point —
and it is also why containment is a first-class concern. This document states the
threat model, the guarantees we rely on, the residual risks, and the controls.

## Guiding principle: contain the box, don't shrink the organism

The user directive is *maximum safety without sacrificing realism or
functionality*. We honor it by **containment, not capability-restriction**:

- We do **not** restrict the instruction set, forbid self-modification, simplify
  the decay laws, or cap how clever an organism may be. Freedom *inside* the
  sandbox is total — that freedom is the realism.
- We **do** make the sandbox walls unbreakable and the room around it empty:
  every layer outside the organism is locked down, audited, and bounded.

The organism is a brain in a vat with full freedom of thought and **no
actuators**. We harden the vat and empty the room; we never lobotomize the brain.

## The containment model ("brain in a vat")

All organism code executes **only inside the Unicorn CPU emulator — never
natively on the host.** Consequences, by construction:

- **No host instruction execution.** Unicorn interprets/JITs guest instructions
  into a controlled context; guest bytes are never branched to by the host CPU.
- **A tiny, fixed memory map.** Arena (64 KiB), stack, and a few control pages —
  nothing else is mapped. The guest **cannot map new memory** (it has no syscall
  path), so it cannot grow beyond its vat.
- **No actuators.** The guest has no file, network, process, clock-set, or device
  access, because it has no working syscall/OS path (see the empirical probe
  below). Its *only* channel to the outside is the bytes the harness chooses to
  read from guest memory.
- **Bounded.** Every run is capped by fuel (instruction count), a wall-clock
  timeout, and a lifetime cap. Infinite loops and runaways halt.
- **Deterministic & auditable.** The solvent medium is fully deterministic; the
  bit-rot medium is seeded. Every run reproduces exactly, so behavior is
  auditable rather than mysterious.

This is the same basis on which digital-evolution systems (Tierra, Avida) have
run self-replicating, evolving code safely for decades: a restricted virtual
machine with no host actuators. The novelty here (real x86 in Unicorn vs. a toy
ISA) raises emulator-bug exposure, addressed below.

## Empirical containment probe (run, not assumed)

Probing the guest sandbox (`harness/sandbox.py`) directly:

| guest attempt | result |
|---|---|
| `int 0x80` | **faults** (UC_ERR_EXCEPTION) |
| write to a host-range address | **faults** (UC_ERR_WRITE_UNMAPPED) |
| jump to an unmapped/host address | **faults** (UC_ERR_FETCH_UNMAPPED) |
| `syscall` | **executes as a no-op** — does *not* reach the host kernel |
| `rdtsc` | executes (emulated counter; no host access) |

The faults confirm the memory and control-flow walls hold. The `syscall` finding
(originally an emulated no-op) is now **closed by C1**: `syscall`/`sysenter`/
`cpuid` are trapped to a fault by default in the Unicorn shim, and
`harness/containment.py` asserts it (11/11 checks). "No privileged/OS instruction
reaches anything, and the run is deterministic" is now *tested*, not assumed.

## Residual risks and controls

| # | Risk | Control | Status |
|---|---|---|---|
| R1 | **Emulator implementation bug** (Unicorn ← QEMU TCG lineage) lets crafted guest code corrupt/execute in the *host process*. | Emulation runs in an **isolated worker process** (`harness/isolation.py`): bounded CPU time + wall-clock, no core dumps, bounded address space (Linux), few fds; a worker that dies/hangs/escapes is contained, not propagated. Network/FS hard-walling comes from the container (C4). | **done (C2)** — `isolation_selftest` |
| R2 | Escaped code inherits the **host user's privileges**. | The container (C4) runs non-root, `--cap-drop ALL`, `--security-opt no-new-privileges`, read-only root FS — the room is empty. | **done (C4)** |
| R3 | **Resource exhaustion / runaway** across many runs or large populations. | Hard caps in force: fuel + wall-clock + lifetime per run; worker CPU/mem/fsize rlimits; container `--memory`/`--cpus`/`--pids-limit`. Population-size budget added at the population phase. | **enforced** |
| R4 | **Unattended autonomous evolution** (Phase 4 natural drift) does something unexpected over long horizons. | `containment/run.sh` runs the rig in a **no-network** (`--network none`), read-only, capability-dropped container with memory/cpu/pid caps; verified by `containment/selftest_all.py`. Human-in-the-loop on every merge (project rule). | **available (C4)** |
| R5 | **Supply chain** (Unicorn/Capstone/toolchain). | `results/provenance.json` records Unicorn version + lib hash and the clang version; the in-repo `ctypes` shim avoids a PyPI binary for Unicorn (binds the system lib). | **done (C5)** |
| R6 | **Nondeterminism leak** (e.g. `rdtsc`) undermines auditability. | `cpuid` trapped (C1); bit-rot seeded and the seed recorded; `rdtsc` documented (emulated counter, off every result path). | partial (C6) |
| R7 | **Visualization surface** — the live visualizer runs the emulator in a long-lived server process (not the C2 isolated worker) so it can stream frames. | The C1 instruction traps stay active; the server binds `127.0.0.1` only and serves a fixed static dir + a closed control API (no arbitrary code from the browser). Safe for the curated demo organisms; for untrusted/evolved organisms run it inside the C4 container (`containment/run.sh python3 -m viz.server`). | **C7** — `viz/README.md` |

## Invariants (test-enforced)

Enforced today by `harness/containment.py` (C1) and `harness/isolation_selftest.py` (C2):

1. Guest memory writes/reads/fetches outside the mapped arena **fault**. ✅
2. Guest cannot map memory or invoke any OS facility; `syscall`/`sysenter`/
   `cpuid`/`int` **fault** — no host call path exists. ✅ (C1)
3. Every run terminates within fuel + wall-clock bounds; a hung/crashed/runaway
   worker is contained and the orchestrator survives. ✅ (C2)
4. Runs are bit-for-bit reproducible from (organism, medium, T, λ, seed). ✅
5. Emulation runs in a separate, resource-clamped process. ✅ (C2) — network and
   writable-FS hard-walling is added by the container (C4, planned).

## Running under full containment (C4)

```sh
containment/run.sh                       # build + run the full self-test suite,
                                         # locked down (no network, read-only, etc.)
containment/run.sh python3 scripts/life.py   # run any command inside the box
```

`containment/run.sh` enforces `--network none`, a read-only root filesystem (only
an ephemeral tmpfs scratch is writable), `--cap-drop ALL`,
`--security-opt no-new-privileges`, a non-root user, and memory/cpu/pid caps.
`containment/selftest_all.py` runs inside and verifies both the science and the
walls (network blocked, root read-only, scratch writable) — all green on Linux.

## Operating rules

- Never run autonomous/long-horizon phases on a networked or privileged host;
  use the locked-down container (C4).
- Escalate deliberately: each new capability (populations, drift, larger arenas)
  gets a containment review before it runs.
- Humans approve every merge and every phase escalation.

## Honest disclaimer

This is **engineering containment, not a proof of safety**. The organisms here
are not adversarial; the controls nonetheless assume a guest could become
emulator-stressing under selection, and are layered so that no single failure
(an emulator bug, a missing trap, a runaway) reaches anything that matters. It is
not a substitute for independent security review before any networked or
privileged deployment.
