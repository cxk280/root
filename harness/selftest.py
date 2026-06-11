"""Harness self-tests: prove the rig itself before trusting any measurement.

    python -m harness.selftest
"""

import sys
import tempfile
from pathlib import Path

from . import assemble, config
from .sandbox import run_vector

ADD_ASM = """\
.text
.globl kernel
kernel:
    leaq (%rdi,%rsi), %rax
    ret
"""

LOOP_ASM = """\
.text
.globl kernel
kernel:
1:  jmp 1b
"""

BADMEM_ASM = """\
.text
.globl kernel
kernel:
    movq 0, %rax
    ret
"""

OUTWRITE_ASM = """\
.text
.globl kernel
kernel:                      # copy first byte of IN to OUT, rax = 1
    movb (%rdi), %al
    movb %al, (%rdx)
    movq $1, %rax
    ret
"""

TABLE_C = """\
/* exercises .rodata + relocations under -O3 */
static const unsigned long t[4] = {11, 22, 33, 44};
unsigned long kernel(unsigned long x) { return t[x & 3] + x; }
"""

SELFMOD_ASM = """\
.text
.globl kernel
kernel:                      # rewrite the placeholder immediate, then run it
    leaq patch+3(%rip), %rcx
    movl $42, (%rcx)
patch:
    movq $0, %rax
    ret
"""


def _build(src_text: str, suffix: str, tmp: Path, opt: str = "-O3") -> Path:
    src = tmp / f"t{abs(hash(src_text)) % 10_000}{suffix}"
    src.write_text(src_text)
    return assemble.build(src, tmp / (src.stem + "_blob"), opt=opt)


def main() -> int:
    checks = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        blob = assemble.load_blob(_build(ADD_ASM, ".s", tmp))
        r = run_vector(blob, [7, 35])
        checks.append(("add: result", r.ok and r.rax == 42, r.status))
        checks.append(("add: exact icount == 2", r.icount == 2, r.icount))
        checks.append(("add: code size == blob bytes",
                       len(blob.code) > 0, len(blob.code)))

        r = run_vector(assemble.load_blob(_build(LOOP_ASM, ".s", tmp)),
                       [], fuel=10_000)
        checks.append(("infinite loop: fuel exhausted",
                       r.status == "fuel_exhausted" and r.icount >= 10_000,
                       (r.status, r.icount)))

        r = run_vector(assemble.load_blob(_build(BADMEM_ASM, ".s", tmp)), [])
        checks.append(("null read: memory fault",
                       r.status.startswith("fault:"), r.status))

        r = run_vector(assemble.load_blob(_build(OUTWRITE_ASM, ".s", tmp)),
                       ["IN", 1, "OUT"], in_bytes=b"\xab", out_read=1)
        checks.append(("OUT buffer: written and read back",
                       r.ok and r.rax == 1 and r.out == b"\xab",
                       (r.status, r.out.hex())))

        blob = assemble.load_blob(_build(TABLE_C, ".c", tmp))
        r = run_vector(blob, [6])
        checks.append(("C -O3 rodata+reloc: t[2]+6 == 39",
                       r.ok and r.rax == 39, (r.status, r.rax)))

        r = run_vector(assemble.load_blob(_build(SELFMOD_ASM, ".s", tmp)), [])
        checks.append(("self-modifying code is legal in CODE (RWX)",
                       r.ok and r.rax == 42, (r.status, r.rax)))

        # A wrong candidate must FAIL scoring (guards against vacuous passes).
        from .runner import score
        wrong = assemble.load_blob(_build(ADD_ASM, ".s", tmp))
        rep = score(wrong, [{"args": [1, 1], "expect": {"rax": 3}}])
        checks.append(("scorer rejects wrong result", not rep["all_pass"], rep["n_pass"]))

    ok = True
    for name, passed, detail in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {name}" +
              ("" if passed else f"   -> {detail}"))
        ok &= passed
    print(f"\n{'ALL SELF-TESTS PASS' if ok else 'SELF-TESTS FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
