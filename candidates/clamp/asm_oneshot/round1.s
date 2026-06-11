# clamp(v, lo, hi), signed, branchless
.text
.globl kernel
kernel:
    movq %rdi, %rax
    cmpq %rsi, %rax
    cmovl %rsi, %rax
    cmpq %rdx, %rax
    cmovg %rdx, %rax
    ret
