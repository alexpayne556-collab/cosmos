---
id: ADR-020
title: The Perpetual Calendar
status: ratified
round-of-origin: 12
originator: claude
contributors: []
source: Annex A
---

## Decision
A rolling **60 days** of everything scheduled: earnings, PDUFA/AdComm, FOMC/CPI,
DoD 5 PM awards, lockups, rebalances, conference abstract drops. **Every slot
refills the SAME DAY its event resolves.** Every event carries a **pre-computed
branch table** (beat/miss/inline — who gets paid in each branch, including
second-order names coverage hasn't connected).

The calendar is an **organ with a daily refresh task, never a document.**

## Consequences
When a scheduled catalyst hits, the reaction map already exists. Backed by the
Robinhood earnings calendar + EPS history (MEASURED) and Spark's scheduled
sensing. Build: Week-2.
