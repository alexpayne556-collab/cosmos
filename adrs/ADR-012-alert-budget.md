---
id: ADR-012
title: 5/day alert budget — ranked W x surprise x decay
status: ratified
round-of-origin: PENDING
originator: per-handoff
contributors: []
---

## Context
An always-on system that alerts on everything trains the human to ignore it.
Attention is the scarcest resource on the desk.

## Decision
At most **5 alerts/day**, ranked by **W × surprise × decay** (W = the
generator/pattern's earned weight; surprise = deviation from expectation; decay =
current conviction per ADR-010). Each alert is a **one-tap capture** into the
ledger — the alert *is* the entry point (Loop 3).

## Consequences
Scarcity forces ranking quality. Ranking weights are unfit (OQ-ALERTS-1). Lives
in Loop 3 / SURFACE; UI (The Wall) is built last.
