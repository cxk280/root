# forager_sweep — the non-cognitive control. It IGNORES the gradient and simply
# sweeps right (wrapping), so it passes over food periodically but never tracks
# it. It should harvest far less and starve where the chemotactic forager lives —
# the foraging analogue of `rock`/`blind`: motion without sensing is not foraging.
.set POS,  64
.set WMAX, 63
.text
.globl kernel
kernel:
    movabsq $0x10000, %rsi
    movzbl POS(%rsi), %eax
    incl %eax
    cmpl $WMAX, %eax
    jle .ok
    xorl %eax, %eax              # wrap 63 -> 0
.ok:
    movb %al, POS(%rsi)
    ret
