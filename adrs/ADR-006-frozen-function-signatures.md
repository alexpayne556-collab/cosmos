---
id: ADR-006
title: Frozen function signatures
status: ratified
round-of-origin: PENDING
originator: per-handoff
contributors: []
---

## Context
Modules are built across many sessions and partners. Signature drift silently
breaks the loop.

## Decision
The public signatures of load-bearing functions are frozen once ratified; changes
require a superseding ADR. Phase-0 modules expose stable entry points:
`oracle.classify(oas_pct, t10y2y_pct)`, `verify_intake.intake(payload, *, actor,
seen_ids)`, `verify_intake.anchor_relative(anchor_close, off_t, off_i)`,
`checkpoints.evaluate_checkpoint_rule(rule, text)`,
`backoff.compute_delay(profile, attempt, rng)`,
`persistence.atomic_write_bytes(path, data) -> sha256`.

## Consequences
Callers can rely on shape. **PENDING:** the exact frozen-signature manifest from
Gemini's Round-12 package (OQ-ADR-FULLTEXT) — current signatures are the builder's
proposal, subject to ratification.
