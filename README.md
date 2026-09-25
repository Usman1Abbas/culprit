# Culprit — verifiable root-cause triage for inherited code

> IBM Bob 2.0 Hackathon (Sep 25–27, 2026) · solo build

**The expensive part of a bug isn't the fix — it's the triage.** Finding *which* of several
plausible causes is the real one eats hours of reading unfamiliar code. Autofix tools (and Bob's
stock quick-fix / PR generation) jump straight to a patch. **Culprit makes the diagnosis
trustworthy first.**

## How it works

1. Paste a stack trace / failing CI log / GitHub issue.
2. The orchestrator (**Bob Shell**) fans out **N parallel subagents**, each committed to a
   *different* root-cause hypothesis — a genuine race, not sequential guessing.
3. A **watsonx.ai Granite** agent ranks the surviving hypotheses by risk / blast-radius.
4. An **adversarial critic subagent** tries to *disprove* the top hypothesis (writes a test that
   should fail if it's right) before anything is shown to the user.
5. Output: a ranked, evidence-backed **diagnosis card** — culprit location, why, confidence, and
   the disproof-test result. The fix is a byproduct shown last, never the headline.

The headline metric is **triage time**, not "PR opened."

## Why this is different from Bob's stock features / Devin / Sweep

Bob already does bug-fix + PR natively. Culprit does *not* touch that. Its value is the
**triage reasoning + verification** layer — parallel competing hypotheses, Granite risk-ranking,
and an adversarial disproof loop — which neither Bob's stock features nor the SWE-agent genre do.

## Run it (mock mode — zero Bobcoins)

```bash
python -m venv .venv && . .venv/Scripts/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1) See the "patient" repo fail (red):
pytest demo_app -q

# 2) Run triage on a sample trace from the CLI:
python run_demo.py --trace samples/sample_trace_pagination.txt

# 3) Launch the 3-screen demo UI:
python -m ui.server           # then open http://127.0.0.1:8000
```

Everything runs in `MOCK_MODE=1` (the default) with canned-but-plausible agent output, so the full
golden path demos before you spend a single Bobcoin. Flip to real Bob Shell + Granite by setting
env vars (see `.env.example`) and `MOCK_MODE=0`.

## Layout

```
demo_app/        the buggy FastAPI service under test (the "patient") + failing pytest suite
orchestrator/    the triage engine: bob_shell wrapper, hypothesis agents, granite ranker, critic
  prompts/       the actual prompt templates each subagent runs
ui/              3-screen streaming demo (paste trace -> hypothesis race -> verdict + timer)
samples/         sample traces + notes on the real GitHub issue to prove generalization
bob_sessions/    <-- REQUIRED at submission: Bob task-session summary screenshots go here
```

## Submission checklist (see SUBMISSION.md)
- [ ] Public repo (fork the IBM template, keep .bobignore)
- [ ] 3-min video, ≥90s live on screen, demo up front
- [ ] Deployed app URL
- [ ] `bob_sessions/` screenshots (solo = at least 1)
- [ ] Problem/Solution ≤500 words + Bob Usage statement ≤500 words
- [ ] Prove on ≥1 REAL open-source GitHub issue
- [ ] Fill the post-hackathon feedback form (the extra $100)
