#!/usr/bin/env python3
"""Run inside the locked-down container (C4): prove BOTH that the science still
works AND that the container's hard walls hold — no network, read-only root,
writable scratch only. Exits nonzero on any failure.
"""

import os
import socket
import subprocess
import sys

MODULES = [
    "harness.selftest",          # rig: build + emulate + self-modifying code
    "harness.containment",       # C1: sandbox walls hold
    "harness.isolation_selftest",  # C2: worker contains failures
    "medium.selftest",           # the aliveness assay + ranking invariants
]


def _run_module(m: str) -> bool:
    r = subprocess.run([sys.executable, "-m", m], capture_output=True, text=True)
    ok = r.returncode == 0
    print(f"[{'PASS' if ok else 'FAIL'}] {m}")
    if not ok:
        sys.stdout.write(r.stdout[-1500:] + r.stderr[-1500:])
    return ok


def _net_blocked() -> bool:
    try:
        s = socket.socket()
        s.settimeout(3)
        s.connect(("1.1.1.1", 53))
        s.close()
        return False                      # connected -> NOT contained
    except OSError:
        return True                       # blocked -> contained


def _root_readonly() -> bool:
    try:
        with open("/work/__rw_probe", "w") as f:
            f.write("x")
        os.remove("/work/__rw_probe")
        return False                      # writable -> NOT contained
    except OSError:
        return True


def _scratch_writable() -> bool:
    p = os.path.join(os.environ.get("TMPDIR", "/tmp"), "__scratch_probe")
    try:
        with open(p, "w") as f:
            f.write("x")
        os.remove(p)
        return True
    except OSError:
        return False


def main() -> int:
    print("== science + safety self-tests ==")
    ok = all(_run_module(m) for m in MODULES)

    print("\n== container hard walls ==")
    walls = [
        ("network egress is blocked (--network none)", _net_blocked()),
        ("root filesystem is read-only", _root_readonly()),
        ("scratch space is writable (ephemeral tmpfs)", _scratch_writable()),
    ]
    for name, passed in walls:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
        ok &= passed

    print(f"\n{'CONTAINER FULLY VERIFIED' if ok else 'CONTAINER VERIFICATION FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
