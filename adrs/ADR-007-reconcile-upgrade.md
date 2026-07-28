---
id: ADR-007
title: Reconcile upgrade — first-touch on 15s bars (incl. extended session)
status: partial
round-of-origin: PENDING
originator: per-handoff
contributors: []
phase: 3
migration: hermes reconcile.py (ancestor -> descendant)
---

## Context
Hermes' `reconcile.py` grades on *daily* closes from a free web endpoint. The
system needs first-touch resolution on 15-second bars, extended session included,
with proper calibration scoring.

## Decision
A descendant grader (Phase 3) upgrades the ancestor to:
- **first-touch on 15-second bars**, extended session included;
- the **structural gate**: a bar breaching BOTH target and invalidation is
  `AMBIGUOUS_BOTH_TOUCHED` = **loss** (never award the optimistic side). The
  deterministic single-bar rule exists today in `cosmos/grading.py`;
- multi-class **Brier** + **Murphy** decomposition (ADR-008).

`governor.py` and `ledger.py` stay byte-frozen; only this descendant changes.

**Extended-session risk (verified insight, Spark — stands):** LULD halts apply in
regular hours ONLY, so AH/PM sessions lack that circuit breaker. First-touch
grading in the extended session must treat gap-throughs as real — an invalidation
can be breached with no halt to arrest it. This is why AMKR graded LOSS on a Jul-27
extended-session move through its invalidation. (See OQ, Confirmed insights.)

## Status — PARTIAL (blocked spec)
The orchestrator's spec for this upgrade was truncated at
`AMBIGUOUS_BOTH_TOUCHED=loss,` (OQ-RECONCILE-P3). Full point-3 list (move-start/
lag capture, checkpoint match rules) still owed before the full grader is built.
Phase-0 ships the deterministic structural gate + fixture 14.
