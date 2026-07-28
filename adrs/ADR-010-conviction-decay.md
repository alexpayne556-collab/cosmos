---
id: ADR-010
title: Conviction decay (P_base = ledger class rate, lambda per event type)
status: ratified
round-of-origin: PENDING
originator: per-handoff
contributors: []
---

## Context
A belief written today is not the same belief in three weeks; unrefreshed
conviction should decay toward the base rate, not linger at entry confidence.

## Decision
Conviction decays exponentially toward **P_base = the ledger's realized class
rate** (e.g. the ~30% base rate Hermes discovered for "+5% in 14d" longs), with
decay constant **λ fit per event type**. Fast-book beliefs use high λ; slow-book
beliefs low λ (ADR-022).

## Consequences
Stale beliefs can't masquerade as fresh conviction. λ values and P_base per class
are unfit until the ledger has volume (OQ-DECAY-1). Analytics implementation is
Week-2.
