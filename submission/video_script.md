# Culprit — 3-minute video script

Hard rules from the guide: **≤3:00** (judges stop at 3:00), **≥90s** showing the solution running on
screen, narrated, demo up front. Record the demo from the UI (`.\run_ui.ps1`) — it renders cleanly.
Rehearse in **mock mode** (free, instant) until the timing is tight, then record **one live run**.

---

## [0:00–0:20] The pain (talking head or title card)
> "When a service breaks, writing the fix is the easy part. The expensive part is triage — figuring
> out *which* of five plausible causes is the real one, in code you didn't write. Every AI tool today
> jumps straight to a pull request. A fix you can't trust is worse than no fix."

On screen: title "Culprit — verifiable root-cause triage on IBM Bob 2.0".

## [0:20–0:35] Setup
> "Culprit diagnoses *why* it broke — and proves it — before suggesting a fix. Here's a real failure
> from a service I've never seen."

Action: open the UI, click a sample trace (or paste one), hit **Run triage**.

## [0:35–2:05] LIVE demo — the pipeline (this is the ≥90s on-screen segment)
Narrate as it streams:
> "Five independent Bob agents race the same trace, each from a different angle — logic, validation,
> concurrency, and more. They run in parallel and can't see each other."

(cards stream in)
> "watsonx Granite ranks them by risk, not by the agents' own confidence."

(scores populate, winner highlighted)
> "Then two adversarial critics try to *disprove* the leader — one writes a failing test that isolates
> the cause, one hunts for a simpler explanation. The winner survives only if neither refutes it."

(verdict panel: CONFIRMED + disproof test + suggested fix + triage timer)
> "Root cause, evidence, a disproof test, and a fix — in [X] seconds. And it never touched the repo:
> every agent ran in a throwaway sandbox."

## [2:05–2:35] Proof on a real repo
> "Does it work on real code? I pointed it at the open-source python-slugify library with a real
> ModuleNotFoundError. Culprit correctly found a missing declared dependency — and refused to invent a
> code bug, checking the library's logic against pyproject.toml. Not hallucinating is the hard part."

On screen: the slugify diagnosis (or `samples/real_issue_notes.md`).

## [2:35–3:00] How it's built + close
> "Culprit runs entirely on IBM Bob 2.0 — eight Bob agents per triage — with watsonx Granite for
> ranking. It attacks the slowest part of incident response: root-cause triage. Less time reading
> unfamiliar code, lower MTTR, and a human still owns the fix. That's Culprit."

On screen: repo URL + "Built on IBM Bob 2.0 + watsonx Granite".

---

### Recording checklist
- [ ] Zoom the browser to ~110–125% so text is legible in the recording.
- [ ] Use the UI (dark theme) — the CLI shows encoding artifacts on Windows.
- [ ] Do a mock rehearsal, then one live run; keep the best take.
- [ ] Fill the actual triage-time number into the [X] placeholder.
- [ ] Export MP4, verify it's under 3:00 and the demo occupies ≥90s.
