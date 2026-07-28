---
id: ADR-001
title: Prediction schema v1.0.1 — dual price modes + last-close anchoring
status: ratified
round-of-origin: PENDING
originator: claude
contributors:
  - name: gemini_spark
    role: relative-pct-model
amends: none
migration: hermes ledger.py (ancestor -> descendant)
---

## Context
Hermes' Phase-1 ledger stored a single absolute `entry_price` + `target_move_pct`.
The multi-generator design needs both absolute picks (Claude) and relative-offset
picks (Gemini) in one frozen schema, with a deterministic anchor so RELATIVE_PCT
rows are reproducible.

## Decision
`prediction_row` v1.0.1 (`schemas/prediction_row.schema.json`) supports two
`price_mode`s:
- **ABSOLUTE** — generator gives relative offsets; verify-station writes absolute
  `verified/target/invalidation` from live quotes.
- **RELATIVE_PCT** — offsets anchor **strictly to the last official close
  preceding `release_timestamp_utc`**. `cosmos.verify_intake.anchor_relative()`
  computes the absolutes; generators never write them.

The four live Gemini rows (BA/PYPL/KO/STX) stand anchored to Jul 27 closes; STX
is `ANCHOR_PENDING` to the Jul 28 close (OQ-STX-ANCHOR).

## Migration note (design-inherited / code-new)
The ancestor `ledger.py` is honored for its append-only discipline. The
"duplicate `prediction_id` rejected" contract Section 2 cites is **not** present
in the Phase-1 code (autoincrement `id`, plain INSERT) — it is implemented fresh
in `verify_intake` (design-inherited, code-new). Open: keep in-place resolution
UPDATE or go event-sourced (OQ-LEDGER-APPENDONLY).

## Consequences
Reproducible RELATIVE_PCT grading; a single schema all generators write into.
Full field list + write-authority ownership live in `cosmos/verify_intake.py`.
