"""C5 — record the toolchain so every result is auditable and reproducible.

Pins the *exact* native libraries and compiler that produced a result by version
and content hash, plus the determinism controls in force. Stable by construction
(hashes/versions don't change between runs), so it adds no churn until the
toolchain actually changes. Written to results/provenance.json.
"""

import hashlib
import subprocess
from pathlib import Path

from . import config, uc


def _sha256(path: str) -> str:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
    except OSError:
        return "unavailable"


def _clang_version() -> str:
    try:
        out = subprocess.run([config.CLANG, "--version"], capture_output=True,
                             text=True).stdout.splitlines()
        return out[0].strip() if out else "unknown"
    except OSError:
        return "unavailable"


def toolchain() -> dict:
    libp = uc.lib_path()
    return {
        "unicorn_version": uc.version(),
        "unicorn_lib": libp,
        "unicorn_sha256_16": _sha256(libp),
        "clang_version": _clang_version(),
        "fuel_cap": config.FUEL,
        "wall_timeout_us": config.WALL_TIMEOUT_US,
        "determinism": {
            "solvent_medium": "deterministic",
            "bitrot_medium": "seeded PRNG (seed recorded per run)",
            "trapped_for_determinism": ["cpuid"],
            "residual_note": "rdtsc executes (emulated counter); not on any "
                             "result path, see SECURITY.md C6",
        },
    }


def write(out_dir: Path | None = None) -> Path:
    import json
    out = (out_dir or (config.REPO_ROOT / "results")) / "provenance.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(toolchain(), indent=1))
    return out


if __name__ == "__main__":
    print(write())
