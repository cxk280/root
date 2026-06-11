# Blob ABI — the contract every candidate follows

A candidate is a flat x86-64 code blob executed inside the Unicorn emulator.
The runner (`harness/runner.py`) enforces this contract; candidates that
deviate simply fail.

## Memory map (fixed, identical for every run)

| Region  | Base         | Size   | Perms | Purpose                                  |
|---------|--------------|--------|-------|------------------------------------------|
| CODE    | `0x0001_0000`| 64 KiB | RWX   | the blob (RWX: self-modification is legal)|
| RODATA  | `0x0004_0000`| 64 KiB | R     | constant pools from compiled C objects    |
| IN      | `0x0020_0000`| 64 KiB | RW    | input buffer (test vector bytes)          |
| OUT     | `0x0030_0000`| 64 KiB | RW    | output buffer (zeroed before each run)    |
| STACK   | `0x7F00_0000`| 1 MiB  | RW    | RSP starts at `0x7F0F_F000`               |
| HALT    | `0x00DE_A000`| 4 KiB  | RX    | magic return page (see Termination)       |

## Calling convention

- Integer/pointer arguments in **RDI, RSI, RDX, RCX** (in that order).
  In test vectors, the placeholders `"IN"` and `"OUT"` resolve to the IN/OUT
  buffer base addresses.
- Result in **RAX**. Kernels that produce bytes write them to OUT and return
  the output length (or status) in RAX.
- All other registers are scratch — no callee-saved obligations.
- The stack is usable (call/push/pop fine). No red-zone guarantees needed.

## Entry and termination

- Entry: for ELF objects, the symbol named `kernel`; for raw blobs, offset 0
  of CODE.
- At entry, `[RSP]` holds the magic return address `0x00DE_A000`. A plain
  `ret` from the entry frame therefore halts emulation cleanly.

## Limits

- **Fuel:** 2,000,000 dynamic instructions per test vector; exceeding it is a
  failure (`fuel_exhausted`). 5 s wall-clock backstop.
- **No syscalls.** Any `syscall`/`int`/`sysenter` faults the run.
- ISA: baseline x86-64 (SSE2). No AVX, no FS/GS-relative addressing.
- Reads/writes outside mapped regions fault the run (`memory_fault`).

## Measurement

- **Dynamic instruction count** via a Unicorn code hook — exact, deterministic.
- **Code size** = byte length of the blob (`.text` for compiled objects).
