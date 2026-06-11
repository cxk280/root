#!/usr/bin/env python3
"""(Re)generate public + holdout test vectors for every kernel.

The reference implementations below are the experiment's oracles. They are
never shown to the candidate generator — candidates are written from the
spec.md files alone (HYPOTHESES.md protocol).

Deterministic: fixed seed, so vectors are reproducible and diffable.
"""

import base64
import binascii
import json
import math
import random
from pathlib import Path

R = random.Random(20260611)
HERE = Path(__file__).resolve().parent
M64 = (1 << 64) - 1


def vec(args=None, data: bytes = None, rax: int = None, out: bytes = None):
    v = {"args": args or []}
    if data is not None:
        v["in"] = data.hex()
    v["expect"] = {}
    if rax is not None:
        v["expect"]["rax"] = rax & M64
    if out is not None:
        v["expect"]["out"] = out.hex()
    return v


# --- reference implementations (oracles) ------------------------------------

def ref_rle(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        j = i
        while j < len(data) and data[j] == data[i] and j - i < 255:
            j += 1
        out += bytes((j - i, data[i]))
        i = j
    return bytes(out)


def ref_utf8(data: bytes) -> int:
    try:
        data.decode("utf-8", "strict")
        return 1
    except UnicodeDecodeError:
        return 0


# --- per-kernel vector builders ----------------------------------------------

def g_popcount():
    fixed = [0, 1, M64, 0xAAAAAAAAAAAAAAAA, 1 << 63, 0x8000000000000001]
    rand = [R.getrandbits(64) for _ in range(16)]
    mk = lambda x: vec(args=[x], rax=bin(x).count("1"))
    xs = fixed + rand
    return [mk(x) for x in xs[:10]], [mk(x) for x in xs[10:]]


def g_clamp():
    cases = [(5, 0, 10), (-5, 0, 10), (15, 0, 10), (0, 0, 0), (-1, -1, -1),
             (-(1 << 63), -100, 100), ((1 << 63) - 1, -100, 100),
             (7, 7, 7), (-50, -100, -10), (3, -(1 << 63), (1 << 63) - 1)]
    for _ in range(12):
        lo = R.randint(-(1 << 62), 1 << 62)
        hi = lo + R.randint(0, 1 << 62)
        cases.append((R.randint(-(1 << 63), (1 << 63) - 1), lo, hi))
    mk = lambda v, lo, hi: vec(args=[v & M64, lo & M64, hi & M64],
                               rax=max(lo, min(v, hi)))
    return [mk(*c) for c in cases[:10]], [mk(*c) for c in cases[10:]]


def g_bitrev64():
    xs = [0, 1, M64, 1 << 63, 0x0123456789ABCDEF, 3] + \
         [R.getrandbits(64) for _ in range(16)]
    mk = lambda x: vec(args=[x], rax=int(f"{x:064b}"[::-1], 2))
    return [mk(x) for x in xs[:10]], [mk(x) for x in xs[10:]]


def g_crc32():
    datas = [b"", b"a", b"123456789", b"\x00" * 64, bytes(range(256)),
             R.randbytes(1), R.randbytes(31), R.randbytes(255),
             R.randbytes(1024), R.randbytes(2048)] + \
            [R.randbytes(R.randint(2, 1500)) for _ in range(10)]
    mk = lambda d: vec(args=["IN", len(d)], data=d, rax=binascii.crc32(d))
    return [mk(d) for d in datas[:10]], [mk(d) for d in datas[10:]]


def g_utf8_validate():
    cases = [b"", b"hello", "héllo wörld".encode(), "日本語テキスト".encode(),
             "👍🐍🚀".encode(), b"\x80", b"\xC0\x80", b"\xED\xA0\x80",
             b"\xF4\x90\x80\x80", "ok".encode() + b"\xE2\x82",  # truncated €
             b"\xC2\xA2", b"\xE2\x82\xAC", b"\xF0\x90\x8D\x88",
             b"\xFF\xFE", b"a\xC3", b"\xF8\x88\x80\x80\x80",
             "𝄞 music".encode(), b"\xC1\xBF", b"\xE0\x80\xAF",
             ("mixed: " + "Ω≈ç√∫".replace(" ", "")).encode(),
             R.randbytes(64), "long valid ✓ " .encode() * 50]
    mk = lambda d: vec(args=["IN", len(d)], data=d, rax=ref_utf8(d))
    return [mk(d) for d in cases[:11]], [mk(d) for d in cases[11:]]


def g_sort16():
    def arr():
        return [R.getrandbits(64) for _ in range(16)]
    cases = [list(range(16)), list(range(15, -1, -1)), [7] * 16,
             [M64, 0] * 8, arr(), arr(), arr(), arr(),
             [R.getrandbits(8) for _ in range(16)], arr(),
             arr(), arr(), [0] + [M64] * 15, arr(), arr(), arr(), arr(),
             [R.getrandbits(16) for _ in range(16)], arr(), arr()]

    def mk(a):
        data = b"".join(x.to_bytes(8, "little") for x in a)
        out = b"".join(x.to_bytes(8, "little") for x in sorted(a))
        return vec(args=["IN", "OUT"], data=data, out=out)
    return [mk(a) for a in cases[:10]], [mk(a) for a in cases[10:]]


def g_memchr():
    cases = [(b"hello", ord("l")), (b"hello", ord("z")), (b"", 0),
             (b"\x00\x01\x02", 0), (b"abc", ord("c")),
             (b"x" * 1000 + b"y", ord("y")), (bytes(range(256)), 255),
             (b"aaa", ord("a")), (R.randbytes(512), 0x7F),
             (b"q" * 64, ord("q"))] + \
            [(R.randbytes(R.randint(1, 800)), R.randrange(256))
             for _ in range(10)]

    def mk(d, b):
        idx = d.find(bytes([b]))
        return vec(args=["IN", len(d), b], data=d,
                   rax=idx if idx >= 0 else M64)
    return [mk(*c) for c in cases[:10]], [mk(*c) for c in cases[10:]]


def g_isqrt():
    xs = [0, 1, 2, 3, 4, 15, 16, 17, M64, (1 << 32) - 1, 1 << 32,
          (1 << 32) ** 2 - 1] + [R.getrandbits(64) for _ in range(8)] + \
         [(R.getrandbits(32) ** 2 + d) & M64 for d in (-1, 0, 1) for _ in range(2)]
    mk = lambda x: vec(args=[x], rax=math.isqrt(x))
    return [mk(x) for x in xs[:11]], [mk(x) for x in xs[11:]]


def g_rle_encode():
    cases = [b"", b"a", b"aaab", b"abc", b"a" * 255, b"a" * 256, b"a" * 600,
             b"\x00" * 10 + b"\x01", bytes(range(64)),
             b"aabbccddeeff" * 4] + \
            [R.choice([R.randbytes(R.randint(1, 400)),
                       bytes(R.choice(b"ab") for _ in range(R.randint(1, 700)))])
             for _ in range(10)]

    def mk(d):
        enc = ref_rle(d)
        return vec(args=["IN", len(d), "OUT"], data=d, rax=len(enc), out=enc)
    return [mk(d) for d in cases[:10]], [mk(d) for d in cases[10:]]


def g_base64_encode():
    cases = [b"", b"f", b"fo", b"foo", b"foob", b"fooba", b"foobar",
             bytes(range(256)), b"\x00\x00\x00", R.randbytes(57)] + \
            [R.randbytes(R.randint(1, 2000)) for _ in range(10)]

    def mk(d):
        enc = base64.b64encode(d)
        return vec(args=["IN", len(d), "OUT"], data=d, rax=len(enc), out=enc)
    return [mk(d) for d in cases[:10]], [mk(d) for d in cases[10:]]


KERNELS = {
    "popcount": g_popcount, "clamp": g_clamp, "bitrev64": g_bitrev64,
    "crc32": g_crc32, "utf8_validate": g_utf8_validate, "sort16": g_sort16,
    "memchr": g_memchr, "isqrt": g_isqrt, "rle_encode": g_rle_encode,
    "base64_encode": g_base64_encode,
}

if __name__ == "__main__":
    for name, gen in KERNELS.items():
        pub, hold = gen()
        d = HERE / name
        d.mkdir(exist_ok=True)
        (d / "tests_public.json").write_text(json.dumps(pub, indent=1))
        (d / "tests_holdout.json").write_text(json.dumps(hold, indent=1))
        print(f"{name}: {len(pub)} public, {len(hold)} holdout")
