# protocell2 — TMR with a TIGHTER germ (64-bit-word majority repair).
#
# Same triple modular redundancy as protocell1, but the repair loop votes a full
# 8-byte word per iteration instead of a byte, so a full self-pass is 8x fewer
# iterations. This tests one of the two levers on the "who repairs the repairer"
# cap: shrinking the executing germ. (The other lever, dilution, and the real fix,
# redundant execution, are tested separately — see results/protocell/RUNG2.md.)
.set L,    160                  # one body's length (multiple of 8); birth = 3*L
.set LL,   320
.set MARK, 128
.text
.globl kernel
kernel:
start:
    movabsq $0x10000, %rcx           # base0 (executing copy)
    leaq L(%rcx), %rdi               # base1
    leaq LL(%rcx), %rsi              # base2
    xorq %rax, %rax                  # i (byte offset, +8 each step)
rloop:
    movq (%rcx,%rax), %r8            # a = copy0[i..i+8]
    movq (%rdi,%rax), %r9            # b
    movq (%rsi,%rax), %r10           # c
    movq %r8, %r11
    andq %r9, %r11                   # a & b
    movq %r8, %rdx
    andq %r10, %rdx                  # a & c
    orq  %rdx, %r11
    movq %r9, %rdx
    andq %r10, %rdx                  # b & c
    orq  %rdx, %r11                  # 64-bit bitwise majority
    movq %r11, (%rcx,%rax)           # consensus -> all three copies
    movq %r11, (%rdi,%rax)
    movq %r11, (%rsi,%rax)
    addq $8, %rax
    cmpq $L, %rax
    jb rloop
    movq MARK(%rcx), %rax            # boundary check on repaired copy0
    movabsq $0xA5A5A5A5A5A5A5A5, %rdx
    cmpq %rdx, %rax
    jne die
    jmp start
die:
    movabsq $0x0DEAD000, %rax
    jmp *%rax
.org MARK
marker:
    .quad 0xA5A5A5A5A5A5A5A5
extent:
    .quad L
.org L
end:
