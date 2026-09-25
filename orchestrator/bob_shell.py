"""Thin wrapper around Bob Shell (the `bob` CLI).

MOCK_MODE=1 (default): returns canned, plausible JSON so the whole pipeline runs with zero
Bobcoins. MOCK_MODE=0: shells out to Bob Shell.

IMPORTANT (real mode): confirm the exact Bob Shell invocation and flags from bob.ibm.com/docs
once your hackathon invite is active. The subprocess call below is a best-effort placeholder
marked with TODO — verify `--instance`, prompt-passing, and how to force non-interactive output
before you burn Bobcoins.
"""
import json
import os
import subprocess
import threading
from typing import Optional

from . import config


class BobShellError(RuntimeError):
    pass


# --- live Bobcoin metering (shared across all concurrent bob run calls) -----
_cost_lock = threading.Lock()
_total_cost = 0.0
_call_count = 0


def bobcoins_spent() -> float:
    """Total Bobcoins consumed by real `bob run` calls so far this process."""
    return _total_cost


def calls_made() -> int:
    return _call_count


def _record_cost(stats: dict) -> None:
    global _total_cost, _call_count
    # Docs describe stats.* including cost; field name has been seen as both "cost" and
    # "session_costs" — read defensively so metering never crashes the pipeline.
    cost = 0.0
    for key in ("cost", "session_costs", "session_cost"):
        if isinstance(stats, dict) and stats.get(key) is not None:
            try:
                cost = float(stats[key])
            except (TypeError, ValueError):
                cost = 0.0
            break
    with _cost_lock:
        _total_cost += cost
        _call_count += 1


def run_bob_task(prompt: str, *, role: str, mock_response: Optional[str] = None,
                 timeout: int = 180, scenario_text: Optional[str] = None) -> str:
    """Run a single Bob agent (one `bob run` process) and return its final answer text.

    Parallelism is achieved by the orchestrator launching many of these concurrently — each is
    an independent Bob agent session. `role` picks the canned response in mock mode; the mock
    detects the scenario from `scenario_text` (the raw trace) rather than the full prompt, because
    the prompt also contains angle descriptions that would confuse detection.
    """
    if config.MOCK_MODE:
        if mock_response is not None:
            return mock_response
        return _canned(role, scenario_text if scenario_text is not None else prompt)

    # --- REAL MODE ---------------------------------------------------------
    # bob run [options] [prompt].  Auth comes from BOB_API_KEY in the environment (no flag).
    # No --instance flag exists: the instance is baked into the API key.
    if not config.BOB_API_KEY:
        raise BobShellError(
            "BOB_API_KEY is not set. Create an Inference-scoped key from inside the "
            "ibm-coding-challenge-uat instance and set BOB_API_KEY, or keep MOCK_MODE=1."
        )

    cmd = [config.BOB_NODE, config.BOB_JS, "run",
           "--format", "json",
           "--trust", "--accept-license",       # clear first-run gates non-interactively
           "--workspace", os.path.abspath(config.REPO_ROOT),
           "--mode", config.BOB_MODE,
           "--max-cost", str(config.BOB_MAX_COST)]
    if config.BOB_TEAM_ID:  # only needed for 'general'-type keys
        cmd += ["--team-id", config.BOB_TEAM_ID]
    cmd += [prompt]

    env = dict(os.environ)
    env["BOB_API_KEY"] = config.BOB_API_KEY  # ensure the child sees it

    try:
        # CRITICAL: stdin=DEVNULL. Bob blocks forever on a non-TTY stdin waiting for input;
        # giving it immediate EOF is what makes headless runs return (verified 2026-09-26).
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env,
                              stdin=subprocess.DEVNULL)
    except FileNotFoundError as e:
        raise BobShellError(
            f"Could not launch Bob via '{config.BOB_NODE} {config.BOB_JS}'. Check node is on PATH "
            f"and BOB_JS points at bobshell/dist/bob.js, or keep MOCK_MODE=1."
        ) from e
    if proc.returncode != 0:
        raise BobShellError(f"Bob task ({role}) failed [exit {proc.returncode}]: {proc.stderr.strip()}")

    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise BobShellError(f"Bob task ({role}) returned non-JSON output: {proc.stdout[:400]}") from e

    if result.get("status") == "error":
        raise BobShellError(f"Bob task ({role}) reported error: {result}")

    _record_cost(result.get("stats", {}) or {})
    # `last_message` is the final assistant text — this is the agent's answer.
    return (result.get("last_message") or "").strip()


