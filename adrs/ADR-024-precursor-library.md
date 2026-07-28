---
id: ADR-024
title: The Precursor Library
status: ratified
round-of-origin: 12
originator: claude
contributors: []
source: Annex A
---

## Decision
A daily autopsy of every top gainer's **BEFORE-state, T-1..T-10**: relative-
volume trend, range compression, float & short structure, filing activity,
chatter presence. **Loading signatures measured, not believed.** Backfillable
from bars immediately.

## Consequences
The system learns what "about to run" looks like from evidence, not intuition.
The FRO smoke test already captured the precursor fields (float, cap) the library
needs. `precursor.py` = Day-4; backfill-ready now (ADR-027).
