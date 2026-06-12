"""Execute a blob against one test vector inside Unicorn, per abi.md.

This is the only module that runs candidate machine code, and it only ever
does so inside the emulator. Keep it that way: that invariant is what makes
evolved/self-modifying code safe to experiment with later.
"""

from dataclasses import dataclass, field

from . import config
from .elfobj import LoadedObject
from .uc import CONST, Uc, UcError, reg

ARG_REGS = ("RDI", "RSI", "RDX", "RCX")


@dataclass
class RunResult:
    status: str            # ok | fuel_exhausted | timeout | fault:<detail>
    rax: int = 0
    out: bytes = b""
    icount: int = 0
    fault: str = field(default="")

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def _resolve_arg(a):
    if a == "IN":
        return config.IN_BASE
    if a == "OUT":
        return config.OUT_BASE
    return int(a)


def run_vector(blob: LoadedObject, args: list, in_bytes: bytes = b"",
               out_read: int = 0, fuel: int = config.FUEL) -> RunResult:
    """One fresh emulator per vector: no state leaks between runs."""
    R, W, X = CONST["UC_PROT_READ"], CONST["UC_PROT_WRITE"], CONST["UC_PROT_EXEC"]
    mu = Uc()
    try:
        mu.mem_map(config.CODE_BASE, config.CODE_SIZE, R | W | X)  # RWX by design
        mu.mem_map(config.RODATA_BASE, config.RODATA_SIZE, R)
        mu.mem_map(config.IN_BASE, config.IN_SIZE, R | W)
        mu.mem_map(config.OUT_BASE, config.OUT_SIZE, R | W)
        mu.mem_map(config.STACK_BASE, config.STACK_SIZE, R | W)
        mu.mem_map(config.HALT_ADDR & ~0xFFF, 0x1000, R | X)

        mu.mem_write(config.CODE_BASE, blob.code)
        if blob.rodata:
            mu.mem_write(config.RODATA_BASE, blob.rodata)
        if in_bytes:
            if len(in_bytes) > config.IN_SIZE:
                raise ValueError("input exceeds IN region")
            mu.mem_write(config.IN_BASE, in_bytes)

        for regname, val in zip(ARG_REGS, args):
            mu.reg_write(reg(regname), _resolve_arg(val))
        mu.reg_write(reg("RSP"), config.STACK_TOP)
        mu.mem_write(config.STACK_TOP, config.HALT_ADDR.to_bytes(8, "little"))

        counter = [0]

        def _count(_addr, _size):
            counter[0] += 1

        mu.hook_code(_count)

        try:
            mu.emu_start(blob.entry, config.HALT_ADDR,
                         config.WALL_TIMEOUT_US, fuel)
        except UcError as e:
            return RunResult(status=f"fault:{e}", icount=counter[0], fault=str(e))

        if mu.violation:                      # trapped a privileged instruction
            return RunResult(status=f"fault:forbidden_{mu.violation}",
                             icount=counter[0], fault=mu.violation)

        icount = counter[0]
        if mu.reg_read(reg("RIP")) != config.HALT_ADDR:
            status = "fuel_exhausted" if icount >= fuel else "timeout"
            return RunResult(status=status, icount=icount)

        out = mu.mem_read(config.OUT_BASE, out_read) if out_read else b""
        return RunResult(status="ok", rax=mu.reg_read(reg("RAX")),
                         out=out, icount=icount)
    finally:
        mu.close()
