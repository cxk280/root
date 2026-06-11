# protocell0 — the first organism intended to LIVE with genuine closure quality.
#
# Each cycle it (1) READS its membrane marker from its own body and dies if the
# boundary is gone, (2) READS its self-described extent N from its own body, and
# (3) re-synthesizes the whole body [0,N) — code AND the marker/extent data —
# back into itself. There is no external master: the bytes that do the copying
# are themselves copied by the copying (organizational closure), and the
# boundary it maintains both conditions production (the copy bound is read from
# self) and conditions life-or-death (a dissolved marker is self-detected and
# the organism leaps out of its own body to dissolve). Under the solvent sweep,
# survival requires re-laying all N bytes within the sweep period T — that is the
# metabolic-rate phase transition the assay measures.
#
# NOTE (honest limitation, by design): the refresh is an IDENTITY copy, so it
# defeats neglect-decay but performs no error CORRECTION. This is the expected
# stage-1 shape; it is exactly why protocell0 is predicted to die at rung 2
# (bit-rot), where it must grow real repair to survive.
.text
.globl kernel
kernel:
start:
    movabsq $0x10000, %rsi               # self base = ARENA_BASE
    movq (marker - start)(%rsi), %rax    # READ the membrane (boundary read)
    movabsq $0xA5A5A5A5A5A5A5A5, %rdx
    cmpq %rdx, %rax
    jne die                              # boundary dissolved -> dissolve self
    movq (extent - start)(%rsi), %rcx    # READ self-described extent N
    xorq %rax, %rax
refresh:
    movb (%rsi,%rax), %dl                # re-synthesize the whole body into self
    movb %dl, (%rsi,%rax)
    incq %rax
    cmpq %rcx, %rax
    jb refresh
    jmp start
die:
    movabsq $0x0DEAD000, %rax
    jmp *%rax                            # leap out of the body -> fault -> death
.p2align 3
marker:
    .quad 0xA5A5A5A5A5A5A5A5             # self-produced boundary sentinel
extent:
    .quad end - start                    # self-described body length N
end:
