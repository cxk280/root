# memchr(p, len, byte) -> index or -1
.text
.globl kernel
kernel:
    xorq %rax, %rax
.loop:
    cmpq %rsi, %rax
    jae .notfound
    cmpb %dl, (%rdi,%rax)
    je .found
    incq %rax
    jmp .loop
.notfound:
    movq $-1, %rax
.found:
    ret
