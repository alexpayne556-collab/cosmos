---
id: ADR-029
title: The Shadow Book (paper execution under the leash)
status: ratified
round-of-origin: 13
originator: tyr
contributors:
  - name: claude_code
    role: implementation
implemented_in: cosmos/execution/adapter.py (PaperExecutionAdapter)
---

## Context
The system must practice execution before it ever executes — but practice that
skips the governor teaches the wrong habit.

## Decision
Paper execution MAY run fully agentic, and **MUST also pass through
`governor.approve()`** — practicing under the leash is the point. The Shadow Book
(`PaperExecutionAdapter`) is governor-gated exactly like a live adapter would be.

**Scoring is separate from prediction Brier.** Paper is graded on its own metrics:
entry slippage vs signal timestamp, max adverse excursion, exit efficiency, and
realized return AFTER governor sizing. These live in `paper_fills`; the
path-dependent ones are filled by a paper reconcile (they need bars) and are
`None` until measured — never guessed.

**The paper->live transition is never automatic and never earned by performance
alone.** It is a written orchestrator decision, per strategy family. No model
proposes its own graduation.

## Consequences
Agentic execution can be exercised safely today. The same governor interlock
(ADR-028) that will gate live orders already gates paper. Metric definitions and
the paper reconcile are follow-on work.
