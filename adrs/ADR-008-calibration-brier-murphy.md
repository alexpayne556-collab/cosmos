---
id: ADR-008
title: Calibration — multi-class Brier + Murphy decomposition
status: ratified
round-of-origin: PENDING
originator: gemini_spark
contributors:
  - name: claude
    role: calibration
phase: 3
---

## Context
A single hit-rate can't tell a well-calibrated forecaster from a lucky one. The
Hermes proof already showed Brier catching overconfidence (0.313 vs 0.500 for
identical picks claiming 60% vs 80%).

## Decision
Score every resolved belief with **multi-class Brier** over the outcome classes,
computed on 15-second bars including the extended session, and decompose via
**Murphy** into reliability − resolution + uncertainty. Calibration feeds the
per-generator × sector × family × regime weight matrix (Loop 4).

## Consequences
Overconfidence is penalized structurally, no human input. Full implementation
lands with the ADR-007 reconcile descendant (Phase 3). Class set and weighting
to finalize with OQ-RECONCILE-P3.
