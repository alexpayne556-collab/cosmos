---
id: ADR-009
title: Collision severity + proximity
status: ratified
round-of-origin: PENDING
originator: gemini_spark
contributors:
  - name: claude
    role: proximity-definition
---

## Context
Two open theses on the same or overlapping catalysts can silently double a bet
or contradict each other. Collisions must be measured.

## Decision
`collision_severity = |P_a − P_b| × Proximity`, where **Proximity = 1** if the
two beliefs share a `trigger_reference`, else the **horizon-overlap fraction**
of their two windows. High-severity collisions surface before entry.

## Consequences
Contradiction and accidental concentration become visible and scored. Exact
horizon-overlap definition to fit (OQ-COLLISION-1). Analytics implementation is
Week-2.
