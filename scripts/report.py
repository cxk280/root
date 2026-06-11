#!/usr/bin/env python3
"""Aggregate results/runs/*.json into the per-kernel comparison table.

    .venv/bin/python scripts/report.py

Prints a Markdown table to stdout. "asm final" = the latest asm_iter round if
one exists, else asm_oneshot. Winner columns compare asm-final to the better of
the two C builds.
"""

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from kernels.genvectors import KERNELS  # noqa: E402

RUNS = Path(__file__).resolve().parent.parent / "results" / "runs"


def load(kernel, tag):
    f = RUNS / f"{kernel}__{tag}.json"
    return json.loads(f.read_text()) if f.exists() else None


def asm_final(kernel):
    iters = sorted(RUNS.glob(f"{kernel}__asm_iter_r*.json"),
                   key=lambda p: int(p.stem.rsplit("r", 1)[1]))
    if iters:
        return json.loads(iters[-1].read_text())
    return load(kernel, "asm_oneshot")


def hv(rec):  # holdout pass string, icount, size
    h = rec["holdout"]
    return f"{h['n_pass']}/{h['n_total']}", h["total_icount"], rec["code_size"]


def main():
    rows = []
    tallies = dict(asm_speed=0, c_speed=0, asm_small=0, b_correct=0,
                   c_correct=0, n=0)
    for k in KERNELS:
        c3, cs, af = load(k, "c_O3"), load(k, "c_Os"), asm_final(k)
        b = load(k, "asm_oneshot")
        if not (c3 and cs and af):
            continue
        tallies["n"] += 1
        _, c3_ic, c3_sz = hv(c3)
        _, cs_ic, cs_sz = hv(cs)
        af_pass, af_ic, af_sz = hv(af)
        b_pass = b["holdout"]["n_pass"] if b else 0
        c_best_ic = min(c3_ic, cs_ic)
        speed = "asm" if af_ic < c_best_ic else ("C" if af_ic > c_best_ic else "tie")
        tallies["asm_speed"] += speed == "asm"
        tallies["c_speed"] += speed == "C"
        tallies["asm_small"] += af_sz < c3_sz
        tallies["b_correct"] += b_pass == b["holdout"]["n_total"] if b else 0
        tallies["c_correct"] += c3["holdout"]["n_pass"] == c3["holdout"]["n_total"]
        rows.append((k, c3_ic, cs_ic, af_ic, c_best_ic, speed,
                     c3_sz, af_sz, af_pass))

    print("| kernel | C -O3 | C -Os | asm final | perf winner | "
          "C -O3 size | asm size | asm holdout |")
    print("|---|--:|--:|--:|:--:|--:|--:|:--:|")
    for (k, c3, cs, af, _cb, sp, c3s, afs, ap) in rows:
        mark = {"asm": "**asm**", "C": "C", "tie": "tie"}[sp]
        print(f"| {k} | {c3} | {cs} | {af} | {mark} | {c3s} | {afs} | {ap} |")

    t = tallies
    print(f"\n- Dynamic-instruction winner: **asm {t['asm_speed']}/"
          f"{t['n']}**, C {t['c_speed']}/{t['n']}.")
    print(f"- asm final smaller than C -O3 .text: **{t['asm_small']}/{t['n']}**.")
    print(f"- one-shot asm holdout-correct: **{t['b_correct']}/{t['n']}**; "
          f"C holdout-correct: **{t['c_correct']}/{t['n']}**.")


if __name__ == "__main__":
    main()
