---
id: ADR-017
title: Names Law v2 (boards)
status: ratified
round-of-origin: PENDING
originator: gemini_spark
contributors: []
---

## Context
Categories without names are useless at 3 AM. A board that says "tanker
operators benefit" but names no ticker is a scramble, not a lookup.

## Decision
**Names Law v2:** no nameless categories — every tier names real tickers. Board
row contract: `ticker | mechanism one-liner | source URL | canon_tag`. Run
history is **instrument-written ONLY** (verify-station lane, ADR-002);
cause/continuation/provenance are **reader-written with one source URL per
claim**. **Reading-List Law:** every domain board carries its upstream trade
press (space: SpaceNews/Payload/NASASpaceflight; defense: Defense News/Breaking
Defense/Janes; bio: Endpoints/STAT/Fierce; gold: Kitco/Mining.com; semis:
SemiAnalysis/EE Times/TrendForce; energy: Argus/EIA).

Boards use frontmatter `ADR-017_<DOMAIN>_v1.0`. Seeds live in `/boards/` (HORMUZ,
TAIWAN, GOLD, SPACE).

## Consequences
Every board is a lookup with real names + sources. Open: boards carry
descriptive source names, not literal URLs yet (OQ-BOARDS-URLS); HORMUZ shipping
press not enumerated by ADR-021 (OQ-BOARDS-PRESS).
