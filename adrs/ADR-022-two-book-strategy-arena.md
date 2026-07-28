---
id: ADR-022
title: The Two-Book Structure + Strategy Arena
status: ratified
round-of-origin: 12
originator: claude
contributors: []
source: Annex A
---

## Decision
- **FAST BOOK** (≤ 5 trading days): price falsifiers, first-touch on 15s bars,
  high λ.
- **SLOW BOOK** (20–60 trading days): event-predicate falsifiers + wide bands,
  weekly sentinel review, low λ per event type, **separate scorecard**.
- **CHECKPOINT ROWS:** slow theses write gradeable interim checkpoints (T+1w,
  T+2w, T+4w, via ADR-015) so long holds feed weekly volume.
- **`strategy_family`** is a first-class OPEN field — situational (hours–3d),
  swing (3–12d), thesis (20–60d), plus any invented family. Families compete on
  ONE scoreboard; **the ledger breeds strategies.**

## Consequences
Long holds don't go dark for two months; new strategy families can be invented
and earn their place empirically. Decay (ADR-010) differs by book. Analytics:
Week-2.
