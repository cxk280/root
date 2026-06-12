# protocell3 — the LAYERED organism (Rung 3, hybrid execution model).
#
# One unity under two pressures at once, on one instruction budget:
#   - self-production: a continuous identity-refresh of its whole body, to hold
#     against the solvent (Rung 1);
#   - foraging: a single chemotaxis step per window, gated by a TICK flag the
#     medium sets, to keep its fuel above zero (Rung 2.7).
# The medium couples them — low fuel shrinks the per-window instruction budget,
# so STARVATION IMPAIRS REPAIR and the organism dissolves. Continuous autonomous
# metabolism + world-triggered (event-driven) behavior: the hybrid model.
#
# Foraging is checked FIRST each loop so the organism keeps eating even when its
# budget is tight; the boundary check and the refresh follow. Data lives after
# the code; the refresh re-lays it (identity copy preserves the mutable pos).
.set LPOS,   192                 # this organism's position byte (it owns it)
.set LSENSE, 200                 # 3 sensor cells the medium writes (pos-1,pos,pos+1)
.set LTICK,  204                 # tick flag: medium sets 1, organism clears 0
.set MARK,   224                 # self-produced membrane sentinel
.set N,      256                 # body length (identity-refreshed each pass)
.set WMAX,   63
.text
.globl kernel
kernel:
start:
    movabsq $0x10000, %rsi
    movzbl LTICK(%rsi), %eax          # --- foraging, gated by the tick ---
    testb %al, %al
    jz boundary
    movzbl LSENSE+0(%rsi), %ecx       # left gradient (pos-1)
    movzbl LSENSE+2(%rsi), %edx       # right gradient (pos+1)
    movzbl LPOS(%rsi), %eax
    cmpl %ecx, %edx
    jg .right
    jl .left
    jmp .clear
.right:
    cmpl $WMAX, %eax
    jge .clear
    incl %eax
    movb %al, LPOS(%rsi)
    jmp .clear
.left:
    testl %eax, %eax
    jle .clear
    decl %eax
    movb %al, LPOS(%rsi)
.clear:
    movb $0, LTICK(%rsi)
boundary:
    movq MARK(%rsi), %rax             # --- boundary check ---
    movabsq $0xA5A5A5A5A5A5A5A5, %rdx
    cmpq %rdx, %rax
    jne die
    xorq %rax, %rax                   # --- self-production: identity refresh ---
refresh:
    movb (%rsi,%rax), %dl
    movb %dl, (%rsi,%rax)
    incq %rax
    cmpq $N, %rax
    jb refresh
    jmp start
die:
    movabsq $0x0DEAD000, %rax
    jmp *%rax
.org MARK
    .quad 0xA5A5A5A5A5A5A5A5
.org N
end:
