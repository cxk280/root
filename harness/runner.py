"""CLI: score one candidate blob against one kernel's test vectors.

    python -m harness.runner --kernel popcount \
        --candidate candidates/popcount/c_O3 --tests holdout

Prints a JSON report to stdout; exit code 0 iff every vector passed.
Vector schema (kernels/<name>/tests_*.json):
    {"args": [1, "IN", "OUT"], "in": "<hex>", "expect": {"rax": 3, "out": "<hex>"}}
"""

import argparse
import json
import sys
from pathlib import Path

from . import assemble, config
from .sandbox import run_vector


def load_vectors(kernel: str, which: str) -> list[dict]:
    kdir = config.REPO_ROOT / "kernels" / kernel
    names = ["tests_public.json", "tests_holdout.json"] if which == "all" \
        else [f"tests_{which}.json"]
    vecs = []
    for n in names:
        vecs += json.loads((kdir / n).read_text())
    return vecs


def score(blob, vectors: list[dict]) -> dict:
    total_icount, failures, n_pass = 0, [], 0
    for i, v in enumerate(vectors):
        expect = v.get("expect", {})
        out_hex = expect.get("out")
        res = run_vector(blob, v.get("args", []),
                         in_bytes=bytes.fromhex(v.get("in", "")),
                         out_read=len(out_hex) // 2 if out_hex else 0)
        good = res.ok
        if good and "rax" in expect:
            good = (res.rax & 0xFFFF_FFFF_FFFF_FFFF) == \
                   (expect["rax"] & 0xFFFF_FFFF_FFFF_FFFF)
        if good and out_hex is not None:
            good = res.out.hex() == out_hex
        total_icount += res.icount
        if good:
            n_pass += 1
        else:
            failures.append({
                "idx": i, "args": v.get("args", []),
                "in": v.get("in", "")[:128],
                "expect": expect,
                "got": {"status": res.status, "rax": res.rax,
                        "out": res.out.hex()},
                "icount": res.icount,
            })
    return {"n_pass": n_pass, "n_total": len(vectors),
            "all_pass": n_pass == len(vectors),
            "total_icount": total_icount, "failures": failures}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kernel", required=True)
    ap.add_argument("--candidate", required=True,
                    help="blob directory (or raw .bin) from harness.assemble")
    ap.add_argument("--tests", choices=["public", "holdout", "all"],
                    default="public")
    ap.add_argument("--max-failures", type=int, default=5,
                    help="cap failure detail in the report")
    args = ap.parse_args(argv)

    blob = assemble.load_blob(Path(args.candidate))
    report = score(blob, load_vectors(args.kernel, args.tests))
    report.update(kernel=args.kernel, candidate=str(args.candidate),
                  tests=args.tests, code_size=len(blob.code))
    report["failures"] = report["failures"][: args.max_failures]
    print(json.dumps(report, indent=1))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
