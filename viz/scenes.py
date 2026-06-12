"""Scenarios — map a visualizer request to a run of the medium.

A scenario produces a `meta` dict (static info the frontend needs once: view kind,
byte roles, thresholds, world size) and a `run(on_frame)` that drives the medium,
calling `on_frame` once per window. The server paces/pauses by blocking inside the
`on_frame` it passes in. All organism emulation here is the same contained medium
used everywhere else (C1 traps active); see SECURITY.md C7.
"""

import json

from harness import config
from medium.build import build_organism
from medium.world import WORLD_N, live, live_colony, live_forage

ORGANISMS = config.REPO_ROOT / "organisms"
T_STAR, LAMBDA_STAR, V_STAR = 500, 0.04, 1.2


def _decl(name: str) -> dict:
    p = ORGANISMS / name / "membrane.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _roles(name: str, footprint: int) -> list:
    """Per-byte role for the arena grid: code / membrane / data."""
    d = _decl(name)
    body_len = d.get("body_len", footprint)
    mem = d.get("membrane")
    m_lo, m_len = (mem if mem else (10 ** 9, 0))
    out = []
    for o in range(footprint):
        loc = o % body_len
        if m_lo <= loc < m_lo + m_len:
            out.append("membrane")
        elif loc < m_lo:
            out.append("code")
        else:
            out.append("data")
    return out


def _grid(footprint: int):
    cols = 24
    while footprint % cols and cols > 16:
        cols -= 1
    return cols, (footprint + cols - 1) // cols


def build(spec: dict):
    """Return (meta, run). `spec` keys: scenario, organism, decay, T, lam,
    food_speed, heads, seed, lifetime, speed (speed handled by the server)."""
    scen = spec.get("scenario", "arena")
    seed = int(spec.get("seed", 0))

    if scen == "forager":
        name = spec.get("organism", "forager0")
        code = build_organism(name)
        speed = float(spec.get("food_speed", 0.8))
        lifetime = int(spec.get("lifetime", 600))
        meta = {"kind": "forager", "organism": name, "world_n": WORLD_N,
                "v_star": V_STAR, "food_speed": speed}

        def run(on_frame):
            live_forage(code, T=10000, lifetime=lifetime, food_speed=speed,
                        seed=seed, on_frame=on_frame)
        return meta, run

    if scen == "colony":
        name = spec.get("organism", "protocell2")
        code = build_organism(name)
        d = _decl(name)
        footprint = d.get("footprint", len(code))
        body_len = d.get("body_len", footprint)
        nheads = int(spec.get("heads", 2))
        heads = [k * body_len for k in range(nheads)]
        lam = float(spec.get("lam", 0.08))
        lifetime = int(spec.get("lifetime", 400))
        cols, rows = _grid(footprint)
        meta = {"kind": "colony", "organism": name, "footprint": footprint,
                "cols": cols, "rows": rows, "roles": _roles(name, footprint),
                "birth": list(code), "body_len": body_len, "heads": nheads,
                "lambda": lam, "lambda_star": LAMBDA_STAR}

        def run(on_frame):
            live_colony(code, T=8000, footprint=footprint, heads=heads,
                        lifetime=lifetime, lam=lam, seed=seed, on_frame=on_frame)
        return meta, run

    # default: single organism in the arena
    name = spec.get("organism", "protocell1")
    code = build_organism(name)
    d = _decl(name)
    footprint = d.get("footprint", len(code))
    decay = spec.get("decay", "bitrot")
    T = int(spec.get("T", 4000))
    lam = float(spec.get("lam", 0.08))
    lifetime = int(spec.get("lifetime", 600))
    cols, rows = _grid(footprint)
    meta = {"kind": "arena", "organism": name, "footprint": footprint,
            "cols": cols, "rows": rows, "roles": _roles(name, footprint),
            "birth": list(code), "decay": decay, "T": T, "lam": lam,
            "t_star": T_STAR, "lambda_star": LAMBDA_STAR}

    def run(on_frame):
        live(code, T=T, lifetime=lifetime, body_hint=footprint, decay=decay,
             lam=lam, seed=seed, on_frame=on_frame)
    return meta, run
