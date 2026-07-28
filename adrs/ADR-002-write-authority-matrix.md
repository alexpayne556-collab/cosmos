---
id: ADR-002
title: Write-Authority Matrix (+ Extensions 1-3)
status: ratified
round-of-origin: 3
originator: claude
provoked-by: gemini's round-3 failure (a generator pre-filling verified numbers)
contributors:
  - name: gemini_spark
    role: provoker (authorship via failure)
---

## Context
A generator once pre-filled fields it had no right to author. "Being the failure
that exposed a flaw is also authorship" — this ADR is the fix.

## Decision
Numbers have exactly one author; a belief and its scoring are written by
different hands. Ownership (enforced in `cosmos/verify_intake.py::FIELD_OWNER`):

| Station | May write |
|---------|-----------|
| GENERATOR | direction, relative offsets, distribution (sum 1.0 ± 0.001), thesis, canon tags, source URLs, strategy_family, price_mode |
| VERIFY | absolute verified/target/invalidation, fundamentals (actual + est), float/cap/short-interest, liquidity, **all run dates & magnitudes** |
| ORACLE | regime, asset_class, credit_strain |
| RECONCILE | status, Brier/Murphy, move_start, lag |

**Extensions 1-3:** (1) unauthorized fields are **stripped → forensics →
quarantine**; (2) reason codes `SELF_VERIFIED` / `FUNDAMENTAL_OVERWRITE` /
`CONFABULATED_HISTORY`; (3) the gap is charged pct-normalized to the generator's
claim-accuracy metric.

## Consequences
No station can launder confidence into numbers. Binds every intelligence,
masters' tools included (Section 7). Regression guards: fixtures 2-4 (ADR-016).
