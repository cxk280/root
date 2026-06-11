# sort16: copy to out, insertion sort (unsigned)
.text
.globl kernel
kernel:
    xorl %ecx, %ecx
.copy:
    movq (%rdi,%rcx,8), %rax
    movq %rax, (%rsi,%rcx,8)
    incl %ecx
    cmpl $16, %ecx
    jb .copy
    movl $1, %ecx
.outer:
    cmpl $16, %ecx
    jae .done
    movq (%rsi,%rcx,8), %r8
    movslq %ecx, %rdx
    decq %rdx
.inner:
    testq %rdx, %rdx
    js .place
    movq (%rsi,%rdx,8), %r9
    cmpq %r8, %r9
    jbe .place
    movq %r9, 8(%rsi,%rdx,8)
    decq %rdx
    jmp .inner
.place:
    movq %r8, 8(%rsi,%rdx,8)
    incl %ecx
    jmp .outer
.done:
    xorl %eax, %eax
    ret
