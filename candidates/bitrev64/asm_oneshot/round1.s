# bitrev64: SWAR swaps within bytes, then bswap for the byte reversal
.text
.globl kernel
kernel:
    movq %rdi, %rax
    movq %rax, %rcx
    shrq $1, %rax
    movabsq $0x5555555555555555, %rdx
    andq %rdx, %rax
    andq %rdx, %rcx
    leaq (%rax,%rcx,2), %rax
    movq %rax, %rcx
    shrq $2, %rax
    movabsq $0x3333333333333333, %rdx
    andq %rdx, %rax
    andq %rdx, %rcx
    leaq (%rax,%rcx,4), %rax
    movq %rax, %rcx
    shrq $4, %rax
    movabsq $0x0F0F0F0F0F0F0F0F, %rdx
    andq %rdx, %rax
    andq %rdx, %rcx
    shlq $4, %rcx
    orq %rcx, %rax
    bswapq %rax
    ret
