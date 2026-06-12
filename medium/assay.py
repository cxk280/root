"""The aliveness assay — Maturana & Varela's six-point key, operationalized.

The key is fundamentally about INTERVENTION ("determine whether ablating the
boundary components halts the production of components"), not passive observation
— passive read-counting cannot tell an organism consulting its boundary from one
merely reading its body as copy payload (the bug that motivated this design).

An organism DECLARES its membrane and synthase regions (organisms/<name>/
membrane.json). The assay does not take the claim on faith: a declared membrane
counts as genuine only if provenance + intervention confirm it is
  (a) read during life, (b) NEVER executed (it is data, not code that merely
  faults when damaged), (c) re-written every cycle (self-produced), and
  (d) value-corrupting it KILLS an otherwise-living organism.
A false declaration (pointing at incidental bytes) fails (a)-(d) and earns no
credit. This is what separates protocell0's functioning boundary from blind's
absence of one.
"""

import json
from dataclasses import dataclass, field

from harness import config
from .world import live

ORGANISMS = config.REPO_ROOT / "organisms"


def declaration(name: str) -> dict:
    return json.loads((ORGANISMS / name / "membrane.json").read_text())


def _corrupt(code: bytes, lo: int, length: int) -> bytes:
    return _apply(code, lo, length, lambda v: v ^ 0xFF)  # change value, stay data


def _zero(code: bytes, lo: int, length: int) -> bytes:
    return _apply(code, lo, length, lambda v: 0)


def _apply(code: bytes, lo: int, length: int, fn, copies=1, stride=0) -> bytes:
    """Apply fn to bytes [lo,lo+length) in EVERY copy. For a redundant organism
    (replicate>1) a component is only ablated when damaged in all copies — a
    single-copy hit is repaired by the vote — so interventions target
    lo + k*stride for k in 0..copies-1."""
    b = bytearray(code)
    for k in range(copies):
        base = lo + k * stride
        for o in range(max(0, base), min(base + length, len(b))):
            b[o] = fn(b[o]) & 0xFF
    return bytes(b)


@dataclass
class Assay:
    organism: str
    footprint: int
    survives: bool
    lifespan: int
    mean_turnover: float
    mean_integrity: float
    t_star: int | None
    criteria: dict = field(default_factory=dict)
    evidence: dict = field(default_factory=dict)

    @property
    def closure_score(self) -> int:
        return sum(1 for v in self.criteria.values() if v)


def phase_transition(code: bytes, ladder, lifetime: int):
    t_star, results = None, {}
    for T in ladder:
        s = live(code, T=T, lifetime=lifetime).survived
        results[T] = s
        if s and t_star is None:
            t_star = T
    return t_star, results


def assay(name: str, code: bytes, *, T_live: int, lifetime: int = 120,
          ladder=None) -> Assay:
    ladder = ladder or [60, 120, 200, 300, 400, 600, 900, 1400, 2200, 3500]
    decl = declaration(name)
    foot = decl.get("footprint", len(code))

    base = live(code, T=T_live, lifetime=lifetime)
    prov = live(code, T=T_live, lifetime=12, probe=True)   # provenance run

    # Redundant organisms: ablate a component in ALL copies (a single-copy hit is
    # repaired by the vote). copies/stride come from the declaration.
    copies = decl.get("replicate", 1)
    stride = decl.get("body_len", 0)

    # --- synthase intervention: zeroing the production machinery must halt life
    syn_lo, syn_len = decl.get("synthase", [0, 0])
    intact = live(code, T=T_live, lifetime=16)
    no_synthase = live(_apply(code, syn_lo, syn_len, lambda v: 0, copies, stride),
                       T=T_live, lifetime=16)
    synthase_matters = intact.survived and not no_synthase.survived
    synthase_self_produced = set(range(syn_lo, syn_lo + syn_len)) <= prov.write_offsets

    # --- membrane verification (declared region must EARN the title) ---
    mem = decl.get("membrane")
    membrane_genuine = False
    ev = {}
    if mem:
        m_lo, m_len = mem
        region = set(range(m_lo, m_lo + m_len))
        read = region <= prov.read_offsets
        not_executed = region.isdisjoint(prov.exec_offsets)
        rewritten = region <= prov.write_offsets
        corrupted = live(_apply(code, m_lo, m_len, lambda v: v ^ 0xFF, copies, stride),
                         T=T_live, lifetime=16)
        corruption_kills = intact.survived and not corrupted.survived
        membrane_genuine = read and not_executed and rewritten and corruption_kills
        ev = {"read": read, "not_executed": not_executed,
              "rewritten": rewritten, "corruption_kills": corruption_kills}

    closed = base.survived and prov.external_reads == 0 and synthase_self_produced
    t_star, ladder_results = phase_transition(code, ladder, lifetime)

    criteria = {
        "1_identifiable_boundary": membrane_genuine,
        "2_constitutive_components": membrane_genuine and synthase_matters,
        "3_mechanistic": True,
        "4_boundary_self_produced": membrane_genuine,   # (d)+(c) proven above
        "5_boundary_conditions_dynamics": membrane_genuine,
        "6_closure_no_external_scaffold": closed,
    }
    return Assay(organism=name, footprint=foot, survives=base.survived,
                 lifespan=base.lifespan, mean_turnover=base.mean_turnover,
                 mean_integrity=base.mean_integrity, t_star=t_star,
                 criteria=criteria,
                 evidence={"membrane": ev, "synthase_matters": synthase_matters,
                           "synthase_self_produced": synthase_self_produced,
                           "external_reads": prov.external_reads,
                           "phase_transition": ladder_results})


def assay_full(name: str, code: bytes, T_live: int = 4000, lifetime: int = 120,
               fine=tuple(range(100, 1001, 50))) -> dict:
    """The complete per-organism assay plus a fine phase-transition sweep, as a
    picklable dict. This is the unit of work run inside an isolated worker
    (harness.isolation) so all organism emulation is contained."""
    A = assay(name, code, T_live=T_live, lifetime=lifetime)
    t_star, table = None, {}
    for T in fine:
        L = live(code, T=T, lifetime=150)
        table[str(T)] = {"survived": L.survived, "lifespan": L.lifespan,
                         "death": L.cause}
        if L.survived and t_star is None:
            t_star = T
    return {"footprint": A.footprint, "survives": A.survives,
            "lifespan": A.lifespan, "closure_score": A.closure_score,
            "criteria": A.criteria, "evidence": A.evidence,
            "t_star_fine": t_star, "mean_turnover": A.mean_turnover,
            "mean_integrity": A.mean_integrity, "phase_fine": table}
