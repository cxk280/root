"""Source -> blob. Both C and assembly go through clang targeting bare-metal
ELF, then through the elfobj loader, so every candidate is measured through
the identical pipeline."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from . import config, elfobj


class BuildError(Exception):
    pass


def _compile(src: Path, extra_flags: list[str]) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        obj = Path(td) / "out.o"
        cmd = [config.CLANG, "-target", config.ELF_TARGET, "-c",
               str(src), "-o", str(obj), *extra_flags]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise BuildError(f"clang failed:\n{r.stderr}")
        return obj.read_bytes()


def build(src: Path, out_dir: Path, opt: str = "-O3") -> Path:
    """Build a .c or .s source into a blob directory (code.bin, rodata.bin,
    meta.json) and return the directory path."""
    src = Path(src)
    if src.suffix == ".c":
        flags = [opt, *config.CFLAGS_COMMON]
    elif src.suffix == ".s" or src.suffix == ".S":
        flags = []
    else:
        raise BuildError(f"unknown source type {src.suffix}")
    loaded = elfobj.load(_compile(src, flags))

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "code.bin").write_bytes(loaded.code)
    (out_dir / "rodata.bin").write_bytes(loaded.rodata)
    (out_dir / "meta.json").write_text(json.dumps({
        "entry": loaded.entry,
        "code_size": len(loaded.code),
        "rodata_size": len(loaded.rodata),
        "source": src.name,
        "flags": flags,
        "sha256": hashlib.sha256(loaded.code).hexdigest(),
    }, indent=1))
    return out_dir


def load_blob(blob_dir: Path) -> elfobj.LoadedObject:
    """Load a built blob directory, or a bare .bin (raw code, entry at 0)."""
    p = Path(blob_dir)
    if p.is_file() and p.suffix == ".bin":
        return elfobj.LoadedObject(code=p.read_bytes(), rodata=b"",
                                   entry=config.CODE_BASE)
    meta = json.loads((p / "meta.json").read_text())
    return elfobj.LoadedObject(code=(p / "code.bin").read_bytes(),
                               rodata=(p / "rodata.bin").read_bytes(),
                               entry=meta["entry"])
