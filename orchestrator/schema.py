"""Typed shapes passed between the triage stages and streamed to the UI."""
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict


@dataclass
class Hypothesis:
    id: str
    title: str                # one-line claim, e.g. "Off-by-one in paginate() start index"
    culprit_file: str
    culprit_symbol: str
    line_hint: Optional[int]
    reasoning: str            # evidence the subagent gathered from the trace + repo
    confidence: float         # 0..1 self-reported by the hypothesis subagent

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RankedHypothesis:
    hypothesis: Hypothesis
    risk_score: float         # Granite: blast-radius / severity, 0..1
    rank_reason: str          # Granite's justification

    def to_dict(self) -> Dict:
        d = {"risk_score": self.risk_score, "rank_reason": self.rank_reason}
        d.update(self.hypothesis.to_dict())
        return d


@dataclass
class CriticVerdict:
    disproof_test: str        # a test the critic wrote that should FAIL if the hypothesis is right
    disproved: bool           # True => hypothesis rejected
    verdict_reason: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DiagnosisCard:
    trace_summary: str
    winner: Optional[RankedHypothesis]
    critic: Optional[CriticVerdict]
    all_ranked: List[RankedHypothesis] = field(default_factory=list)
    suggested_fix: Optional[str] = None       # byproduct, shown last
    triage_seconds: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "trace_summary": self.trace_summary,
            "winner": self.winner.to_dict() if self.winner else None,
            "critic": self.critic.to_dict() if self.critic else None,
            "all_ranked": [r.to_dict() for r in self.all_ranked],
            "suggested_fix": self.suggested_fix,
            "triage_seconds": round(self.triage_seconds, 2),
        }
