# forager0 — CHEMOTAXIS (Rung 2.7). One forage action per window: sense the
# local chemical gradient and take a single step toward food, then return.
#
# The medium writes, into this organism's sensor cells, the gradient signal at
# its left (pos-1), here (pos), and right (pos+1). The organism compares the two
# flanks and steps toward the stronger — climbing the gradient to a nutrient that
# drifts through the world. Behavior tracks the world; this is Maturana &
# Varela's chemotaxing bacterium, the paradigm of minimal cognition, in machine
# code. It eats only if it keeps up; otherwise it starves (the medium's job).
.set POS,   64                   # this organism's position byte (it owns it)
.set SENSE, 72                   # 3 sensor cells the medium writes: pos-1, pos, pos+1
.set WMAX,  63                   # world is [0, 63]
.text
.globl kernel
kernel:
    movabsq $0x10000, %rsi        # body base
    movzbl SENSE+0(%rsi), %ecx    # signal to the left  (pos-1)
    movzbl SENSE+2(%rsi), %edx    # signal to the right (pos+1)
    movzbl POS(%rsi), %eax        # current position
    cmpl %ecx, %edx
    jg .right                     # right flank stronger -> step right
    jl .left                      # left flank stronger  -> step left
    ret                           # equal -> stay put
.right:
    cmpl $WMAX, %eax
    jge .end                      # at the wall -> stay
    incl %eax
    movb %al, POS(%rsi)
    ret
.left:
    testl %eax, %eax
    jle .end                      # at the wall -> stay
    decl %eax
    movb %al, POS(%rsi)
.end:
    ret
