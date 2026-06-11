#!/usr/bin/env python3
"""Run the rung-1 (solvent) aliveness assay for every organism and record it.

    .venv/bin/python scripts/life.py

Writes results/protocell/assay.json (raw) and prints the summary table. The
fine phase-transition sweep locates T* (metabolic-rate threshold) per organism.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness import config                       # noqa: E402
from medium.build import build_organism          # noqa: E402
from medium.assay import assay                   # noqa: E402
from medium.world import live                    # noqa: E402

ORGS = ["rock", "blind", "protocell0"]
OUT = config.REPO_ROOT / "results" / "protocell"
FINE = list(range(100, 1001, 50))


def fine_t_star(code, lifetime=150):
    t_star, table = None, {}
    for T in FINE:
        L = live(code, T=T, lifetime=lifetime)
        table[T] = {"survived": L.survived, "lifespan": L.lifespan,
                    "death": L.cause}
        if L.survived and t_star is None:
            t_star = T
    return t_star, table


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = {}
    print(f"{'organism':12s} {'alive':6s} {'closure':8s} {'T*':>5s} "
          f"{'turnover':>9s} {'integ':>6s}")
    for name in ORGS:
        code = build_organism(name)
        A = assay(name, code, T_live=4000, lifetime=120)
        tstar, table = fine_t_star(code)
        records[name] = {
            "footprint": A.footprint, "survives": A.survives,
            "lifespan": A.lifespan, "closure_score": A.closure_score,
            "criteria": A.criteria, "evidence": A.evidence,
            "t_star_fine": tstar, "mean_turnover": A.mean_turnover,
            "mean_integrity": A.mean_integrity, "phase_fine": table,
        }
        print(f"{name:12s} {str(A.survives):6s} {A.closure_score}/6      "
              f"{str(tstar):>5s} {A.mean_turnover:9.0f} {A.mean_integrity:6.2f}")
    (OUT / "assay.json").write_text(json.dumps(records, indent=1))
    print(f"\nwrote {OUT/'assay.json'}")
    return records


if __name__ == "__main__":
    main()
