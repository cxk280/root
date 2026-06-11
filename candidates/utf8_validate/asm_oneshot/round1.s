# utf8_validate(p, len) -> 1/0, RFC 3629 (overlongs, surrogates, >U+10FFFF)
.text
.globl kernel
kernel:
    xorq %rcx, %rcx
.loop:
    cmpq %rsi, %rcx
    jae .valid
    movzbl (%rdi,%rcx), %eax
    cmpl $0x80, %eax
    jb .ascii
    cmpl $0xC2, %eax
    jb .invalid
    cmpl $0xDF, %eax
    jbe .two
    cmpl $0xEF, %eax
    jbe .three
    cmpl $0xF4, %eax
    jbe .four
    jmp .invalid
.ascii:
    incq %rcx
    jmp .loop

.two:
    movq %rsi, %rdx
    subq %rcx, %rdx
    cmpq $2, %rdx
    jb .invalid
    movzbl 1(%rdi,%rcx), %edx
    andl $0xC0, %edx
    cmpl $0x80, %edx
    jne .invalid
    addq $2, %rcx
    jmp .loop

.three:
    movq %rsi, %rdx
    subq %rcx, %rdx
    cmpq $3, %rdx
    jb .invalid
    movzbl 1(%rdi,%rcx), %edx
    cmpl $0xE0, %eax
    jne .not_e0
    cmpl $0xA0, %edx
    jb .invalid
    cmpl $0xBF, %edx
    ja .invalid
    jmp .three_c2
.not_e0:
    cmpl $0xED, %eax
    jne .e_generic
    cmpl $0x80, %edx
    jb .invalid
    cmpl $0x9F, %edx
    ja .invalid
    jmp .three_c2
.e_generic:
    movl %edx, %r8d
    andl $0xC0, %r8d
    cmpl $0x80, %r8d
    jne .invalid
.three_c2:
    movzbl 2(%rdi,%rcx), %edx
    andl $0xC0, %edx
    cmpl $0x80, %edx
    jne .invalid
    addq $3, %rcx
    jmp .loop

.four:
    movq %rsi, %rdx
    subq %rcx, %rdx
    cmpq $4, %rdx
    jb .invalid
    movzbl 1(%rdi,%rcx), %edx
    cmpl $0xF0, %eax
    jne .not_f0
    cmpl $0x90, %edx
    jb .invalid
    cmpl $0xBF, %edx
    ja .invalid
    jmp .four_c2
.not_f0:
    cmpl $0xF4, %eax
    jne .f_generic
    cmpl $0x80, %edx
    jb .invalid
    cmpl $0x8F, %edx
    ja .invalid
    jmp .four_c2
.f_generic:
    movl %edx, %r8d
    andl $0xC0, %r8d
    cmpl $0x80, %r8d
    jne .invalid
.four_c2:
    movzbl 2(%rdi,%rcx), %edx
    andl $0xC0, %edx
    cmpl $0x80, %edx
    jne .invalid
    movzbl 3(%rdi,%rcx), %edx
    andl $0xC0, %edx
    cmpl $0x80, %edx
    jne .invalid
    addq $4, %rcx
    jmp .loop

.valid:
    movl $1, %eax
    ret
.invalid:
    xorl %eax, %eax
    ret
