# IBM Bob 2.0 Usage statement

_(≤500 words — paste into the lablab "IBM Bob Usage" field)_

IBM Bob 2.0 is the core of Culprit in two distinct ways.

**1. Bob as the runtime engine (the product itself).**
Every triage is powered by Bob Shell. The orchestrator launches Bob agents headlessly via
`bob run --format json`, parsing each task's `last_message` and `session_costs`:

- **Hypothesis race** — five concurrent `bob run` processes, one per investigative angle. Each is an
  independent Bob agent with full repository context, committed to arguing one angle. Parallelism is
  at the process level, which is how Culprit fields a genuine competitive race rather than a single
  linear pass.
- **Dual adversarial critic** — two more Bob agents run in parallel to disprove the winner, each
  writing a concrete disproof test.
- **Suggested fix** — a final Bob agent produces the one-line fix, only after the diagnosis is
  confirmed.

That is **eight Bob calls per triage**. Bob's full-repository context and agentic tool use are what
let each agent read unfamiliar code, quote the offending lines, and justify its hypothesis with
evidence. To keep triage non-destructive, agents run against a throwaway copy of the repo (Bob agent
mode has write tools that would otherwise edit source).

**2. Bob as a coding assistant (building Culprit).**
Bob agent mode authored real parts of this repository: the deployment configuration (Dockerfile,
render.yaml, Procfile), the 25-test orchestrator test suite, and the architecture documentation with
a pipeline diagram — each committed after review.

**watsonx integration.** The ranking stage runs on **watsonx.ai Granite** (`ibm/granite-4-h-small`)
via the text-generation API, scoring hypotheses by risk / blast-radius — a Granite-first, model-graded
second opinion distinct from the agents' self-assessment. If watsonx is unavailable, Culprit degrades
gracefully to a deterministic heuristic so a live demo never breaks.

**Verified usage.** Building and exercising Culprit consumed **19.69 Bobcoins across 125 Bob tasks**
(2.7M context tokens), confirmed in both Bobalytics and Bob's local task store; per-task session
summaries are in [`bob_sessions/`](../bob_sessions/).

Bob 2.0's headless Bob Shell, parallel agents, full-repository context, and agentic tools made it
possible to use Bob not just to write code, but as the reasoning substrate of a new developer tool.
