"""Minimal ctypes binding to the Homebrew-installed libunicorn.

We deliberately avoid the PyPI bindings (unavailable in this environment) and
bind only the handful of C calls the rig needs. Enum constants are parsed from
the installed unicorn headers rather than hard-coded, so the shim tracks the
library version it actually loads.
"""

import ctypes
import ctypes.util
import re
from pathlib import Path

_SEARCH_PREFIXES = [
    Path("/usr/local/opt/unicorn"),
    Path("/opt/homebrew/opt/unicorn"),
    Path("/usr/local"),
    Path("/usr"),
]


def _find(kind: str) -> Path:
    for p in _SEARCH_PREFIXES:
        if kind == "lib":
            for name in ("libunicorn.dylib", "libunicorn.2.dylib", "libunicorn.so"):
                c = p / "lib" / name
                if c.exists():
                    return c
        else:
            c = p / "include" / "unicorn"
            if (c / "unicorn.h").exists():
                return c
    raise RuntimeError(
        f"libunicorn {kind} not found; install with `brew install unicorn`")


def _parse_enums(header_text: str, into: dict) -> None:
    """Extract NAME = value pairs from C enum bodies (handles `1 << n`, hex,
    references to earlier names, and plain auto-increment)."""
    text = re.sub(r"//[^\n]*", "", header_text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    for body in re.findall(r"enum\s+\w*\s*\{(.*?)\}", text, flags=re.S):
        prev = -1
        for entry in body.split(","):
            entry = entry.strip()
            if not entry:
                continue
            if "=" in entry:
                name, expr = (s.strip() for s in entry.split("=", 1))
                expr = re.sub(r"\b([A-Z][A-Z0-9_]*)\b",
                              lambda m: str(into.get(m.group(1), m.group(1))), expr)
                if not re.fullmatch(r"[0-9a-fxA-FX+|<>()\s]+", expr):
                    continue  # expression we can't evaluate; skip (unused by us)
                try:
                    val = eval(expr, {"__builtins__": {}})  # sanitized above
                except Exception:
                    continue
            else:
                name, val = entry, prev + 1
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                into[name] = val
                prev = val if isinstance(val, int) else prev


_inc = _find("include")
CONST: dict = {}
for _h in ("unicorn.h", "x86.h"):
    _parse_enums((_inc / _h).read_text(errors="replace"), CONST)

for _needed in ("UC_ARCH_X86", "UC_MODE_64", "UC_PROT_READ", "UC_PROT_WRITE",
                "UC_PROT_EXEC", "UC_HOOK_CODE", "UC_HOOK_MEM_WRITE",
                "UC_HOOK_MEM_READ", "UC_ERR_OK", "UC_X86_REG_RAX",
                "UC_X86_REG_RDI", "UC_X86_REG_RSP", "UC_X86_REG_RIP"):
    if _needed not in CONST:
        raise RuntimeError(f"failed to parse {_needed} from unicorn headers")

_lib = ctypes.CDLL(str(_find("lib")))
_lib.uc_open.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)]
_lib.uc_strerror.restype = ctypes.c_char_p
_lib.uc_strerror.argtypes = [ctypes.c_int]
_lib.uc_mem_map.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_size_t, ctypes.c_uint32]
_lib.uc_mem_write.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_char_p, ctypes.c_size_t]
_lib.uc_mem_read.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_char_p, ctypes.c_size_t]
_lib.uc_reg_write.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
_lib.uc_reg_read.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
_lib.uc_emu_start.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_uint64,
                              ctypes.c_uint64, ctypes.c_size_t]
_lib.uc_emu_stop.argtypes = [ctypes.c_void_p]
_lib.uc_close.argtypes = [ctypes.c_void_p]

_CODE_CB = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_uint64,
                            ctypes.c_uint32, ctypes.c_void_p)
# uc_mem_hook callback: (uc, type, address, size, value, user_data)
_MEM_CB = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int,
                           ctypes.c_uint64, ctypes.c_int, ctypes.c_int64,
                           ctypes.c_void_p)
# uc_hook_add is variadic; both prototypes below cover the forms we use.
_lib.uc_hook_add.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t),
                             ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
                             ctypes.c_uint64, ctypes.c_uint64]


class UcError(Exception):
    def __init__(self, errno: int):
        self.errno = errno
        super().__init__(_lib.uc_strerror(errno).decode())


def _check(err: int) -> None:
    if err != CONST["UC_ERR_OK"]:
        raise UcError(err)


class Uc:
    """The slice of the Unicorn API the rig uses."""

    def __init__(self):
        self._uc = ctypes.c_void_p()
        _check(_lib.uc_open(CONST["UC_ARCH_X86"], CONST["UC_MODE_64"],
                            ctypes.byref(self._uc)))
        self._cbs = []  # keep callback objects alive for the engine's lifetime

    def mem_map(self, addr: int, size: int, perms: int) -> None:
        _check(_lib.uc_mem_map(self._uc, addr, size, perms))

    def mem_write(self, addr: int, data: bytes) -> None:
        _check(_lib.uc_mem_write(self._uc, addr, data, len(data)))

    def mem_read(self, addr: int, size: int) -> bytes:
        buf = ctypes.create_string_buffer(size)
        _check(_lib.uc_mem_read(self._uc, addr, buf, size))
        return buf.raw

    def reg_write(self, regid: int, value: int) -> None:
        v = ctypes.c_uint64(value & 0xFFFF_FFFF_FFFF_FFFF)
        _check(_lib.uc_reg_write(self._uc, regid, ctypes.byref(v)))

    def reg_read(self, regid: int) -> int:
        v = ctypes.c_uint64()
        _check(_lib.uc_reg_read(self._uc, regid, ctypes.byref(v)))
        return v.value

    def hook_code(self, fn) -> None:
        """fn(addr, size) is invoked for every executed instruction."""
        cb = _CODE_CB(lambda _uc, addr, size, _ud: fn(addr, size))
        self._cbs.append(cb)
        hh = ctypes.c_size_t()
        _check(_lib.uc_hook_add(self._uc, ctypes.byref(hh), CONST["UC_HOOK_CODE"],
                                cb, None, 1, 0))

    def hook_mem_write(self, fn) -> None:
        """fn(addr, size, value) for every memory write (the freshness signal)."""
        cb = _MEM_CB(lambda _uc, _t, addr, size, value, _ud: fn(addr, size, value))
        self._cbs.append(cb)
        hh = ctypes.c_size_t()
        _check(_lib.uc_hook_add(self._uc, ctypes.byref(hh),
                                CONST["UC_HOOK_MEM_WRITE"], cb, None, 1, 0))

    def hook_mem_read(self, fn) -> None:
        """fn(addr, size) for every memory read (boundary-read provenance)."""
        cb = _MEM_CB(lambda _uc, _t, addr, size, _value, _ud: fn(addr, size))
        self._cbs.append(cb)
        hh = ctypes.c_size_t()
        _check(_lib.uc_hook_add(self._uc, ctypes.byref(hh),
                                CONST["UC_HOOK_MEM_READ"], cb, None, 1, 0))

    def emu_start(self, begin: int, until: int, timeout_us: int, count: int) -> None:
        _check(_lib.uc_emu_start(self._uc, begin, until, timeout_us, count))

    def emu_stop(self) -> None:
        _check(_lib.uc_emu_stop(self._uc))

    def close(self) -> None:
        if self._uc:
            _lib.uc_close(self._uc)
            self._uc = ctypes.c_void_p()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


def reg(name: str) -> int:
    return CONST[f"UC_X86_REG_{name.upper()}"]
