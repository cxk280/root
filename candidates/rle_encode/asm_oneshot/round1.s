# rle_encode(in, len, out) -> bytes written; (count 1..255, value) pairs
.text
.globl kernel
kernel:
    xorq %rax, %rax
    xorq %rcx, %rcx
.outer:
    cmpq %rsi, %rcx
    jae .done
    movzbl (%rdi,%rcx), %r8d
    movl $1, %r9d
.run:
    leaq (%rcx,%r9), %r10
    cmpq %rsi, %r10
    jae .emit
    cmpb %r8b, (%rdi,%r10)
    jne .emit
    cmpq $255, %r9
    jae .emit
    incq %r9
    jmp .run
.emit:
    movb %r9b, (%rdx,%rax)
    incq %rax
    movb %r8b, (%rdx,%rax)
    incq %rax
    addq %r9, %rcx
    jmp .outer
.done:
    ret
