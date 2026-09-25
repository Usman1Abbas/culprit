"""Pytest suite for the orchestrator package — pure/deterministic logic only.

All tests run under MOCK_MODE so no real Bob Shell calls or watsonx.ai calls are made.
Run from the repo root:
    pytest tests/test_orchestrator.py -v
"""
import os
import pytest

# ---------------------------------------------------------------------------
# 1.  orchestrator.bob_shell.parse_json
# ---------------------------------------------------------------------------

from orchestrator.bob_shell import parse_json


class TestParseJson:
    def test_clean_json(self):
        raw = '{"culprit_file": "app/foo.py", "confidence": 0.9}'
        result = parse_json(raw)
        assert result["culprit_file"] == "app/foo.py"
        assert result["confidence"] == 0.9

    def test_fenced_json(self):
        raw = '```json\n{"title": "Off-by-one", "confidence": 0.8}\n```'
        result = parse_json(raw)
        assert result["title"] == "Off-by-one"
        assert result["confidence"] == 0.8

    def test_prose_before_and_after(self):
        raw = (
            "Here is the analysis you requested:\n"
            '{"culprit_file": "app/tasks.py", "culprit_symbol": "process_task"}\n'
            "Hope that helps!"
        )
        result = parse_json(raw)
        assert result["culprit_file"] == "app/tasks.py"
        assert result["culprit_symbol"] == "process_task"

    def test_raises_on_empty_input(self):
        with pytest.raises(ValueError, match="empty response"):
            parse_json("")

    def test_raises_on_whitespace_only(self):
        with pytest.raises(ValueError, match="empty response"):
            parse_json("   \n  ")

    def test_raises_when_no_json_object(self):
        with pytest.raises(ValueError, match="no JSON object"):
            parse_json("This is just plain text with no braces at all.")


# ---------------------------------------------------------------------------
# 2.  orchestrator.bob_shell._detect_scenario
# ---------------------------------------------------------------------------

from orchestrator.bob_shell import _detect_scenario


class TestDetectScenario:
    def test_pagination_trace(self):
        trace = (
            "AssertionError: GET /tasks?page=1 returned items 11-20, expected items 1-10\n"
            "  File 'app/pagination.py', line 6, in paginate\n"
            "    start = page * per_page"
        )
        assert _detect_scenario(trace) == "pagination"

    def test_parsing_trace_attributeerror(self):
        trace = (
            "AttributeError: 'NoneType' object has no attribute 'lower'\n"
            "  File 'app/parsing.py', line 8, in parse_user\n"
            '    "email": payload["email"].lower()'
        )
        assert _detect_scenario(trace) == "parsing"

    def test_parsing_trace_email_keyword(self):
        # Minimal trigger — just the word "email" in the trace
        trace = "KeyError: 'email' missing from payload in parse_user"
        assert _detect_scenario(trace) == "parsing"

    def test_tasks_trace_await(self):
        trace = (
            "RuntimeWarning: coroutine 'enrich' was never awaited\n"
            "POST /tasks/1/process -> returned a coroutine, expected dict"
        )
        assert _detect_scenario(trace) == "tasks"

    def test_tasks_trace_coroutine(self):
        trace = "AssertionError: got <coroutine object enrich> instead of dict"
        assert _detect_scenario(trace) == "tasks"

    def test_tasks_trace_process_task_keyword(self):
        trace = "Error inside process_task: result was not a dict"
        assert _detect_scenario(trace) == "tasks"

    def test_pagination_default_fallthrough(self):
        # No parsing/tasks keywords → should fall through to pagination
        trace = "AssertionError: unexpected page offset in list_tasks"
        assert _detect_scenario(trace) == "pagination"


# ---------------------------------------------------------------------------
# 3.  orchestrator.granite._extract_json_array
# ---------------------------------------------------------------------------

from orchestrator.granite import _extract_json_array


class TestExtractJsonArray:
    def test_clean_array(self):
        text = '[{"id": "h1", "risk_score": 0.9}, {"id": "h2", "risk_score": 0.4}]'
        result = _extract_json_array(text)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["id"] == "h1"

    def test_fenced_array(self):
        text = '```json\n[{"id": "h3", "risk_score": 0.7}]\n```'
        result = _extract_json_array(text)
        assert result[0]["id"] == "h3"
        assert result[0]["risk_score"] == 0.7

    def test_prose_surrounding_array(self):
        text = (
            "Based on the trace, here is my ranked output:\n"
            '[{"id": "h1", "risk_score": 0.85, "rank_reason": "direct cause"}]\n'
            "Let me know if you need more detail."
        )
        result = _extract_json_array(text)
        assert result[0]["id"] == "h1"
        assert result[0]["risk_score"] == 0.85

    def test_raises_when_no_array(self):
        with pytest.raises(ValueError, match="no JSON array"):
            _extract_json_array("There is no array here, just prose.")


