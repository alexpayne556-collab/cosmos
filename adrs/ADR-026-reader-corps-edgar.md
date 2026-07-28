---
id: ADR-026
title: The Reader Corps (news & catalyst finders)
status: ratified
round-of-origin: 12
originator: gemini_spark
contributors:
  - name: gemini_spark
    role: chatter spec
source: Annex A
implemented_in: cosmos/edgar_poller.py (Drill 3)
---

## Decision
The workers of Loop 1:

- **`edgar_poller.py`** — 15-min RSS, SEC-compliant **declared UA**, ≤ 5 req/sec.
  **Drill 3 (corrected, load-bearing ethics):** on 403/429, honor the block
  completely — exponential backoff w/ full jitter (`SEC_EDGAR_PROFILE`
  30s→2m→10m), then switch to the SEC official **daily bulk index** (`master.idx`),
  alert the human (`SEC_EDGAR_BULK_FALLBACK`). **NEVER rotate identity or spoof
  the UA to evade a block** — the retry and fallback use the SAME UA. Implemented
  + tested (fixture 13). Human channel: local `/data/alerts.jsonl` + Sheet is
  load-bearing; Google-Tasks queue is CLAIMED (OQ-GTASKS-CAP).
- DoD 5 PM contract-award reader · FDA/PDUFA + AdComm reader · dilution radar
  (S-1/S-3/424B) + Form-4 cluster reader · FTD twice-monthly.
- **`chatter_sensor.py`** — Reddit + niche forums. **FIREWALL:** everything lands
  `canon_tag: HYPOTHESIS` + source URL, treated as ATTENTION data (mention
  velocity vs own baseline), **never truth.** Forward-collect from day one.
- Domain sweeps output **BOARD ROWS** (`ticker | mechanism | source URL | tag`),
  never prose.

Readers learn via Loop 4: reaction/non-reaction pairs teach which events matter;
`call_grade_delta` (settle − kneejerk) teaches which words matter. Reader
claim-accuracy is scored forever.

## Consequences
The catalyst-finding workforce, with ethics that are code, not aspiration. EDGAR
Drill 3 ships in Phase 0; the rest are Day-5/Week-2 sensors.
