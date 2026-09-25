"""The triage engine: race -> Granite rank -> adversarial critic -> diagnosis card.

`run_triage` returns a DiagnosisCard. `stream_triage` yields events for the live UI.
Both share the same stages so the CLI and the UI never drift.
"""
import os
import shutil
import sys
import tempfile
import time
from typing import AsyncIterator, Callable, Dict, List

from . import config, granite
from .bob_shell import run_bob_task, bobcoins_spent
from .critic import challenge
from .hypotheses import run_race
from .schema import CriticVerdict, DiagnosisCard, Hypothesis, RankedHypothesis


class _Sandbox:
    """Copy the patient repo to a temp dir and point the engine at it, so Bob agents can never
    mutate the real working tree. No-op in mock mode (nothing is executed)."""

    def __init__(self):
        self._orig = config.REPO_ROOT
        self._dir = None

    def __enter__(self):
        if config.MOCK_MODE or not config.SANDBOX:
            return self
        self._dir = tempfile.mkdtemp(prefix="culprit_sbx_")
        dst = os.path.join(self._dir, "repo")
        shutil.copytree(
            os.path.abspath(self._orig), dst,
            ignore=shutil.ignore_patterns(".venv", "__pycache__", ".pytest_cache", "*.pyc"),
        )
        config.REPO_ROOT = dst
        return self

    def __exit__(self, *exc):
        config.REPO_ROOT = self._orig
        if self._dir:
            shutil.rmtree(self._dir, ignore_errors=True)
        return False


def _summarize_trace(trace: str) -> str:
    first = next((ln for ln in trace.splitlines() if ln.strip()), "").strip()
    return (first[:160] + "…") if len(first) > 160 else first


async def _suggested_fix(winner: RankedHypothesis) -> str:
    # The fix is a BYPRODUCT, produced only after the diagnosis is trusted.
    from .bob_shell import run_bob_task as _r  # local import keeps intent obvious
    prompt = (f"Given confirmed root cause: {winner.hypothesis.title} in "
              f"{winner.hypothesis.culprit_file}:{winner.hypothesis.culprit_symbol}. "
              f"Give the single-line minimal fix. One sentence.")
    hint = f"{winner.hypothesis.title} {winner.hypothesis.culprit_file} {winner.hypothesis.culprit_symbol}"
    import asyncio
    return (await asyncio.to_thread(_r, prompt, role="fix", scenario_text=hint)).strip()


async def stream_triage(trace: str, emit: Callable[[str, Dict], None] = None) -> DiagnosisCard:
    """Run the full pipeline, calling emit(event_type, payload) at each milestone."""
    def _emit(kind: str, payload: Dict):
        if emit:
            emit(kind, payload)

    t0 = time.perf_counter()
    summary = _summarize_trace(trace)
    _emit("start", {"trace_summary": summary})

    # Run everything against a throwaway copy so Bob agents can't touch the real repo.
    with _Sandbox():
        # 1) Parallel hypothesis race
        _emit("race_start", {"width": None})
        hypotheses: List[Hypothesis] = await run_race(trace)
        for h in hypotheses:
            _emit("hypothesis", h.to_dict())

        # 2) Granite risk-ranking (guarded — a flaky watsonx response must not crash the triage;
        #    fall back to the deterministic heuristic ranker).
        _emit("ranking_start", {})
        if hypotheses:
            try:
                ranked: List[RankedHypothesis] = granite.rank(hypotheses, summary)
            except Exception as e:
                print(f"[granite ranking failed, using heuristic: {type(e).__name__}: {e}]", file=sys.stderr)
                ranked = granite._mock_rank(hypotheses)
        else:
            ranked = []
        _emit("ranked", {"all_ranked": [r.to_dict() for r in ranked]})

        winner = ranked[0] if ranked else None

        # 3) Adversarial critic on the winner — two independent passes with different lenses,
        #    run in parallel. The winner survives only if NEITHER pass disproves it.
        critic_verdict = None
        if winner:
            _emit("critic_start", {"winner_id": winner.hypothesis.id})
            try:
                import asyncio
                v1, v2 = await asyncio.gather(
                    challenge(winner, trace,
                              lens="Verify the disproof test truly isolates THIS cause and nothing else."),
                    challenge(winner, trace,
                              lens="Actively hunt for a SIMPLER or alternative root cause the race "
                                   "may have missed. If a more plausible cause exists, set disproved=true."),
                )
                disproved = v1.disproved or v2.disproved
                critic_verdict = CriticVerdict(
                    disproof_test=v1.disproof_test,
                    disproved=disproved,
                    verdict_reason=f"Pass 1 (isolation): {v1.verdict_reason}  ||  "
                                   f"Pass 2 (alternatives): {v2.verdict_reason}",
                )
                _emit("critic", critic_verdict.to_dict())
                if disproved and len(ranked) > 1:
                    winner = ranked[1]
                    _emit("winner_reassigned", {"winner_id": winner.hypothesis.id})
            except Exception as e:
                print(f"[critic failed: {type(e).__name__}: {e}]", file=sys.stderr)
                _emit("critic_failed", {"error": str(e)})

        # 4) Suggested fix (byproduct, shown last)
        fix = await _suggested_fix(winner) if winner else None

    elapsed = time.perf_counter() - t0
    card = DiagnosisCard(
        trace_summary=summary,
        winner=winner,
        critic=critic_verdict,
        all_ranked=ranked,
        suggested_fix=fix,
        triage_seconds=elapsed,
    )
    _emit("done", {**card.to_dict(), "bobcoins": round(bobcoins_spent(), 4)})
    return card


async def run_triage(trace: str) -> DiagnosisCard:
    return await stream_triage(trace, emit=None)
