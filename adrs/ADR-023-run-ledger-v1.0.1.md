---
id: ADR-023
title: Run Ledger v1.0.1 — complete rules
status: ratified
round-of-origin: 12
originator: gemini_spark
contributors:
  - name: claude
    role: end-rules
source: Annex A
schema: schemas/run_ledger.schema.json
---

## Decision
`run_id = sha256(ticker + date + run_scale + start_hour)`.

**End rules:** intraday run ends at the earlier of (50%-retrace-of-peak-gain
sustained 10 min) or session close; multiday run ends on first close below prior
session's low. `run_scale ∈ {INTRADAY, MULTIDAY}`; intraday runs surviving the
close **PROMOTE** to multiday via `parent_run_id`.

**Volume shape** (deterministic, time-terciles): `FRONT_LOADED` > 50% first
tercile; `LATE` > 40% last; else `SUSTAINED`.

**Fields:** `end_timestamp`, `run_duration`, `end_rule_fired`,
`max_drawdown_during_run_pct`, `rel_volume_vs_20d`, precursor snapshot
(float/SI/cap), kneejerk/settle/`call_grade_delta`, `cause_category` +
`source_url` + `flagged_no_cause`.

**Harvest:** DAILY_GAINERS scan → dated cohort watchlists → overlap detection →
ADR-018 recurrence → Serial-Runner dossiers.

## Consequences
Every run is a reproducible, hashed, fully-attributed record. Tercile cuts + the
retrace rule are guessed (OQ-RUNLEDGER-1). `run_ledger.py` = Day-4/backfill.
