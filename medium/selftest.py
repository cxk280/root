"""Self-tests for the solvent medium + assay: prove the instrument before
trusting any aliveness verdict.

    python -m medium.selftest
"""

import sys

from .assay import assay
from .build import build_organism
from .world import live


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
    ok = True
    for name, passed, detail in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {name}"
              + ("" if passed else f"   -> {detail}"))
        ok &= passed
    print(f"\n{'ALL MEDIUM SELF-TESTS PASS' if ok else 'MEDIUM SELF-TESTS FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
