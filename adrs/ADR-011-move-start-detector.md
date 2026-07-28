---
id: ADR-011
title: Move-start detector v1 (SPIKE + DRIFT triggers)
status: ratified
round-of-origin: PENDING
originator: gemini_spark
contributors: []
note: "absorption-drift trigger"
---

## Context
LEAD TIME (ADR-014) is only measurable if we can pin *when* a move actually
started, separately from when we alerted.

## Decision
Move-start detector v1 fires on either of two triggers, **recording which
fired**:
- **SPIKE** — an abrupt price/volume impulse over the null band.
- **DRIFT** — sustained absorption/directional drift below spike threshold (the
  "absorption-drift" signature).

The detector stamps `move_start` (a RECONCILE-lane field, ADR-002) so lag =
alert_time − move_start is computable.

## Consequences
LEAD TIME becomes measurable and attributable to trigger type. Thresholds ride
the Phase-0-null band (OQ-TRIPWIRE-1); `move_start.py` is Day-5/Phase-5.
