#!/usr/bin/env python3
"""Rung 2.7 — foraging / structural coupling. Records the foraging phase
transition (survival vs nutrient drift speed) for the chemotactic forager vs the
non-sensing sweep control. Emulation runs in an isolated worker (control C2).

    .venv/bin/python scripts/forage.py   ->  results/protocell/forage.json
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness import config                       # noqa: E402
from harness.isolation import isolated_call      # noqa: E402
from medium.build import build_organism          # noqa: E402

OUT = config.REPO_ROOT / "results" / "protocell"
SPEEDS = [0.0, 0.5, 0.8, 1.0, 1.2, 1.5, 2.0]
SEEDS = 12


def _sweep(name):
    code = build_organism(name)
    out = {}
    for sp in SPEEDS:
        runs = isolated_call("scripts.forage", "_runs", code, sp, SEEDS)
        survived = sum(r[0] for r in runs)
        track = sum(r[1] for r in runs) / len(runs)
        out[sp] = {"survived": survived, "of": SEEDS, "track_error": round(track, 2)}
    return out


def _runs(code, food_speed, seeds):
    """Run `seeds` foraging trials; return (survived, track_error) per trial.
    Module-level so the isolation worker can import it."""
    from medium.world import live_forage
    res = []
    for s in range(seeds):
        r = live_forage(code, T=10000, lifetime=300, food_speed=food_speed, seed=s)
        res.append((r.survived, r.track_error))
    return res


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = {"speeds": SPEEDS, "seeds": SEEDS,
            "chemotaxis": _sweep("forager0"), "sweep": _sweep("forager_sweep")}
    (OUT / "forage.json").write_text(json.dumps(data, indent=1))
    print(f"{'speed':>6} | chemotaxis | sweep | chemo track_err")
    for sp in SPEEDS:
        c, s = data["chemotaxis"][sp], data["sweep"][sp]
        print(f"{sp:6} |   {c['survived']:2d}/{SEEDS}    | {s['survived']:2d}/{SEEDS} "
              f"|  {c['track_error']}")
    print(f"\nwrote {OUT/'forage.json'}")


if __name__ == "__main__":
    main()
