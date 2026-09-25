# Culprit — slide deck outline (5 slides)

Keep it to 5 slides; judges skim. Dark theme, one idea per slide, mirror the UI's look.

## Slide 1 — Title
- **Culprit** — verifiable root-cause triage for inherited code
- Built on IBM Bob 2.0 + watsonx Granite
- One-line: "Diagnoses *why* it broke — and proves it — before suggesting a fix."
- Your name / handle · repo URL

## Slide 2 — The problem
- Fixing is easy; **triage is expensive** — deciding which of several causes is real, in unfamiliar code.
- Every AI tool jumps to a PR. A fix you can't trust is worse than no fix.
- Metric that hurts: **MTTR** (mean time to resolution) stays high because triage is manual.

## Slide 3 — The solution (the pipeline)
Diagram (reuse `docs/ARCHITECTURE.md` mermaid):
1. Parallel hypothesis race — 5 independent Bob agents, different angles
2. watsonx Granite risk-ranking
3. Dual adversarial critic — disprove the winner (writes a disproof test)
4. Diagnosis card — culprit file/line + evidence + fix (byproduct)
- Non-destructive: runs in a throwaway sandbox.

## Slide 4 — Proof it's real (not a demo trick)
- Live red→green pipeline in seconds (screenshot of the verdict card).
- **Real unfamiliar repo:** python-slugify `ModuleNotFoundError` → correctly identified a *missing
  declared dependency*, refused to invent a code bug (verified vs pyproject.toml).
- Evidence: 125 Bob tasks · 19.69 Bobcoins · dual-critic CONFIRMED.

## Slide 5 — Impact + how it uses Bob
- **Business value:** compresses root-cause triage from hours → minutes; lowers MTTR; human owns the fix.
- **Distinctive Bob use:** 8 Bob agents per triage (race + dual critic + fix), full-repo context, Bob
  Shell headless; Granite for model-graded ranking. Not a wrapper on Bob's stock fix/PR.
- Close: repo URL + deployed app URL.

---
Tip: export slide visuals from the actual UI screenshots so the deck and demo feel like one product.
