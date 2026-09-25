# Real-bug proof (the credibility move)

The demo bugs are planted, which judges know is the easy case. To defend Business Value, run Culprit
live on ONE real open-source GitHub issue during the video.

## How to pick a good one (30 min, Saturday)
- A Python repo with a **reproducible bug** and a linked failing test or clear stack trace.
- Small enough that Bob can hold repo context; recent enough to feel real.
- Good sources: GitHub search `label:bug is:issue language:Python` with a traceback in the body;
  the `pytest`, `httpx`, `fastapi`, `requests` issue trackers; or a "good first issue" with a repro.

## What to capture
1. Clone the real repo locally.
2. Set `REPO_ROOT` to it (env var) so the hypothesis subagents read the real code (real mode).
3. Paste the issue's stack trace into Culprit.
4. Record: the hypothesis race, the Granite ranking, the critic's disproof test, the triage time.
5. Compare Culprit's diagnosis to the issue's eventual accepted fix — if they match, that's your
   money shot for the video.

## Fill in once chosen
- Repo:
- Issue #:
- Trace pasted:
- Culprit's top hypothesis:
- Actual accepted fix:
- Match? (Y/N):
- Triage time:
