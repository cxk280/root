"""Fixed constants of the rig. The authoritative prose contract is abi.md."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Memory map (see abi.md)
CODE_BASE = 0x0001_0000
CODE_SIZE = 0x1_0000
RODATA_BASE = 0x0004_0000
RODATA_SIZE = 0x1_0000
IN_BASE = 0x0020_0000
IN_SIZE = 0x1_0000
OUT_BASE = 0x0030_0000
OUT_SIZE = 0x1_0000
STACK_BASE = 0x7F00_0000
STACK_SIZE = 0x10_0000
STACK_TOP = 0x7F0F_F000
HALT_ADDR = 0x00DE_A000

FUEL = 2_000_000          # max dynamic instructions per test vector
WALL_TIMEOUT_US = 20_000_000  # emulator wall-clock backstop

CLANG = "clang"
ELF_TARGET = "x86_64-elf"
CFLAGS_COMMON = [
    "-ffreestanding", "-fno-builtin", "-fno-stack-protector",
    "-fno-asynchronous-unwind-tables",
]

ENTRY_SYMBOL = "kernel"
