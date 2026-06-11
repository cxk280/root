"""Minimal ELF64 relocatable-object loader.

clang -target x86_64-elf -c gives us a .o; this module places its .text at
CODE_BASE and its read-only data at RODATA_BASE, applies the small set of
relocation types such objects need, and returns flat images ready for the
sandbox. Writable state (.data/.bss) is rejected by design: kernels are pure
functions (abi.md).
"""

import struct
from dataclasses import dataclass

from . import config

SHT_PROGBITS, SHT_SYMTAB, SHT_STRTAB, SHT_RELA, SHT_NOBITS = 1, 2, 3, 4, 8
SHF_WRITE, SHF_ALLOC, SHF_EXECINSTR = 0x1, 0x2, 0x4
SHN_UNDEF, SHN_ABS = 0, 0xFFF1
R_X86_64_64, R_X86_64_PC32, R_X86_64_PLT32 = 1, 2, 4
R_X86_64_32, R_X86_64_32S = 10, 11


class ElfError(Exception):
    pass


@dataclass
class LoadedObject:
    code: bytes          # image for CODE_BASE
    rodata: bytes        # image for RODATA_BASE (possibly empty)
    entry: int           # absolute address of the `kernel` symbol


def _sections(data: bytes):
    if data[:4] != b"\x7fELF" or data[4] != 2:
        raise ElfError("not a 64-bit ELF object")
    e_shoff, = struct.unpack_from("<Q", data, 0x28)
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 0x3A)
    raw = [struct.unpack_from("<IIQQQQIIQQ", data, e_shoff + i * e_shentsize)
           for i in range(e_shnum)]
    shstr = data[raw[e_shstrndx][4]: raw[e_shstrndx][4] + raw[e_shstrndx][5]]

    def name(off):
        end = shstr.index(b"\0", off)
        return shstr[off:end].decode()

    return [dict(name=name(s[0]), type=s[1], flags=s[2], offset=s[4], size=s[5],
                 link=s[6], info=s[7], align=max(s[8], 1), entsize=s[9])
            for s in raw]


def load(data: bytes) -> LoadedObject:
    secs = _sections(data)

    # Decide placement for every SHF_ALLOC section.
    addr_of, images = {}, {}
    ro_cursor = config.RODATA_BASE
    text_idx = None
    for i, s in enumerate(secs):
        if not s["flags"] & SHF_ALLOC:
            continue
        if s["type"] == SHT_NOBITS or s["flags"] & SHF_WRITE:
            if s["size"]:
                raise ElfError(f"writable section {s['name']} not allowed: "
                               "kernels must be pure functions (abi.md)")
            continue
        img = bytearray(data[s["offset"]: s["offset"] + s["size"]])
        if s["flags"] & SHF_EXECINSTR:
            if text_idx is not None:
                raise ElfError("multiple executable sections; compile without "
                               "-ffunction-sections")
            text_idx = i
            addr_of[i] = config.CODE_BASE
        else:
            ro_cursor = (ro_cursor + s["align"] - 1) & ~(s["align"] - 1)
            addr_of[i] = ro_cursor
            ro_cursor += s["size"]
        images[i] = img
    if text_idx is None:
        raise ElfError("no executable section")
    if len(images[text_idx]) > config.CODE_SIZE:
        raise ElfError(".text exceeds CODE region")
    if ro_cursor - config.RODATA_BASE > config.RODATA_SIZE:
        raise ElfError("read-only data exceeds RODATA region")

    # Symbol table.
    symtab = next((s for s in secs if s["type"] == SHT_SYMTAB), None)
    syms = []
    if symtab:
        strtab = secs[symtab["link"]]
        names = data[strtab["offset"]: strtab["offset"] + strtab["size"]]
        for off in range(symtab["offset"], symtab["offset"] + symtab["size"], 24):
            n, info, _o, shndx, value, _sz = struct.unpack_from("<IBBHQQ", data, off)
            end = names.index(b"\0", n)
            syms.append(dict(name=names[n:end].decode(), shndx=shndx, value=value))

    def sym_addr(idx):
        s = syms[idx]
        if s["shndx"] == SHN_ABS:
            return s["value"]
        if s["shndx"] == SHN_UNDEF:
            raise ElfError(f"undefined symbol {s['name']!r} — kernels may not "
                           "call external functions (memcpy/memset included)")
        if s["shndx"] not in addr_of:
            raise ElfError(f"symbol {s['name']!r} in unloadable section")
        return addr_of[s["shndx"]] + s["value"]

    # Relocations, applied to the in-memory images.
    for s in secs:
        if s["type"] != SHT_RELA or s["info"] not in images:
            continue
        img, base = images[s["info"]], addr_of[s["info"]]
        for off in range(s["offset"], s["offset"] + s["size"], 24):
            r_off, r_info, r_add = struct.unpack_from("<QQq", data, off)
            val, rtype = sym_addr(r_info >> 32), r_info & 0xFFFFFFFF
            place = base + r_off
            if rtype == R_X86_64_64:
                struct.pack_into("<Q", img, r_off, (val + r_add) & (2**64 - 1))
            elif rtype in (R_X86_64_PC32, R_X86_64_PLT32):
                struct.pack_into("<i", img, r_off, val + r_add - place)
            elif rtype in (R_X86_64_32, R_X86_64_32S):
                struct.pack_into("<I", img, r_off, (val + r_add) & 0xFFFFFFFF)
            else:
                raise ElfError(f"unsupported relocation type {rtype}")

    entry = next((sym_addr(i) for i, s in enumerate(syms)
                  if s["name"] == config.ENTRY_SYMBOL), None)
    if entry is None:
        raise ElfError(f"no global symbol {config.ENTRY_SYMBOL!r}")

    rodata = bytearray(ro_cursor - config.RODATA_BASE)
    for i, img in images.items():
        if i != text_idx:
            o = addr_of[i] - config.RODATA_BASE
            rodata[o:o + len(img)] = img
    return LoadedObject(code=bytes(images[text_idx]), rodata=bytes(rodata),
                        entry=entry)
