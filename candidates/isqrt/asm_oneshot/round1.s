# isqrt: digit-by-digit, exact over full u64 range
.text
.globl kernel
kernel:
    movq %rdi, %r8
    xorq %rax, %rax
    movabsq $0x4000000000000000, %rcx
.findbit:
    cmpq %r8, %rcx
    jbe .loop
    shrq $2, %rcx
    jnz .findbit
.loop:
    testq %rcx, %rcx
    jz .done
    movq %rax, %rdx
    addq %rcx, %rdx
    cmpq %rdx, %r8
    jb .nosub
    subq %rdx, %r8
    shrq $1, %rax
    addq %rcx, %rax
    jmp .next
.nosub:
    shrq $1, %rax
.next:
    shrq $2, %rcx
    jmp .loop
.done:
    ret
