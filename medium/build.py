"""Compile an organism's .s into its birth image (flat bytes at ARENA_BASE).

If organisms/<name>/membrane.json declares `"replicate": N`, the assembled
single-body image is repeated N times to form the birth image — this is how a
redundant organism (e.g. protocell1's triple modular redundancy) gets N
byte-identical copies of itself at birth, at base, base+L, ... base+(N-1)L.
"""

import json
import tempfile
from pathlib import Path

from harness import assemble, config

ORGANISMS = config.REPO_ROOT / "organisms"


def build_organism(name: str) -> bytes:
    src = ORGANISMS / name / "organism.s"
    with tempfile.TemporaryDirectory() as td:
        blob_dir = assemble.build(src, Path(td) / "blob")
        body = assemble.load_blob(blob_dir).code
    decl_path = ORGANISMS / name / "membrane.json"
    replicate = 1
    if decl_path.exists():
        replicate = json.loads(decl_path.read_text()).get("replicate", 1)
    return body * replicate
