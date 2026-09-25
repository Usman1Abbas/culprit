# Culprit — Architecture

## Overview

**Culprit** is a verifiable root-cause triage engine built on IBM Bob 2.0 and watsonx.ai Granite.
Given a failing stack trace or test log, it diagnoses *why* a failure happens — not just how to
patch it. The suggested fix is a deliberate byproduct: it appears only after the diagnosis has
survived adversarial challenge.

Key properties:
- **Parallel reasoning** — N independent Bob agents attack the same trace from different angles
  simultaneously, catching root causes that a single-pass LLM would miss.
- **Model-graded ranking** — watsonx.ai Granite scores each hypothesis by risk/blast-radius rather
  than by the agent's self-reported confidence alone.
- **Adversarial verification** — two critic passes try to disprove the winner before it is shown.
  Only a diagnosis that survives both passes reaches the output.
- **Non-destructive** — all agent work runs against a throwaway copy of the repo; the real working
  tree is never touched.

---

## Pipeline

The pipeline is implemented as a single `async` function,
[`stream_triage()`](../orchestrator/triage.py), which drives all four stages in order and pushes
Server-Sent Events to the live UI at each milestone.

### Stage 1 — Parallel hypothesis race

**Module:** [`orchestrator/hypotheses.py`](../orchestrator/hypotheses.py)

`run_race(trace)` launches `RACE_WIDTH` concurrent async tasks (default 5), one per angle defined
in `ANGLES`:

| ID | Angle |
|----|-------|
| h1 | Logic error (off-by-one, boundary, wrong operator) |
| h2 | Input validation / unhandled edge case |
| h3 | Data / state / configuration issue |
| h4 | Concurrency / async defect (missing `await`, race condition) |
| h5 | Interface / contract mismatch (wrong type, API shape) |

Each angle is run by an independent `bob run` process via
[`orchestrator/bob_shell.py`](../orchestrator/bob_shell.py) → `run_bob_task()`.
Because `run_bob_task` is a blocking subprocess call, it is pushed off the event loop with
`asyncio.to_thread`; all five fire concurrently via `asyncio.gather`.

Each agent is given the [`hypothesis_agent.md`](../orchestrator/prompts/hypothesis_agent.md)
prompt and must return a single JSON object: `title`, `culprit_file`, `culprit_symbol`,
`line_hint`, `reasoning`, `confidence`. The result is deserialised into a
[`Hypothesis`](../orchestrator/schema.py) dataclass. A flaky or empty agent is silently dropped so
one failure cannot kill the whole race.

### Stage 2 — Granite risk-ranking

**Module:** [`orchestrator/granite.py`](../orchestrator/granite.py)

`granite.rank(hypotheses, trace_summary)` sends all surviving hypotheses to watsonx.ai
(`ibm/granite-4-h-small` by default) via the text-generation REST API. Granite scores each
hypothesis with a `risk_score` (0–1, reflecting blast-radius / severity) and a `rank_reason`.
Results are deserialised into [`RankedHypothesis`](../orchestrator/schema.py) objects and sorted
descending by `risk_score`.

**Fallback:** if `WATSONX_API_KEY` / `WATSONX_PROJECT_ID` are absent, ranking falls back to a
local heuristic that combines `confidence` (70 %) and specificity — whether the agent pinpointed
a concrete file + symbol + line (30 %). The top-ranked hypothesis becomes the **winner**.

### Stage 3 — Dual adversarial critic

**Modules:** [`orchestrator/critic.py`](../orchestrator/critic.py) and
[`orchestrator/triage.py`](../orchestrator/triage.py)

The winner is challenged by two independent critic passes, run in parallel via `asyncio.gather`:

| Pass | Lens |
|------|------|
| **Isolation** | *Verify the disproof test truly isolates this cause and nothing else.* |
| **Alternatives** | *Actively hunt for a simpler or alternative root cause the race may have missed.* |

Each pass is a separate `bob run` process using the
[`critic_agent.md`](../orchestrator/prompts/critic_agent.md) prompt. The critic must write a
minimal pytest assertion that should fail on the current (buggy) code and pass after the fix, then
decide `disproved: true/false`.

The winner is **rejected** if *either* pass returns `disproved: true`. If rejected and a
second-ranked hypothesis exists, it is promoted as the new winner. Both verdicts are merged into a
single [`CriticVerdict`](../orchestrator/schema.py) that shows both reasoning chains.

### Stage 4 — Suggested fix (byproduct)

**Module:** [`orchestrator/triage.py`](../orchestrator/triage.py) → `_suggested_fix()`

Only after the winner survives both critic passes, one more `bob run` call asks for the
single-line minimal fix. This is explicitly a **byproduct** — the diagnosis is the primary output.

### Non-destructive sandbox

**Module:** [`orchestrator/triage.py`](../orchestrator/triage.py) → `_Sandbox`

