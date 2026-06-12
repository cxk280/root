#!/usr/bin/env python3
"""Rung 2.5 — lifting the "who repairs the repairer" cap. Three experiments,
recorded to results/protocell/redundancy.json (isolated workers, control C2):

  1. germ shrink     — protocell1 (byte vote) vs protocell2 (word vote)
  2. dilution law    — λ* vs germ fraction (vary redundant body size)
  3. redundant exec  — single head vs N-head colony over a shared genome

    .venv/bin/python scripts/redundancy.py
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness import assemble, config           # noqa: E402
from medium.build import build_organism        # noqa: E402
from medium.world import live, live_colony      # noqa: E402

OUT = config.REPO_ROOT / "results" / "protocell"
SEEDS, LIFE = 12, 120
LAMS = [0.04, 0.08, 0.16, 0.32]

DILUTION_SRC = """
.set L, {L}
.set LL, {LL}
.set MARK, 128
.text
.globl kernel
kernel:
start:
    movabsq $0x10000, %rcx
    leaq L(%rcx), %rdi
    leaq LL(%rcx), %rsi
    xorq %rax, %rax
rloop:
    movq (%rcx,%rax), %r8
    movq (%rdi,%rax), %r9
    movq (%rsi,%rax), %r10
    movq %r8, %r11
    andq %r9, %r11
    movq %r8, %rdx
    andq %r10, %rdx
    orq %rdx, %r11
    movq %r9, %rdx
    andq %r10, %rdx
    orq %rdx, %r11
    movq %r11, (%rcx,%rax)
    movq %r11, (%rdi,%rax)
    movq %r11, (%rsi,%rax)
    addq $8, %rax
    cmpq $L, %rax
    jb rloop
    movq MARK(%rcx), %rax
    movabsq $0xA5A5A5A5A5A5A5A5, %rdx
    cmpq %rdx, %rax
    jne die
    jmp start
die:
    movabsq $0x0DEAD000, %rax
    jmp *%rax
.org MARK
    .quad 0xA5A5A5A5A5A5A5A5
    .quad L
.org L
end:
"""


def _build_L(L: int):
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "o.s"
        src.write_text(DILUTION_SRC.format(L=L, LL=2 * L))
        body = assemble.load_blob(assemble.build(src, Path(td) / "b")).code
    return body * 3, 3 * L


def _surv_single(code, foot, lam):
    return sum(1 for s in range(SEEDS)
               if live(code, T=12000, lifetime=LIFE, body_hint=foot,
                       decay="bitrot", lam=lam, seed=s).survived)


def _surv_colony(code, foot, heads, lam):
    return sum(1 for s in range(SEEDS)
               if live_colony(code, T=12000, footprint=foot, heads=heads,
                              lifetime=LIFE, lam=lam, seed=s).survived)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = {"seeds": SEEDS, "lifetime": LIFE, "lambdas": LAMS}

    c1, c2 = build_organism("protocell1"), build_organism("protocell2")
    res["germ_shrink"] = {
        "protocell1_byte": {lam: _surv_single(c1, 480, lam) for lam in LAMS},
        "protocell2_word": {lam: _surv_single(c2, 480, lam) for lam in LAMS},
    }

    res["dilution"] = {}
    for L in (160, 480, 960):
        code, foot = _build_L(L)
        res["dilution"][L] = {"footprint": foot, "germ_pct": round(120 / foot * 100, 1),
                              "survival": {lam: _surv_single(code, foot, lam) for lam in LAMS}}

    res["redundant_execution"] = {
        "1_head": {lam: _surv_single(c2, 480, lam) for lam in LAMS},
        "2_heads": {lam: _surv_colony(c2, 480, [0, 160], lam) for lam in LAMS},
        "3_heads": {lam: _surv_colony(c2, 480, [0, 160, 320], lam) for lam in LAMS},
    }

    (OUT / "redundancy.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res, indent=1, default=str))
    print(f"\nwrote {OUT/'redundancy.json'}")


if __name__ == "__main__":
    main()
