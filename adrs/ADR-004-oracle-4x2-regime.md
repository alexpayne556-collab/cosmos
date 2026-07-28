---
id: ADR-004
title: Oracle 4x2 regime — FRED credit-strain + curve, HYG-proxy fallback
status: ratified
round-of-origin: PENDING
originator: gemini_spark
contributors: []
implemented_in: cosmos/oracle.py
---

## Context
The desk needs a cheap, deterministic macro stamp on every belief: what regime
were we in when this was written?

## Decision
A 4x2 matrix: **rows** = HY credit-strain band from FRED **BAMLH0A0HYM2** (HY
OAS) → {LOW, NORMAL, ELEVATED, ACUTE}; **cols** = curve state from FRED
**T10Y2Y** → {POSITIVE, INVERTED}. The eight cells map to a regime label +
asset_class tilt (`cosmos/oracle.py::REGIME_MATRIX`). The oracle writes ONLY
`regime / asset_class / credit_strain` (ADR-002).

**Fallback:** FRED is CLAIMED (not in the MEASURED set, OQ-FRED-CAP). When no
`FRED_API_KEY`, `classify_from_hyg()` derives an OAS proxy from HYG behaviour
over MEASURED Robinhood daily historicals. HYG proxy is the load-bearing path.

## Consequences
Deterministic, offline-testable. Thresholds are guessed (OQ-ORACLE-1/2). Until
the oracle runs live, rows are stamped PROVISIONAL by hand (Section 4).
