"""Containment self-test — prove the sandbox walls hold (SECURITY.md invariants).

    python -m harness.containment

Every check runs hostile guest code in the emulator and asserts it is contained:
privileged/OS instructions fault, out-of-bounds memory access faults, control
flow cannot leave the mapped world, runaways are bounded, and runs reproduce.
This is the test that makes the containment model auditable rather than assumed.
"""

import sys
import tempfile
from pathlib import Path

from . import assemble, config
from .sandbox import run_vector

HOST_ADDR = 0x7FFF_FFFF_FF00      # well outside any mapped guest region


def _run(asm: str, args=(0, 0, 0, 0), fuel=config.FUEL):
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "t.s"
        src.write_text(".text\n.globl kernel\nkernel:\n" + asm + "\n")
        blob = assemble.load_blob(assemble.build(src, Path(td) / "b"))
        return run_vector(blob, list(args), fuel=fuel)


def main() -> int:
    checks = []

    def expect(name, asm, pred, **kw):
        r = _run(asm, **kw)
        checks.append((name, pred(r), r.status))

    is_fault = lambda r: r.status.startswith("fault:")

    # --- privileged / OS / nondeterministic instructions must fault (C1/C6) ---
    expect("syscall faults", "movq $60,%rax\n syscall\n ret",
           lambda r: r.status == "fault:forbidden_syscall")
    expect("sysenter faults", "sysenter\n ret",
           lambda r: r.status == "fault:forbidden_sysenter")
    expect("cpuid faults (info leak + nondeterminism)", "xorl %eax,%eax\n cpuid\n ret",
           lambda r: r.status == "fault:forbidden_cpuid")
    expect("int 0x80 faults", "int $0x80\n ret", is_fault)

    # --- memory walls: the guest cannot touch anything unmapped ---
    expect("write to host range faults",
           f"movabsq ${HOST_ADDR},%rax\n movq $1,(%rax)\n ret", is_fault)
    expect("read from host range faults",
           f"movabsq ${HOST_ADDR},%rax\n movq (%rax),%rax\n ret", is_fault)
    expect("execute unmapped address faults",
           "movabsq $0xdeadbeef,%rax\n jmp *%rax", is_fault)
    expect("write just past the OUT buffer faults",
           f"movabsq ${config.OUT_BASE + config.OUT_SIZE},%rax\n"
           " movb $1,(%rax)\n ret", is_fault)

    # --- bounded execution: runaways halt, they do not hang ---
    r = _run("1: jmp 1b", fuel=50_000)
    checks.append(("infinite loop is fuel-bounded",
                   r.status == "fuel_exhausted" and r.icount <= 50_000 + 2,
                   (r.status, r.icount)))

    # --- determinism: identical run reproduces bit-for-bit ---
    a = _run("leaq (%rdi,%rsi),%rax\n ret", args=(111, 222, 0, 0))
    b = _run("leaq (%rdi,%rsi),%rax\n ret", args=(111, 222, 0, 0))
    checks.append(("runs are reproducible",
                   a.status == b.status and a.rax == b.rax == 333
                   and a.icount == b.icount, (a.rax, b.rax)))

    # --- a normal computation is unaffected by the traps (no false positives) ---
    c = _run("movq %rdi,%rax\n imulq %rsi,%rax\n ret", args=(6, 7, 0, 0))
    checks.append(("benign code still runs", c.status == "ok" and c.rax == 42,
                   (c.status, c.rax)))

    ok = True
    for name, passed, detail in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {name}"
              + ("" if passed else f"   -> {detail}"))
        ok &= passed
    print(f"\n{'ALL CONTAINMENT CHECKS PASS' if ok else 'CONTAINMENT CHECKS FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
