---
id: ADR-016
title: Fixtures 1-14 — permanent regression guards
status: ratified
round-of-origin: PENDING
originator: gemini_spark
contributors:
  - name: gemini_spark
    role: fixtures 1-4 (from his own failures)
implemented_in: tests/test_fixtures_01_14.py
---

## Context
Every failure the partners hit in twelve rounds is a mistake the system must
never make silently again. Fixtures 1-4 come from Gemini's own failures.

## Decision
Fixtures 1-14 are permanent regression tests, each pinning a specific failure
mode, asserted against live Phase-0 code (no stubs):
1 sum-to-1 · 2 SELF_VERIFIED · 3 FUNDAMENTAL_OVERWRITE · 4 CONFABULATED_HISTORY ·
5 RELATIVE_PCT last-close anchor · 6 literal-not-regex · 7 invalid-regex
quarantined · 8 scope pre-filter · 9 oracle 4x2 · 10 backoff full-jitter bounds ·
11 atomic persistence + hash · 12 quarantine manifest · 13 no EDGAR identity
rotation · 14 AMBIGUOUS_BOTH_TOUCHED = loss.

## Status
**RECONSTRUCTED** from the constitution's failure fingerprints; pending
ratification against Gemini's exact Round-12 enumeration (OQ-FIXTURES-1). Full
first-touch series grading (beyond the single-bar structural gate) is Phase 3.
