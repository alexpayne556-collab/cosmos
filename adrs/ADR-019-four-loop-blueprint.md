---
id: ADR-019
title: The Unified Four-Loop Blueprint
status: ratified
round-of-origin: 12
originator: claude
contributors: []
source: Annex A
---

## Decision
The whole system is FOUR concurrent loops on ONE ledger. Every module belongs to
exactly one loop.

- **LOOP 1 · SENSE (24/7)** — world enters as observations, sources attached,
  numbers `PENDING_VERIFY` until the instrument fills them.
- **LOOP 2 · THINK (triggered + scheduled)** — differential state vs open theses
  (including silence — the Non-Reaction Queue), hypothesis generation by ALL
  generators into one frozen schema, red-team objections (graded), collisions
  (ADR-009), decay (ADR-010).
- **LOOP 3 · SURFACE (market hours)** — the 5-alert budget (ADR-012), measured
  WHAT + sourced WHY joined; alert = ledger entry point. The Wall (UI) built
  last: Today queue · Open Theses w/ clocks · Forward Calendar w/ branches ·
  Scorecard (Brier, claim-accuracy, LEAD TIME).
- **LOOP 4 · LEARN (nightly/weekly/monthly)** — reconcile grades; weights update
  per generator × sector × family × regime; precursor autopsy (ADR-024); miss
  ledger + Friday replay (ADR-025) → sensor-gap tickets → Loop 1 grows new
  sensors; monthly regime review + death certificates; backfill flywheel (ADR-027).

## Consequences
Every module has exactly one home loop. This is the top-level map the other ADRs
hang from.
