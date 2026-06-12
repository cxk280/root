"""C2 — run emulation in a sandboxed worker process.

The organism cannot reach the host (it has no syscalls; SECURITY.md), but the
*emulator* is a large C library descended from QEMU, and a hypothetical bug
triggered by crafted guest code could corrupt the host process. So we never run
emulation in the orchestrator process: `isolated_call` forks a disposable worker
that first clamps its own resources (no core dumps, bounded CPU time, bounded
address space on Linux, few file descriptors, no fork bombs), runs the work, and
returns the result over a pipe. A worker that dies, hangs, or blows its limits is
contained — the orchestrator observes a ContainmentError, not corruption.

Memory/network/filesystem isolation is only *best-effort* here (macOS does not
enforce RLIMIT_AS, and network/FS lockdown needs the container, C4). This layer's
guarantee is the process boundary + CPU/wall-clock bounds + crash containment;
the container is where memory and network become hard walls.
"""

import multiprocessing as mp
import resource

GiB = 1024 ** 3
MiB = 1024 ** 2

DEFAULT_LIMITS = {
    "cpu_seconds": 600,        # RLIMIT_CPU backstop against a hung emulator
    "memory_bytes": 2 * GiB,   # RLIMIT_AS — enforced on Linux/container
    "max_files": 64,           # RLIMIT_NOFILE
    "fsize_bytes": 256 * MiB,  # RLIMIT_FSIZE — bound accidental disk writes
}
DEFAULT_TIMEOUT = 600          # wall-clock backstop (s)


class ContainmentError(Exception):
    """The isolated worker died, hung, or exceeded its limits."""


def _set(limit, soft):
    try:
        hard = resource.getrlimit(limit)[1]
        cap = soft if hard == resource.RLIM_INFINITY else min(soft, hard)
        resource.setrlimit(limit, (cap, hard))
    except (ValueError, OSError):
        pass


def apply_limits(limits: dict) -> None:
    """Clamp the calling process's resources. Best-effort and platform-dependent;
    each limit is applied independently so an unsupported one is skipped."""
    _set(resource.RLIMIT_CORE, 0)                     # never dump core
    _set(resource.RLIMIT_CPU, limits["cpu_seconds"])
    _set(resource.RLIMIT_NOFILE, limits["max_files"])
    _set(resource.RLIMIT_FSIZE, limits["fsize_bytes"])
    if hasattr(resource, "RLIMIT_AS"):                # Linux-enforced
        _set(resource.RLIMIT_AS, limits["memory_bytes"])


def _worker(conn, limits, modname, fnname, args, kwargs):
    apply_limits(limits)
    try:
        import importlib
        fn = getattr(importlib.import_module(modname), fnname)
        conn.send(("ok", fn(*args, **kwargs)))
    except BaseException as e:                         # noqa: BLE001 — report all
        conn.send(("err", f"{type(e).__name__}: {e}"))
    finally:
        conn.close()


def isolated_call(modname: str, fnname: str, *args,
                  limits: dict | None = None,
                  timeout: float = DEFAULT_TIMEOUT, **kwargs):
    """Run `modname.fnname(*args, **kwargs)` in a resource-limited worker process
    and return its result. Raises ContainmentError if the worker hangs, dies, or
    raises. The callable and its args/result must be picklable."""
    limits = {**DEFAULT_LIMITS, **(limits or {})}
    ctx = mp.get_context("fork")
    recv, send = ctx.Pipe(False)
    proc = ctx.Process(target=_worker,
                       args=(send, limits, modname, fnname, args, kwargs))
    proc.start()
    send.close()
    if not recv.poll(timeout):
        proc.terminate()
        proc.join(5)
        raise ContainmentError(f"worker exceeded {timeout}s wall-clock; terminated")
    try:
        status, payload = recv.recv()
    except EOFError:
        proc.join()
        raise ContainmentError(
            f"worker died (exit {proc.exitcode}) before returning a result")
    proc.join()
    if status == "err":
        raise ContainmentError(f"worker raised: {payload}")
    return payload
