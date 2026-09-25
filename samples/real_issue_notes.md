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

## Result — python-slugify (real, unfamiliar OSS repo)

Ran Culprit **live** against a real third-party repo it had never seen (`github.com/un33k/python-slugify`,
cloned fresh), pointing `REPO_ROOT` at it. Input: a genuine chained `ModuleNotFoundError` traceback
produced by calling `slugify(b'...')` in an environment without a transliteration backend.

- **Repo:** un33k/python-slugify (shallow clone)
- **Real error:** `ModuleNotFoundError: No module named 'text_unidecode'` (chained from `unidecode`),
  raised in `slugify/_legacy.py::_transliterate` via the auto-backend import fallback.
- **Culprit's winning diagnosis:** the `auto` backend in `_legacy.py` (lines 51–57) tries `unidecode`,
  falls back to `text_unidecode`, and both are absent — a missing **declared** dependency, not a
  code logic bug. It verified against `pyproject.toml` (text-unidecode is a hard dependency) and
  explicitly ruled out the bytes-decoding path and the `error.name` guard as sound.
- **Suggested fix:** `pip install text-unidecode` (the package is declared but not installed).
- **Why this matters:** Culprit correctly *avoided* inventing a code bug and identified the true
  environmental root cause with file/line evidence and a disproof test — the hard case for a triage tool.
- **Cost:** ~1.36 Bobcoins · 8 Bob calls (5 hypotheses + 2 critics + fix) · dual-critic CONFIRMED.
