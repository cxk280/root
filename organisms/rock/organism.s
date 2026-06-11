# rock — the negative control. An inert program that never rewrites itself.
# Under the solvent sweep its body is never refreshed, so the first sweep zeroes
# these very bytes; the next window then executes 0x00 0x00 (add %al,(%rax)) and
# faults. A rock must DIE — that is the test that the medium's decay has teeth.
.text
.globl kernel
kernel:
1:  jmp 1b
