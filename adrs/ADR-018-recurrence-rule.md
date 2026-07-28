---
id: ADR-018
title: Recurrence rule (3-in-10) -> serial-runner dossiers
status: ratified
round-of-origin: PENDING
originator: per-handoff
contributors: []
---

## Context
Some names run again and again (RDW, LUNR, ASTS, APLD — Section 5). Catching the
repeat offenders early is a distinct, learnable edge.

## Decision
A ticker appearing in the **daily top-20 gainers ≥ 3 times in a rolling 10-day
window** is flagged a **serial-runner suspect** and gets an auto-dossier. Fed by
the DAILY_GAINERS harvest → dated cohort watchlists → overlap detection (ADR-023),
and by the backfill recurrence scan (ADR-027). Serial-runner is a candidate third
behavioral class beside metronome / powder keg.

## Consequences
Repeat structure surfaces automatically. Exact window semantics to confirm
(OQ-RECURRENCE-1). The `🔁 Serial Runner Suspects` watchlist is live (Section 5).
