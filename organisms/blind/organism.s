# blind — a degenerate "organism" that survives without genuine closure quality.
# It refreshes its whole body every cycle (so the solvent never catches it), but
# its extent is a hardcoded immediate and it never CONSULTS its own state: there
# is no self-produced boundary and production is not conditioned on self. It is
# self-producing in the letter, not in spirit. The assay must rank it ALIVE but
# LOW-closure, below protocell0 — and it is exactly the organism expected to die
# at rung 2 (bit-rot), since a blind identity copy cannot repair what it cannot
# detect.
.text
.globl kernel
kernel:
    movabsq $0x10000, %rsi          # self base (hardcoded; not read from self)
    xorq %rax, %rax
1:
    movb (%rsi,%rax), %dl           # identity refresh: b[i] = b[i]
    movb %dl, (%rsi,%rax)
    incq %rax
    cmpq $96, %rax                  # hardcoded extent; never consults a boundary
    jb 1b
    jmp kernel
