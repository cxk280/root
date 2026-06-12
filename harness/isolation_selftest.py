"""Self-test for the C2 isolation worker: prove a worker that misbehaves is
CONTAINED — the orchestrator survives and observes a ContainmentError.

    python -m harness.isolation_selftest
"""

import sys

from .isolation import ContainmentError, isolated_call

_MOD = "harness.isolation_selftest"


def _probe_double(x):
    return x * 2


def _probe_raise():
    raise ValueError("boom")


def _probe_hang():
    while True:
        pass


def _probe_crash():
    import os
    os.abort()          # hard crash (SIGABRT) — simulates an emulator segfault


def _probe_cpu_hog():
    x = 0
    while True:
        x += 1


def _expect_contained(name, fn_args, checks, **call_kw):
    try:
        isolated_call(*fn_args, **call_kw)
        checks.append((name, False, "worker was NOT contained"))
    except ContainmentError as e:
        checks.append((name, True, str(e)[:60]))


def main() -> int:
    checks = []

    r = isolated_call(_MOD, "_probe_double", 21)
    checks.append(("normal call runs in a worker and returns", r == 42, r))

    _expect_contained("worker exception -> ContainmentError",
                      (_MOD, "_probe_raise"), checks)
    _expect_contained("worker hang -> wall-clock ContainmentError",
                      (_MOD, "_probe_hang"), checks, timeout=2)
    _expect_contained("worker hard crash (abort) is contained",
                      (_MOD, "_probe_crash"), checks)
    _expect_contained("RLIMIT_CPU kills a compute runaway",
                      (_MOD, "_probe_cpu_hog"), checks,
                      limits={"cpu_seconds": 1}, timeout=30)

    # The decisive property: after all that worker death, the orchestrator is
    # still alive and able to run more work.
    r = isolated_call(_MOD, "_probe_double", 50)
    checks.append(("orchestrator survives worker death, keeps working",
                   r == 100, r))

    ok = True
    for name, passed, detail in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {name}"
              + ("" if passed else f"   -> {detail}"))
        ok &= passed
    print(f"\n{'ALL ISOLATION CHECKS PASS' if ok else 'ISOLATION CHECKS FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
