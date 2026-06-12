#!/usr/bin/env python3
"""Run the rung-1 (solvent) aliveness assay for every organism and record it.

    .venv/bin/python scripts/life.py

All organism emulation runs inside an ISOLATED worker process (harness.isolation,
control C2) — the orchestrator only builds organisms (host clang) and writes
results. Writes results/protocell/assay.json and prints the summary table.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness import config, provenance           # noqa: E402
from harness.isolation import isolated_call      # noqa: E402
from medium.build import build_organism          # noqa: E402

ORGS = ["rock", "blind", "protocell0"]
OUT = config.REPO_ROOT / "results" / "protocell"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = {}
    print(f"{'organism':12s} {'alive':6s} {'closure':8s} {'T*':>5s} "
          f"{'turnover':>9s} {'integ':>6s}")
    for name in ORGS:
        code = build_organism(name)                       # host toolchain
        rec = isolated_call("medium.assay", "assay_full", name, code)  # contained
        records[name] = rec
        print(f"{name:12s} {str(rec['survives']):6s} {rec['closure_score']}/6      "
              f"{str(rec['t_star_fine']):>5s} {rec['mean_turnover']:9.0f} "
              f"{rec['mean_integrity']:6.2f}")
    (OUT / "assay.json").write_text(json.dumps(records, indent=1))
    provenance.write()                       # stamp the toolchain (C5)
    print(f"\nwrote {OUT/'assay.json'}")
    return records


if __name__ == "__main__":
    main()
