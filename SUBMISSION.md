# Submission checklist — IBM Bob 2.0 Hackathon

Deadline: **Sun Sep 27, 2026, 8:00 PM PKT / 11:00 AM ET.**

## Required deliverables (lablab platform)
- [ ] **Public repo** — fork/base off `github.com/watsonxhackathon/ibm-hackathon-template`; keep `.bobignore`.
- [ ] **Project title + short description**
- [ ] **Long description** — problem, target user (on-call dev inheriting a legacy service), how they
      interact, why it's novel. ≤500 words for the Problem/Solution statement.
- [ ] **IBM Bob Usage statement** (≤500 words) — exactly where Bob subagents were used (the race +
      critic), plus how watsonx.ai Granite is used for ranking.
- [ ] **`bob_sessions/`** — task-session summary screenshot(s). Solo = at least 1; grab several.
- [ ] **Public code repo URL**
- [ ] **Deployed application URL** — deploy `ui/server.py` (Render/Railway/HF Spaces).
- [ ] **Cover image**
- [ ] **Video demo** — MP4, **≤3:00** (judges stop at 3:00), **≥90s** showing the solution running,
      narrated, demo up front.
- [ ] **Slide deck** (≈5 slides)
- [ ] **Tech/category tags**

## Winning-move extras
- [ ] Prove on **≥1 real open-source GitHub issue** (see `samples/real_issue_notes.md`).
- [ ] Granite-first (guide penalizes some non-IBM models).
- [ ] **Fill the post-hackathon feedback form** — that's the extra $100.

## Video script (≤3:00)
- 0:00–0:20  the pain: triage, not fixing, is where hours go (on-call persona).
- 0:20–0:35  paste a real stack trace.
- 0:35–2:10  LIVE: 3 hypothesis subagents race → Granite ranks by risk → critic writes a disproof
             test → confirmed diagnosis card + triage timer. (this is the ≥90s on-screen segment)
- 2:10–2:35  the real-GitHub-issue case: Culprit's diagnosis == the accepted fix.
- 2:35–3:00  how Bob's parallel subagents + Granite made it possible; ROI line.

## ⚠️ Safety
- No IBM Cloud credentials in the repo (auto-suspend risk). Verify `.gitignore`/`.bobignore` before
  every push. Run a quick secret scan before submitting.
