#!/usr/bin/env python3
"""Rung 3 — the layered viability envelope. One organism under two pressures on
one budget: self-production (solvent) and foraging (starvation), coupled so that
low fuel shrinks the repair budget. Sweeps the self-production budget T and the
nutrient drift v; records the outcome (live / dissolved / starved) to
results/protocell/layered.json. Emulation runs in isolated workers (control C2).

    .venv/bin/python scripts/layered.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness import config                       # noqa: E402
from harness.isolation import isolated_call      # noqa: E402
from medium.build import build_organism          # noqa: E402

OUT = config.REPO_ROOT / "results" / "protocell"
TS = [700, 1000, 2000, 4000]
VS = [0.3, 0.6, 1.0, 1.4, 1.8]
SEEDS = 4


def _cell(code, T, v):
    """Run SEEDS trials in a worker; classify the (T,v) cell."""
    outs = isolated_call("scripts.layered", "_trials", code, T, v, SEEDS)
    nsurv = sum(o[0] for o in outs)
    if nsurv >= 3:
        verdict = "live"
    else:
        modes = [o[1] for o in outs if not o[0]]
        verdict = "starved" if modes.count("starved") >= modes.count("dissolved") \
            else "dissolved"
    return {"survived": nsurv, "of": SEEDS, "verdict": verdict}


def _trials(code, T, v, seeds):
    """(survived, cause) per seed — module-level for the isolation worker."""
    from medium.world import live_layered
    res = []
    for s in range(seeds):
        r = live_layered(code, T=T, footprint=256, lifetime=200, food_speed=v, seed=s)
        res.append((r.survived, r.cause))
    return res


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    code = build_organism("protocell3")
    grid = {T: {v: _cell(code, T, v) for v in VS} for T in TS}
    (OUT / "layered.json").write_text(json.dumps(
        {"Ts": TS, "Vs": VS, "seeds": SEEDS, "grid": grid}, indent=1, default=str))
    print("Layered viability envelope (T budget × v drift):")
    print("        v=" + "  ".join(f"{v:>4}" for v in VS))
    for T in TS:
        row = "  ".join(f"{grid[T][v]['verdict'][:4]:>4}" for v in VS)
        print(f"  T={T:5d} {row}")
    print(f"\nwrote {OUT/'layered.json'}")


if __name__ == "__main__":
    main()
