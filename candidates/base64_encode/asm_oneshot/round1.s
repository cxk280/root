# base64_encode(in, len, out) -> bytes written; RFC 4648 with padding
.section .rodata
alpha:
    .ascii "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
.text
.globl kernel
kernel:
    leaq alpha(%rip), %r11
    xorq %rax, %rax
    xorq %rcx, %rcx
.main:
    movq %rsi, %r8
    subq %rcx, %r8
    cmpq $3, %r8
    jb .tail
    movzbl (%rdi,%rcx), %r9d
    shll $16, %r9d
    movzbl 1(%rdi,%rcx), %r10d
    shll $8, %r10d
    orl %r10d, %r9d
    movzbl 2(%rdi,%rcx), %r10d
    orl %r10d, %r9d
    movl %r9d, %r10d
    shrl $18, %r10d
    andl $63, %r10d
    movzbl (%r11,%r10), %r10d
    movb %r10b, (%rdx,%rax)
    incq %rax
    movl %r9d, %r10d
    shrl $12, %r10d
    andl $63, %r10d
    movzbl (%r11,%r10), %r10d
    movb %r10b, (%rdx,%rax)
    incq %rax
    movl %r9d, %r10d
    shrl $6, %r10d
    andl $63, %r10d
    movzbl (%r11,%r10), %r10d
    movb %r10b, (%rdx,%rax)
    incq %rax
    movl %r9d, %r10d
    andl $63, %r10d
    movzbl (%r11,%r10), %r10d
    movb %r10b, (%rdx,%rax)
    incq %rax
    addq $3, %rcx
    jmp .main
.tail:
    testq %r8, %r8
    jz .done
    movzbl (%rdi,%rcx), %r9d
    shll $16, %r9d
    cmpq $2, %r8
    jne .emit_head
    movzbl 1(%rdi,%rcx), %r10d
    shll $8, %r10d
    orl %r10d, %r9d
.emit_head:
    movl %r9d, %r10d
    shrl $18, %r10d
    andl $63, %r10d
    movzbl (%r11,%r10), %r10d
    movb %r10b, (%rdx,%rax)
    incq %rax
    movl %r9d, %r10d
    shrl $12, %r10d
    andl $63, %r10d
    movzbl (%r11,%r10), %r10d
    movb %r10b, (%rdx,%rax)
    incq %rax
    cmpq $2, %r8
    jne .pad2
    movl %r9d, %r10d
    shrl $6, %r10d
    andl $63, %r10d
    movzbl (%r11,%r10), %r10d
    movb %r10b, (%rdx,%rax)
    incq %rax
    movb $61, (%rdx,%rax)
    incq %rax
    jmp .done
.pad2:
    movb $61, (%rdx,%rax)
    incq %rax
    movb $61, (%rdx,%rax)
    incq %rax
.done:
    ret
