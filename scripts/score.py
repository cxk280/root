#!/usr/bin/env python3
"""Build and score one candidate condition for one kernel; record the result.

    .venv/bin/python scripts/score.py --kernel popcount --condition c
    .venv/bin/python scripts/score.py --all-built   # rescore every built blob

Conditions: c (built at -O3 and -Os), asm_oneshot, asm_iter (latest round).
Writes results/runs/<kernel>__<tag>.json; build failures are recorded as
results too — a candidate that doesn't assemble has failed the experiment,
not the harness.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness import assemble, config  # noqa: E402
from harness.runner import load_vectors, score  # noqa: E402

RUNS = config.REPO_ROOT / "results" / "runs"


def record(kernel: str, tag: str, payload: dict) -> None:
    RUNS.mkdir(parents=True, exist_ok=True)
    payload = {"kernel": kernel, "tag": tag, **payload}
    (RUNS / f"{kernel}__{tag}.json").write_text(json.dumps(payload, indent=1))
    pub = payload.get("public", {})
    hold = payload.get("holdout", {})
    print(f"{kernel:16s} {tag:12s} "
          + (f"build FAILED" if "build_error" in payload else
             f"public {pub['n_pass']}/{pub['n_total']}  "
             f"holdout {hold['n_pass']}/{hold['n_total']}  "
             f"icount {hold['total_icount']:>8}  size {payload['code_size']}"))


def build_and_score(kernel: str, src: Path, tag: str, opt: str) -> None:
    blob_dir = config.REPO_ROOT / "candidates" / kernel / "blobs" / tag
    try:
        assemble.build(src, blob_dir, opt=opt)
    except Exception as e:
        record(kernel, tag, {"source": str(src), "build_error": str(e)})
        return
    blob = assemble.load_blob(blob_dir)
    record(kernel, tag, {
        "source": str(src), "code_size": len(blob.code),
        "public": score(blob, load_vectors(kernel, "public")),
        "holdout": score(blob, load_vectors(kernel, "holdout")),
    })


def latest_round(d: Path) -> Path:
    rounds = sorted(d.glob("round*.[cs]"),
                    key=lambda p: int("".join(filter(str.isdigit, p.stem))))
    if not rounds:
        raise FileNotFoundError(f"no rounds in {d}")
    return rounds[-1]


def run(kernel: str, condition: str) -> None:
    cdir = config.REPO_ROOT / "candidates" / kernel
    if condition == "c":
        src = latest_round(cdir / "c")
        build_and_score(kernel, src, "c_O3", "-O3")
        build_and_score(kernel, src, "c_Os", "-Os")
    else:
        src = latest_round(cdir / condition)
        tag = condition if condition == "asm_oneshot" else \
            f"asm_iter_r{''.join(filter(str.isdigit, src.stem))}"
        build_and_score(kernel, src, tag, "-O3")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--kernel")
    ap.add_argument("--condition",
                    choices=["c", "asm_oneshot", "asm_iter"])
    ap.add_argument("--all", action="store_true",
                    help="run c + asm_oneshot for every kernel")
    a = ap.parse_args()
    if a.all:
        from kernels.genvectors import KERNELS
        for k in KERNELS:
            for cond in ("c", "asm_oneshot"):
                run(k, cond)
    else:
        run(a.kernel, a.condition)