Before the race begins, `_Sandbox.__enter__` copies the entire patient repo to a throwaway
`tempfile.mkdtemp` directory (skipping `.venv`, `__pycache__`, `.pytest_cache`, `*.pyc`) and
re-points `config.REPO_ROOT` at the copy. Bob's agent mode has write tools that will edit code;
the sandbox ensures those edits can never touch the real working tree. The temp directory is
deleted in `__exit__`, regardless of outcome. The sandbox is a no-op in `MOCK_MODE`.

---

## Pipeline diagram

```mermaid
flowchart TD
    A([Paste trace / log]) --> B[_Sandbox: copy repo to temp dir]
    B --> C

    subgraph RACE ["Stage 1 — Parallel hypothesis race (orchestrator/hypotheses.py)"]
        C["asyncio.gather — 5 concurrent bob run agents"]
        C --> H1["h1: Logic error"]
        C --> H2["h2: Input validation"]
        C --> H3["h3: Data/state"]
        C --> H4["h4: Concurrency/async"]
        C --> H5["h5: Interface/contract"]
    end

    H1 & H2 & H3 & H4 & H5 --> D

    subgraph RANK ["Stage 2 — Granite risk-ranking (orchestrator/granite.py)"]
        D["watsonx.ai Granite — score by risk/blast-radius\n(heuristic fallback if creds absent)"]
        D --> E[Ranked hypotheses — winner = highest risk_score]
    end

    E --> F

    subgraph CRITIC ["Stage 3 — Dual adversarial critic (orchestrator/critic.py + triage.py)"]
        F["asyncio.gather — 2 concurrent critic bob run agents"]
        F --> V1["Pass 1: Isolation lens"]
        F --> V2["Pass 2: Alternative-cause lens"]
        V1 & V2 --> G{Either disproved?}
        G -- yes --> G2[Promote runner-up]
        G -- no --> G3[Winner confirmed]
    end

    G2 & G3 --> FIX

    subgraph FIX ["Stage 4 — Suggested fix (byproduct)"]
        FIX["bob run — one-line minimal fix"]
    end

    FIX --> OUT([DiagnosisCard → UI / CLI])
```

---

## Mock vs Live mode

Controlled by the `MOCK_MODE` environment variable (default `1`).

| Mode | Behaviour |
|------|-----------|
| `MOCK_MODE=1` | All `bob run` calls return scenario-aware canned JSON from `bob_shell._SCENARIOS`. Granite ranking uses the local heuristic. Zero Bobcoins consumed. Instant. Safe for rehearsal and CI. |
| `MOCK_MODE=0` | Real `bob run` subprocesses fire against the live Bob Shell. Granite ranking calls watsonx.ai. Consumes Bobcoins (budget: 40 for the hackathon). Requires `BOB_API_KEY` and optionally `WATSONX_API_KEY` / `WATSONX_PROJECT_ID` in `.env`. |

`RACE_WIDTH` (default `5`) controls how many parallel hypothesis agents run; lower it to conserve
Bobcoins during live testing.

---

## How Bob is used

- **Process-level parallelism.** Bob is invoked as an independent subprocess for every agent call
  (`bob run` via [`orchestrator/bob_shell.py`](../orchestrator/bob_shell.py) → `run_bob_task`).
  The orchestrator launches N of these concurrently (up to `RACE_WIDTH` hypothesis agents +
  2 critic agents), each a fully independent Bob session with no shared state.
- **No model pin.** Bob's model is auto-selected by the Bob Shell runtime; the orchestrator does
  not pin a model for any Bob agent call.
- **Granite is separate.** watsonx.ai Granite (`ibm/granite-4-h-small`) is invoked directly via
  REST only for the risk-ranking stage — it never goes through Bob Shell. This keeps ranking fast
  and deterministic, and makes Granite's contribution explicit and auditable.

---

## Demo application (`demo_app/`)

`demo_app/` is a minimal FastAPI service with three intentionally planted bugs — one per module —
that serve as the controlled "patient" for the demo:

| Module | Bug |
|--------|-----|
| [`app/pagination.py`](../demo_app/app/pagination.py) | Off-by-one: `start = page * per_page` treats a 1-indexed page as 0-indexed |
| [`app/parsing.py`](../demo_app/app/parsing.py) | Unguarded optional: `payload["email"].lower()` crashes when `email` is `None` |
| [`app/tasks.py`](../demo_app/app/tasks.py) | Missing `await`: `process_task` returns the `enrich()` coroutine object instead of its result |

The failing pytest suite in `demo_app/tests/` is intentional — it is the target the triage engine
diagnoses. **Do not fix the bugs silently; the failures are the demo.**

---

## Entry points

| Command | Description |
|---------|-------------|
| `python run_demo.py --trace samples/sample_trace_pagination.txt` | CLI — runs triage and prints the diagnosis card |
| `python -m ui.server` | Web UI — streams pipeline events over SSE; open `http://127.0.0.1:8000` |
