# popcount, SWAR (no popcnt: baseline x86-64 only)
.text
.globl kernel
kernel:
    movq %rdi, %rax
    movq %rax, %rcx
    shrq $1, %rcx
    movabsq $0x5555555555555555, %rdx
    andq %rdx, %rcx
    subq %rcx, %rax
    movabsq $0x3333333333333333, %rdx
    movq %rax, %rcx
    andq %rdx, %rax
    shrq $2, %rcx
    andq %rdx, %rcx
    addq %rcx, %rax
    movq %rax, %rcx
    shrq $4, %rcx
    addq %rcx, %rax
    movabsq $0x0F0F0F0F0F0F0F0F, %rdx
    andq %rdx, %rax
    movabsq $0x0101010101010101, %rdx
    imulq %rdx, %rax
    shrq $56, %rax
    ret