def parse_json(text: str) -> dict:
    """Extract the agent's JSON object, tolerating fences and surrounding prose.

    Real Bob sometimes wraps the JSON in a sentence or a ```json fence. We strip fences, then
    use raw_decode from the first '{' so trailing prose (and braces inside strings) are handled
    correctly.
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("empty response from Bob")

    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            head, rest = text.split("\n", 1)
            if head.strip().lower() in ("json", ""):
                text = rest
        text = text.strip()

    idx = text.find("{")
    if idx == -1:
        raise ValueError(f"no JSON object in response: {text[:200]}")
    obj, _ = json.JSONDecoder().raw_decode(text[idx:])
    return obj


# --- canned mock output (scenario-aware) -----------------------------------
# Each scenario provides: the correct hypothesis for whichever angle catches it (h1=logic,
# h2=validation, h3=data/state), two plausible-but-wrong decoys for the other angles, a critic
# verdict, and the byproduct fix. The mock detects the scenario from the trace text so different
# traces produce genuinely different diagnoses — no Bobcoins, rehearsal-ready.
_SCENARIOS = {
    "pagination": {
        "h1": {
            "title": "Off-by-one in paginate(): 1-indexed page treated as 0-indexed",
            "culprit_file": "app/pagination.py", "culprit_symbol": "paginate", "line_hint": 6,
            "reasoning": "GET /tasks?page=1 returns items 11-20 instead of 1-10. In paginate(), "
                         "start = page * per_page gives 10 for page=1, so items[10:20] is returned. "
                         "A 1-indexed page needs (page-1)*per_page.",
            "confidence": 0.9,
        },
        "h2": {
            "title": "Missing bounds check on the `page` query parameter",
            "culprit_file": "app/main.py", "culprit_symbol": "list_tasks", "line_hint": 21,
            "reasoning": "No guard for page<=0 on the endpoint. Plausible, but it does not explain "
                         "the exact one-page (10-item) shift that was observed.",
            "confidence": 0.4,
        },
        "h3": {
            "title": "Seed data _TASKS misaligned with page indexing",
            "culprit_file": "app/main.py", "culprit_symbol": "_TASKS", "line_hint": 17,
            "reasoning": "Considered the seed list's starting value, but _TASKS starts at 1; the "
                         "slice math in paginate() is the more direct cause.",
            "confidence": 0.3,
        },
        "h4": {
            "title": "Suspected async/ordering effect in the request path",
            "culprit_file": "app/main.py", "culprit_symbol": "list_tasks", "line_hint": 21,
            "reasoning": "Checked for concurrency/ordering effects, but the endpoint is synchronous; "
                         "the shift is deterministic slice math, not a race.",
            "confidence": 0.2,
        },
        "h5": {
            "title": "Return-shape/contract mismatch in paginate()",
            "culprit_file": "app/pagination.py", "culprit_symbol": "paginate", "line_hint": 6,
            "reasoning": "The return type is correct (a list slice); the contract is fine — the "
                         "start offset is what's wrong.",
            "confidence": 0.33,
        },
        "critic": {
            "disproof_test": "assert paginate(list(range(1,21)), page=1, per_page=10) == list(range(1,11))",
            "disproved": False,
            "verdict_reason": "The test fails on current code (returns 11-20) and passes after "
                              "(page-1)*per_page. The off-by-one fully explains the shift; confirmed.",
        },
        "fix": "In paginate(), change `start = page * per_page` to `start = (page - 1) * per_page`.",
    },
    "parsing": {
        "h2": {
            "title": "Unguarded access to optional 'email' field in parse_user()",
            "culprit_file": "app/parsing.py", "culprit_symbol": "parse_user", "line_hint": 8,
            "reasoning": "Trace is AttributeError: 'NoneType' has no attribute 'lower' from "
                         "parse_user. `email` is optional and may be None/absent, but "
                         "payload['email'].lower() assumes a non-null string.",
            "confidence": 0.9,
        },
        "h1": {
            "title": "Case-normalization logic error on email",
            "culprit_file": "app/parsing.py", "culprit_symbol": "parse_user", "line_hint": 8,
            "reasoning": "Looked at the .lower() transform, but the transform itself is correct; "
                         "the failure is the None input, not the normalization logic.",
            "confidence": 0.35,
        },
        "h3": {
            "title": "Request schema permits a null email",
            "culprit_file": "app/main.py", "culprit_symbol": "UserIn", "line_hint": 28,
            "reasoning": "The Pydantic model allows email=None. Tightening the schema would help, "
                         "but the crash originates in parse_user, not the schema.",
            "confidence": 0.42,
        },
        "h4": {
            "title": "Async handling issue in create_user",
            "culprit_file": "app/main.py", "culprit_symbol": "create_user", "line_hint": 38,
            "reasoning": "No async is involved in this path; the crash is a null attribute access, "
                         "not a concurrency defect.",
            "confidence": 0.18,
        },
        "h5": {
            "title": "Schema/type contract permits an optional email",
            "culprit_file": "app/main.py", "culprit_symbol": "UserIn", "line_hint": 28,
            "reasoning": "The model types email as optional; tightening the contract could prevent "
                         "None, but the crash still originates in parse_user.",
            "confidence": 0.4,
        },
        "critic": {
            "disproof_test": "assert parse_user({'name': 'Ada'}).get('email') is None  # must not raise",
            "disproved": False,
            "verdict_reason": "parse_user without an email raises today; after guarding the optional "
                              "field it returns None safely. The unguarded access is the root cause.",
        },
        "fix": "Guard the optional field: `email = payload.get('email')` then "
               "`'email': email.lower() if email else None`.",
    },
    "tasks": {
        "h1": {
            "title": "Missing await on enrich() in process_task()",
            "culprit_file": "app/tasks.py", "culprit_symbol": "process_task", "line_hint": 12,
            "reasoning": "RuntimeWarning 'coroutine enrich was never awaited' plus a returned "
                         "coroutine object show enrich() is called without await, so process_task "
                         "returns the coroutine instead of its result.",
            "confidence": 0.9,
        },
        "h2": {
            "title": "process_task does not validate its task payload",
            "culprit_file": "app/tasks.py", "culprit_symbol": "process_task", "line_hint": 11,
            "reasoning": "Considered input validation, but the failure is a coroutine-not-awaited, "
                         "unrelated to payload contents.",
            "confidence": 0.3,
        },
        "h3": {
            "title": "enrich() returns the wrong shape",
            "culprit_file": "app/tasks.py", "culprit_symbol": "enrich", "line_hint": 8,
            "reasoning": "enrich() returns the enriched dict correctly; the problem is the caller "
                         "not awaiting it.",
            "confidence": 0.35,
        },
        "h4": {
            "title": "Unawaited coroutine: process_task returns enrich() without await",
            "culprit_file": "app/tasks.py", "culprit_symbol": "process_task", "line_hint": 12,
            "reasoning": "The concurrency lens catches it directly: enrich() is a coroutine returned "
                         "without await, so the caller receives a coroutine object — matching the "
                         "RuntimeWarning.",
            "confidence": 0.88,
        },
        "h5": {
            "title": "Return-shape contract mismatch in process_task",
            "culprit_file": "app/tasks.py", "culprit_symbol": "process_task", "line_hint": 12,
            "reasoning": "The declared return is a dict but a coroutine is returned; the contract "
                         "mismatch is a symptom of the missing await.",
            "confidence": 0.55,
        },
        "critic": {
            "disproof_test": "result = await process_task({'id': 1}); assert result.get('enriched') is True",
            "disproved": False,
            "verdict_reason": "The test fails today (result is a coroutine) and passes once enrich() "
                              "is awaited. Missing await is the confirmed cause.",
        },
        "fix": "In process_task(), `return await enrich(task)` (add the missing await).",
    },
}


def _detect_scenario(text: str) -> str:
    t = (text or "").lower()
    if any(k in t for k in ("await", "coroutine", "enrich", "process_task")):
        return "tasks"
    if any(k in t for k in ("email", "nonetype", ".lower", "parse_user", "keyerror")):
        return "parsing"
    return "pagination"


def _canned(role: str, prompt: str = "") -> str:
    scenario = _SCENARIOS[_detect_scenario(prompt)]
    if role == "fix":
        return scenario["fix"]
    if role in ("h1", "h2", "h3", "h4", "h5", "critic"):
        return json.dumps(scenario[role])
    # unknown role → return the validation-angle hypothesis as a safe default
    return json.dumps(scenario.get("h2", scenario.get("h1")))
