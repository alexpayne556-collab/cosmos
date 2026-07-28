---
id: ADR-015
title: Checkpoint predicate enum + deterministic match rules (Extension)
status: ratified
round-of-origin: PENDING
originator: gemini_spark
contributors:
  - name: claude
    role: escape/scope/quarantine hardening
implemented_in: cosmos/checkpoints.py
---

## Context
Slow-book theses (ADR-022) write gradeable interim checkpoints. If checkpoint
grading used natural-language judgement, the grader would be non-deterministic
and un-auditable.

## Decision
Checkpoints grade via deterministic string/regex matches over **frozen source
scopes**. `CheckpointMatchRule(predicate_type, source_scope, match_pattern,
case_sensitive=False, is_regex=False)`; `evaluate_checkpoint_rule(rule, text) ->
bool`. Predicate enum: `EDGAR_FILING_CONTAINS`, `NEWS_HEADLINE_MATCH`,
`PRICE_ABOVE`, `PRICE_BELOW`.

**Verify-station hardening (this build):**
- `is_regex=False` (default) literals are `re.escape()`d — "BRK.B" ≠ "BRKXB".
- Invalid regex → quarantined (`INVALID_REGEX`) + WARN alert, treated as
  non-match. **The nightly grading pass never crashes.**
- `source_scope` is **pre-filtered** before evaluation — a headline rule never
  runs against an 8-K, nor vice versa.

## Consequences
NL judgement cannot leak into grading. Regression guards: fixtures 6-8 (ADR-016).
Open: are T+1w/2w/4w interim-checkpoint predicate types owed? (OQ-CHECKPOINT-1).
