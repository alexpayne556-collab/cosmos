---
id: ADR-003
title: Sheets staging protocol — run_id atomicity + COMPLETE terminator
status: ratified
round-of-origin: PENDING
originator: gemini_spark
contributors: []
---

## Context
Spark writes to one Google Sheet; the desk polls read-only. Torn writes and
abandoned runs must be distinguishable from empty ones (Section 8.2).

## Decision
Transport is **Google Sheets staging** (not Drive). Every run carries a `run_id`
and terminates with a `COMPLETE` marker + `row_count`. `sync_staging.py` (Phase 3)
consumes **completed run_ids only**, reads back on every write, and archives each
polled run as raw JSONL to `/data/staging_mirror/` **before** parsing. Local
bookkeeping (`/data/processed_runs.json`) is never written into the Sheet.

Empty/missing behaviors (encoded in `cosmos/alerts.py`): `NO_NEW_DATA` (not an
error), `SETUP_INCOMPLETE` (once/day), incomplete run → skip+count, alert after 3
consecutive incomplete polls; malformed row → quarantine, never crash.

## Consequences
The pipe distinguishes *nothing arrived / arrived broken / pipe down*; only the
last two escalate. Sheet-unreachable backoff = `SHEETS_PROFILE` (30s→2m→8m).
