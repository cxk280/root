# crc32 (reflected 0xEDB88320, init/xorout 0xFFFFFFFF), bitwise
.text
.globl kernel
kernel:
    movl $0xFFFFFFFF, %eax
    testq %rsi, %rsi
    jz .done
    xorq %rcx, %rcx
.byte_loop:
    movzbl (%rdi,%rcx), %edx
    xorl %edx, %eax
    movl $8, %r8d
.bit_loop:
    movl %eax, %edx
    shrl $1, %eax
    andl $1, %edx
    negl %edx
    andl $0xEDB88320, %edx
    xorl %edx, %eax
    decl %r8d
    jnz .bit_loop
    incq %rcx
    cmpq %rsi, %rcx
    jb .byte_loop
.done:
    notl %eax
    ret
