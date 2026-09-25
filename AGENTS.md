# AGENTS.md — context for Bob

This repo is **Culprit**, a root-cause triage engine built for the IBM Bob 2.0 Hackathon.

## What Bob is used for here (the distinctive, non-stock use)
Bob Shell drives a **multi-agent triage race**. Parallelism is at the process level: the
orchestrator launches N concurrent `bob run` processes, each an independent Bob agent on a
different root-cause angle (Bob's own auto-spawned subagents are model-decided and not forced here):
- `orchestrator/hypotheses.py` runs N parallel `bob run` agents, one per angle
  (see `orchestrator/prompts/hypothesis_agent.md`).
- `orchestrator/critic.py` runs an adversarial `bob run` agent that tries to disprove the winner
  (`orchestrator/prompts/critic_agent.md`).
- Ranking runs on **watsonx.ai Granite** via REST (`orchestrator/granite.py`) — the Granite-first
  stage (Bob Shell cannot pin a model, so ranking is done directly on Granite).

This is deliberately NOT Bob's stock quick-fix / PR generation. The value is the triage reasoning
+ verification layer.

## Conventions
- Every subagent returns a single JSON object (schemas in `orchestrator/schema.py`).
- Keep `MOCK_MODE=1` during development; only flip to `0` for final captures (Bobcoin budget = 40).
- Never commit credentials. `.bobignore` and `.gitignore` exclude `.env` and secrets.

## The "patient"
`demo_app/` is a small FastAPI service with three intentionally planted bugs and a failing pytest
suite — the controlled stage for the demo. Do not "fix" it silently; the failing tests are the demo.
