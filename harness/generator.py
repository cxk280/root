"""Pluggable candidate-generation interface.

The rig treats "where candidate source code comes from" as a strategy so the
experiment protocol doesn't change when the engine does. Milestone 1 uses
InSessionSource: Claude authors files under candidates/ during a session and
the harness simply picks them up. A future hybrid engine (autonomous cheap
mutations + sparing API calls for intelligent rewrites) implements the same
two methods and nothing downstream moves.
"""

from pathlib import Path
from typing import Protocol

from . import config


class CandidateSource(Protocol):
    def next_candidate(self, kernel: str, condition: str,
                       feedback: dict | None) -> Path:
        """Return a source file (.c or .s) for the kernel. `feedback` is the
        previous round's runner report (None on round 1)."""
        ...

    def rounds(self) -> int:
        """Maximum feedback rounds this source supports."""
        ...


class InSessionSource:
    """Candidates are files authored in-session at
    candidates/<kernel>/<condition>/round<N>.{c,s}; feedback is delivered as
    conversation context rather than through this object."""

    def __init__(self, max_rounds: int = 5):
        self._max_rounds = max_rounds

    def next_candidate(self, kernel: str, condition: str,
                       feedback: dict | None) -> Path:
        cdir = config.REPO_ROOT / "candidates" / kernel / condition
        rounds = sorted(cdir.glob("round*.[cs]"))
        if not rounds:
            raise FileNotFoundError(f"no candidate authored yet in {cdir}")
        return rounds[-1]

    def rounds(self) -> int:
        return self._max_rounds
