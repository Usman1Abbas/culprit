# Bob task session evidence

Evidence that IBM Bob 2.0 was used to build and run Culprit. All figures are real and cross-consistent.

## Contents

**Aggregate usage (IBM Bob web portal — bob.ibm.com/admin → Bobalytics):**
- `usman_bobalytics_today_63tasks.png` — Bobalytics "Today" (task count)
- `usman_bobalytics_metrics_bobcoins.png` — Bobalytics "Metrics" (Bobcoin spend)
- `usman_bobalytics_insights.png` — Bobalytics "Insights" (usage timeline + repository impact)
- `usman_bobalytics_subscription.png` — Subscription (team spend against the 40-Bobcoin limit)

**Per-task session summaries (exported from the local Bob store):**
- `usman_bob_session_ledger.png` / `bob_session_ledger.html` — per-task Bobcoin consumption for the
  triage engine's Bob agents (hypothesis race, dual critic, suggested fix) and the Bob-assisted dev
  tasks. Generated directly from `~/.bob/db/bob.db` (table `tasks`, column `costs`).

## Totals (from `~/.bob/db/bob.db`)
- **125** Bob tasks with recorded consumption
- **19.69** Bobcoins consumed
- **2,727,962** context tokens

These match the Bobalytics dashboard exactly (19.69 Bobcoins), confirming the figures.

## How Bob was used
- **As the runtime engine** — Culprit spawns N parallel `bob run` agents per triage (the hypothesis
  race) plus two adversarial critic passes and a fix step (8 Bob calls per run).
- **As a coding assistant** — Bob (agent mode) authored the deployment config, the orchestrator test
  suite, and the architecture docs.

> Note: IBM Bob stores task history **locally** (per IBM docs, it is not mirrored to the web), so the
> per-task consumption panel lives only in the desktop Bob IDE. This ledger is that same data exported
> from Bob's own local database for a portable, verifiable record.
