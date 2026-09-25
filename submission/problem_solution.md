# Culprit — Problem & Solution statement

_(≤500 words — paste into the lablab "Problem & Solution / Long description" field)_

**The problem.** When a production service breaks, the expensive part isn't writing the fix — it's
the triage. An on-call engineer paged at 2 a.m. against a service they didn't write burns hours
deciding which of several plausible causes is the real one: reading unfamiliar code, forming
hypotheses, ruling them out. Today's AI coding tools skip straight to a patch. IBM Bob, Devin,
Sweep, and Copilot Workspace will all confidently open a pull request — but a fix you can't trust is
worse than no fix, and none of them make the *diagnosis* trustworthy first. So engineers still do the
hard reasoning by hand, and MTTR (mean time to resolution) stays high.

**The solution.** Culprit is a verifiable root-cause **triage** engine built on IBM Bob 2.0 and
watsonx Granite. It diagnoses *why* a failure happens — the fix is a deliberate byproduct, shown only
after the diagnosis survives scrutiny.

Paste a stack trace, failing CI log, or issue, and Culprit runs a four-stage pipeline:

1. **Parallel hypothesis race** — five independent Bob agents attack the same failure at once, each
   from a different angle (logic, input-validation, data/state, concurrency, interface/contract).
   Running in parallel and blind to each other, they surface causes a single pass would miss.
2. **Granite risk-ranking** — watsonx Granite scores each hypothesis by risk and blast-radius, not by
   the agent's self-reported confidence.
3. **Dual adversarial critic** — two more Bob agents *try to disprove* the leading hypothesis (one
   checks isolation, one hunts for a simpler cause) and write a disproof test. The winner survives
   only if neither refutes it.
4. **Diagnosis card** — a ranked, evidence-backed verdict: culprit file/line, the disproof test, and
   a suggested fix.

Everything runs against a **throwaway copy of the repo**, so Bob's agents can never modify the real
working tree — triage is non-destructive by construction.

**Why it's different.** Culprit deliberately does *not* re-wrap Bob's stock quick-fix/PR features.
Its value is the triage *reasoning and verification* layer the autonomous-fixer genre skips. We
proved it on unfamiliar third-party code: pointed at the open-source `python-slugify` repo with a real
`ModuleNotFoundError`, Culprit correctly identified a **missing declared dependency** — and explicitly
refused to invent a code bug, verifying the library's logic against `pyproject.toml`. Not
hallucinating a fix is the hard part, and it passed.

**Impact.** For the on-call engineer and their team, Culprit compresses the slowest, most manual part
of incident response — root-cause triage — from hours of reading unfamiliar code into a minutes-long,
evidence-backed verdict, directly lowering MTTR while keeping a human in control of the fix.