# ---------------------------------------------------------------------------
# 4.  orchestrator.granite._mock_rank
# ---------------------------------------------------------------------------

from orchestrator.schema import Hypothesis
from orchestrator.granite import _mock_rank


def _make_hypothesis(hid: str, confidence: float, has_symbol: bool = True) -> Hypothesis:
    return Hypothesis(
        id=hid,
        title=f"Hypothesis {hid}",
        culprit_file="app/foo.py",
        culprit_symbol="my_func" if has_symbol else "",
        line_hint=10 if has_symbol else None,
        reasoning="Some reasoning.",
        confidence=confidence,
    )


class TestMockRank:
    def test_sorted_by_risk_score_descending(self):
        hypotheses = [
            _make_hypothesis("h1", confidence=0.9),
            _make_hypothesis("h2", confidence=0.3),
            _make_hypothesis("h3", confidence=0.6),
        ]
        ranked = _mock_rank(hypotheses)
        scores = [r.risk_score for r in ranked]
        assert scores == sorted(scores, reverse=True), "risk_scores must be descending"

    def test_highest_confidence_first(self):
        hypotheses = [
            _make_hypothesis("low", confidence=0.2),
            _make_hypothesis("high", confidence=0.95),
            _make_hypothesis("mid", confidence=0.5),
        ]
        ranked = _mock_rank(hypotheses)
        assert ranked[0].hypothesis.id == "high"

    def test_risk_score_bounded_0_to_1(self):
        hypotheses = [_make_hypothesis("h1", confidence=1.0)]
        ranked = _mock_rank(hypotheses)
        assert 0.0 <= ranked[0].risk_score <= 1.0

    def test_specificity_bonus_applied(self):
        # A hypothesis with symbol+line should score higher than one with same confidence but no symbol
        with_symbol = _make_hypothesis("ws", confidence=0.5, has_symbol=True)
        without_symbol = _make_hypothesis("ns", confidence=0.5, has_symbol=False)
        ranked = _mock_rank([without_symbol, with_symbol])
        assert ranked[0].hypothesis.id == "ws", "hypothesis with symbol+line should rank higher"

    def test_returns_all_hypotheses(self):
        hypotheses = [_make_hypothesis(f"h{i}", confidence=i * 0.1) for i in range(1, 6)]
        ranked = _mock_rank(hypotheses)
        assert len(ranked) == 5


# ---------------------------------------------------------------------------
# 5.  End-to-end MOCK triage
# ---------------------------------------------------------------------------

import pathlib
import asyncio
from orchestrator.triage import run_triage


SAMPLES_DIR = pathlib.Path(__file__).parent.parent / "samples"

TRACE_EXPECTATIONS = [
    ("sample_trace_pagination.txt", "app/pagination.py"),
    ("sample_trace_parsing.txt",    "app/parsing.py"),
    ("sample_trace_tasks.txt",      "app/tasks.py"),
]


@pytest.fixture(autouse=True)
def force_mock_mode(monkeypatch):
    """Ensure MOCK_MODE is True for every test in this module."""
    monkeypatch.setenv("MOCK_MODE", "1")
    # Also patch the already-imported config object so run-time checks see True.
    import orchestrator.config as cfg
    monkeypatch.setattr(cfg, "MOCK_MODE", True)


@pytest.mark.parametrize("trace_file,expected_culprit", TRACE_EXPECTATIONS)
async def test_end_to_end_mock_triage(trace_file, expected_culprit):
    trace = (SAMPLES_DIR / trace_file).read_text(encoding="utf-8")
    card = await run_triage(trace)

    assert card.winner is not None, f"No winner produced for {trace_file}"
    assert card.winner.hypothesis.culprit_file == expected_culprit, (
        f"Expected culprit_file={expected_culprit!r}, "
        f"got {card.winner.hypothesis.culprit_file!r} for {trace_file}"
    )
    assert card.suggested_fix, f"suggested_fix is empty for {trace_file}"
