---
id: ADR-014
title: LEAD TIME — the headline KPI
status: ratified
round-of-origin: PENDING
originator: per-handoff
contributors: []
---

## Context
The mission is to be *on time* — before the crowd. The single number that
measures the mission must be primary, not buried.

## Decision
**LEAD TIME** (alert/entry time relative to `move_start`, ADR-011) is the
headline KPI on the Scorecard, above Brier and claim-accuracy. Positive lead time
= positioned before the move; negative = chasing. Domain-press → finance-press
lag (ADR-021) is the purchasable lead time the readers harvest.

## Consequences
The system optimizes for earliness, not just accuracy. Displayed on The Wall
(built last); measurable now that `move_start` is a first-class field.
