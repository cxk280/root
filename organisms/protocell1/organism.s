# protocell1 — the error-CORRECTING organism, grown from protocell0's death.
#
# protocell0 lives under the solvent (neglect-decay) but dies under bit-rot,
# because its identity-copy refresh propagates corruption it cannot detect. The
# fix is redundancy: protocell1 keeps THREE copies of its body and, each cycle,
# repairs itself by bitwise MAJORITY across the copies —
#       m = (a&b) | (a&c) | (b&c)
# computed per byte and written back to all three. Any single-copy bit flip is
# outvoted 2-to-1 and healed. The organism dies only when corruption defeats the
# vote (>=2 copies hit at the same bit between repair passes) or strikes the
# executing copy's code before the pass heals it — that boundary is the error
# catastrophe λ* the assay measures.
#
# The build step (medium/build.py, replicate=3) triplicates this single L-byte
# body into the 3L birth image; all three copies are byte-identical, and because
# the code addresses absolute copies at base, base+L, base+2L, the same machine
# code is correct in every copy.
#
# Layout: code | pad | marker | extent, padded with .org to exactly L bytes.
.set L,    160                 # one body's length (birth image is 3*L)
.set LL,   320                 # 2*L
.set MARK, 128                 # offset of the membrane descriptor within a body
.text
.globl kernel
kernel:
start:
    movabsq $0x10000, %rcx          # base0 = copy 0 (the executing copy)
    leaq L(%rcx), %rdi              # base1 = copy 1
    leaq LL(%rcx), %rsi             # base2 = copy 2
    xorq %rax, %rax                 # i = 0
rloop:                              # --- bitwise-majority repair across copies ---
    movb (%rcx,%rax), %r8b          # a = copy0[i]
    movb (%rdi,%rax), %r9b          # b = copy1[i]
    movb (%rsi,%rax), %r10b         # c = copy2[i]
    movb %r8b, %r11b
    andb %r9b, %r11b                # a & b
    movb %r8b, %dl
    andb %r10b, %dl                 # a & c
    orb  %dl, %r11b
    movb %r9b, %dl
    andb %r10b, %dl                 # b & c
    orb  %dl, %r11b                 # r11b = majority(a,b,c)
    movb %r11b, (%rcx,%rax)         # write consensus back to all three copies
    movb %r11b, (%rdi,%rax)
    movb %r11b, (%rsi,%rax)
    incq %rax
    cmpq $L, %rax
    jb rloop
    movq MARK(%rcx), %rax           # read the (now-repaired) membrane in copy0
    movabsq $0xA5A5A5A5A5A5A5A5, %rdx
    cmpq %rdx, %rax
    jne die                         # boundary irrecoverable -> dissolve
    jmp start
die:
    movabsq $0x0DEAD000, %rax
    jmp *%rax
.org MARK                           # pad to the membrane descriptor
marker:
    .quad 0xA5A5A5A5A5A5A5A5         # self-produced boundary sentinel
extent:
    .quad L                          # self-described single-body length
.org L                              # pad the body to exactly L bytes
end:
