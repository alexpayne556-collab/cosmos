---
id: ADR-005
title: Capability ledger + nonce proofs
status: ratified
round-of-origin: PENDING
originator: gemini_spark
contributors: []
---

## Context
Claims about what a station *can* do have been wrong before (Section 3 lists
several FAILED capabilities). Capability must be measured, not asserted.

## Decision
A capability is one of **MEASURED / FAILED / CLAIMED**. Nothing load-bears on
CLAIMED. A new capability enters the MEASURED set only via a **nonce proof**
written to the `capability_proofs` tab and verified by human eyes (live example:
nonce `WPK-R5-4c1f9e2a`). The capability ledger is the standing record of these
proofs; `README.md` Section 3 is its human-readable projection.

## Consequences
"Build only on MEASURED" is enforceable, not aspirational. FRED and the Google-
Tasks alert channel remain CLAIMED pending nonce proofs (OQ-FRED-CAP, OQ-GTASKS-CAP).
