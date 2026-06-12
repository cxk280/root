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

The faults confirm the memory and control-flow walls hold. The `syscall` result
is the actionable finding: it cannot reach the host (Unicorn emulates the CPU; it
is not a hypervisor with syscall passthrough), but it is currently **not
explicitly trapped** — we lean on Unicorn's default instead of enforcing the
invariant. **Hardening item C1** closes this by trapping `syscall`/`sysenter` to a
fault and asserting it in a containment self-test, so "no privileged/OS
instructions reach anything" becomes tested, not assumed.

## Residual risks and controls

| # | Risk | Control | Status |
|---|---|---|---|
| R1 | **Emulator implementation bug** (Unicorn ← QEMU TCG lineage) lets crafted guest code corrupt/execute in the *host process*. | Run emulation in an **isolated worker process** under an OS sandbox (memory/CPU rlimits, no network, read-only FS except a results dir, no child processes, no core dumps). Pin & record the Unicorn version. So even a full emulator escape lands in a process that can do nothing. | **planned (C2)** |
| R2 | Escaped code inherits the **host user's privileges**. | Worker drops to least privilege; the surrounding room is empty (R1 controls). | planned (C2) |
| R3 | **Resource exhaustion / runaway** across many runs or large populations. | Hard caps: fuel + wall-clock + lifetime (in place); add memory rlimit, total-runtime budget, population-size and disk-write caps. | partial → C3 |
| R4 | **Unattended autonomous evolution** (Phase 4 natural drift) does something unexpected over long horizons. | Run autonomous phases in a **no-network container/VM**, ephemeral FS, kill-switch + max-wallclock, human checkpoint cadence; never on a host with sensitive access. Human-in-the-loop on every merge (already a project rule). | at that phase (C4) |
| R5 | **Supply chain** (Unicorn/Capstone/toolchain). | Pin and record versions + hashes in run records; the in-repo `ctypes` shim avoids a PyPI binary for Unicorn (binds the system lib). | ongoing (C5) |
| R6 | **Nondeterminism leak** (e.g. `rdtsc`) undermines auditability. | Note in records; optionally trap/zero such instructions in a deterministic-mode hook. | tracked (C6) |

## Invariants (to be test-enforced by a containment self-test)

1. Guest memory writes/reads/fetches outside the mapped arena **fault**.
2. Guest cannot map memory or invoke any OS facility; `syscall`/`sysenter`/`int`
   **fault** (after C1) — no host call path exists.
3. Every run terminates within fuel + wall-clock bounds.
4. Runs are bit-for-bit reproducible from (organism, medium, T, λ, seed).
5. Emulation runs in a process that itself has no network and no writable FS
   outside a designated results dir (after C2).

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
