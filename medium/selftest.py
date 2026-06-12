"""Self-tests for the solvent medium + assay: prove the instrument before
trusting any aliveness verdict.

    python -m medium.selftest
"""

import sys

from .assay import assay
from .build import build_organism
from .world import live, live_colony, live_forage


def main() -> int:
    rock = assay("rock", build_organism("rock"), T_live=4000, lifetime=60)
    blind = assay("blind", build_organism("blind"), T_live=4000, lifetime=120)
    cell = assay("protocell0", build_organism("protocell0"),
                 T_live=4000, lifetime=120)

    checks = [
        ("rock dies (decay has teeth)", not rock.survives, rock.lifespan),
        ("rock has no closure", rock.closure_score <= 1, rock.closure_score),
        ("blind lives", blind.survives, blind.lifespan),
        ("blind is low-closure (no genuine boundary)",
         blind.closure_score == 2, blind.closure_score),
        ("protocell0 lives", cell.survives, cell.lifespan),
        ("protocell0 is full-closure 6/6", cell.closure_score == 6,
         cell.closure_score),
        ("membrane is read", cell.evidence["membrane"]["read"], None),
        ("membrane is never executed (data, not code)",
         cell.evidence["membrane"]["not_executed"], None),
        ("membrane is re-laid each cycle (self-produced)",
         cell.evidence["membrane"]["rewritten"], None),
        ("corrupting the membrane VALUE kills",
         cell.evidence["membrane"]["corruption_kills"], None),
        ("closure ranking rock < blind < protocell0",
         rock.closure_score < blind.closure_score < cell.closure_score,
         (rock.closure_score, blind.closure_score, cell.closure_score)),
        ("protocell0 has a metabolic threshold T*", cell.t_star is not None,
         cell.t_star),
        ("protocell0 dies below threshold (T=200)",
         not live(build_organism("protocell0"), T=200, lifetime=80).survived,
         None),
        ("protocell0 holds integrity in steady state",
         cell.mean_integrity > 0.99, cell.mean_integrity),
        ("protocell0 metabolizes (turnover > 0)",
         cell.mean_turnover > 0, cell.mean_turnover),
        ("no external scaffold consulted (closure by construction)",
         cell.evidence["external_reads"] == 0, cell.evidence["external_reads"]),
    ]

    # Redundant error correction (Rung 2): a TMR organism is full-closure when the
    # assay ablates components across ALL copies, and survives bit-rot.
    tmr = assay("protocell2", build_organism("protocell2"), T_live=8000, lifetime=80)
    checks += [
        ("protocell2 (TMR) is full-closure 6/6 via all-copy ablation",
         tmr.closure_score == 6, tmr.closure_score),
        ("TMR membrane survives a single-copy hit but all-copy corruption kills",
         tmr.evidence["membrane"]["corruption_kills"], None),
    ]

    # Redundant EXECUTION (Rung 2.5): a colony of heads over a shared genome breaks
    # the single-PC SPOF — it survives a corruption rate that kills the single head.
    c2 = build_organism("protocell2")
    colony_clean = live_colony(c2, T=8000, footprint=480, heads=[0, 160],
                               lifetime=120, lam=0.0)
    single_dead = sum(live(c2, T=8000, lifetime=120, body_hint=480, decay="bitrot",
                           lam=0.16, seed=s).survived for s in range(8))
    colony_alive = sum(live_colony(c2, T=8000, footprint=480, heads=[0, 160],
                                   lifetime=120, lam=0.16, seed=s).survived
                       for s in range(8))
    checks += [
        ("colony of 2 heads survives with no decay (register contexts isolated)",
         colony_clean.survived, colony_clean.cause),
        ("redundant execution lifts the cap: colony outlives single head at lethal lambda",
         colony_alive > single_dead, (single_dead, colony_alive)),
    ]

    # Foraging / structural coupling (Rung 2.7): chemotaxis tracks a moving
    # nutrient and lives; non-sensing motion starves. There is a drift-speed
    # bandwidth v* below which the forager survives and above which it starves.
    f0, fsweep = build_organism("forager0"), build_organism("forager_sweep")
    chemo_slow = live_forage(f0, T=10000, lifetime=300, food_speed=0.8, seed=0)
    chemo_fast = sum(live_forage(f0, T=10000, lifetime=300, food_speed=2.0, seed=s).survived
                     for s in range(6))
    sweep_static = live_forage(fsweep, T=10000, lifetime=300, food_speed=0.0, seed=0)
    checks += [
        ("chemotaxis tracks a moving nutrient and lives (v < v*)",
         chemo_slow.survived and chemo_slow.track_error < 2.0,
         (chemo_slow.survived, round(chemo_slow.track_error, 1))),
        ("foraging has a bandwidth v*: chemotaxis starves when food outruns it",
         chemo_fast == 0, chemo_fast),
        ("non-sensing motion is not foraging: the sweep control starves",
         not sweep_static.survived and sweep_static.cause == "starved",
         (sweep_static.cause, sweep_static.harvests)),
    ]

    # Layered (Rung 3): one organism under both pressures on one budget. It lives
    # where it can afford both; dissolves when the budget can't self-produce;
    # starves when the nutrient outruns it.
    from .world import live_layered
    lay = lambda T, v: live_layered(build_organism("protocell3"), T=T, footprint=256,
                                    lifetime=180, food_speed=v, seed=1)
    moderate, lowT, highV = lay(4000, 0.4), lay(700, 0.4), lay(4000, 1.8)
    checks += [
        ("protocell3 lives layered (self-produce + forage on one budget)",
         moderate.survived and moderate.mean_integrity > 0.9, (moderate.survived,
         round(moderate.mean_integrity, 2))),
        ("layered: too small a budget -> dissolution (can't self-produce)",
         not lowT.survived and lowT.cause == "dissolved", lowT.cause),
        ("layered: nutrient outruns it -> starvation impairs repair -> death",
         not highV.survived and highV.cause == "starved", highV.cause),
    ]

    ok = True
    for name, passed, detail in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {name}"
              + ("" if passed else f"   -> {detail}"))
        ok &= passed
    print(f"\n{'ALL MEDIUM SELF-TESTS PASS' if ok else 'MEDIUM SELF-TESTS FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
