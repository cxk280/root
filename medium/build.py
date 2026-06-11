"""Compile an organism's .s into its birth image (flat bytes at ARENA_BASE)."""

import tempfile
from pathlib import Path

from harness import assemble, config

ORGANISMS = config.REPO_ROOT / "organisms"


def build_organism(name: str) -> bytes:
    src = ORGANISMS / name / "organism.s"
    with tempfile.TemporaryDirectory() as td:
        blob_dir = assemble.build(src, Path(td) / "blob")
        return assemble.load_blob(blob_dir).code
