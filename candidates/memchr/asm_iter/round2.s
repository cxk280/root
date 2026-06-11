# memchr, condition C (round 2): SWAR 8-bytes-at-a-time + scalar tail.
# Feedback from round 1 (asm_oneshot): correct 10/10 but 7322 dyn-instr on
# holdout, slower than clang -Os (6157) which did NOT vectorize. The scalar
# loop costs ~5 instr/byte; SWAR scans 8 bytes in ~12 instr (~1.5/byte).
#
# Match-detection: xor each word with broadcast(byte) so a matching byte
# becomes 0x00, then haszero(v) = (v - 0x01..01) & ~v & 0x80..80 marks zero
# bytes; bsf gives the lowest, /8 is its index. Only FULL words (len & ~7)
# are read so we never read past the buffer; the remainder is scalar.
.text
.globl kernel
kernel:
    movzbl %dl, %r8d                       # r8b = needle (for the tail)
    movabsq $0x0101010101010101, %rcx
    movq %r8, %r11
    imulq %rcx, %r11                        # r11 = broadcast(needle)
    movq %rsi, %r9
    andq $-8, %r9                           # r9 = len & ~7  (full-word bytes)
    xorq %rax, %rax                         # rax = index
.wordloop:
    cmpq %r9, %rax
    jae .tail
    movq (%rdi,%rax), %rcx
    xorq %r11, %rcx                         # matching lane -> 0x00
    movq %rcx, %r10
    movabsq $0x0101010101010101, %rdx
    subq %rdx, %r10
    notq %rcx
    andq %rcx, %r10
    movabsq $0x8080808080808080, %rdx
    andq %rdx, %r10                         # 0x80 set in each zero (match) lane
    jnz .found_word
    addq $8, %rax
    jmp .wordloop
.found_word:
    bsfq %r10, %rcx                         # lowest marker bit
    shrq $3, %rcx                           # -> byte index within the word
    addq %rcx, %rax
    ret
.tail:
    cmpq %rsi, %rax
    jae .notfound
    cmpb %r8b, (%rdi,%rax)
    je .done                                # rax already holds the index
    incq %rax
    jmp .tail
.notfound:
    movq $-1, %rax
.done:
    ret
