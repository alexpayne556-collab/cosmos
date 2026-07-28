---
id: ADR-027
title: The Backfill Program
status: ratified
round-of-origin: 12
originator: claude
contributors: []
source: Annex A
---

## Decision
**BUILD ITEM #1:** the **90-day top-20-gainers recurrence scan** (universe daily
bars → daily top-20 lists → 3-in-10 repeat offenders (ADR-018) → auto-dossiers).
Then: **6-month catalyst replay** (earnings/FDA/DoD events → measured reactions)
as `generator_id: backfill_historical` — **atlas and lag distributions ONLY,
never Brier** (backfilled beliefs weren't written before the outcome, so they
can't score calibration).

## Consequences
**Volume without waiting** — the ledger gets a history the day it's born, while
keeping the Brier scoreboard honest (only forward beliefs score). Backfillable
immediately from MEASURED daily historicals. This is Day-4 build item #1.
