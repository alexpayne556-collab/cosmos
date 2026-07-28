---
id: ADR-028
title: The Order Interlock
status: ratified
round-of-origin: 13
originator: claude_code
contributors:
  - name: tyr
    role: ruling (priority-1 reorder)
provoked-by: audit severity finding #1 (LLM->money path had no code interlock)
implemented_in: cosmos/execution/adapter.py, tests/test_order_interlock.py
---

## Context
The audit found the highest-blast-radius risk was latent: the Robinhood MCP
exposes `place_equity_order` / `place_option_order`, reachable by a model, with
no code-level guard forcing sizing through the frozen governor. Discipline is not
an interlock.

## Decision
1. **No language-model output reaches an order endpoint.** No module in `cosmos/`
   may import or call `place_equity_order` / `place_option_order` except a single
   file explicitly named in the interlock allow-list. A test greps the package and
   FAILS if the symbols appear anywhere else. Today the allow-list is empty — no
   live adapter exists.
2. **Execution is human-authorized, deterministic, governed.** Any execution
   adapter (paper or live) must be constructed WITH a governor and must act ONLY
   on `governor.approve()`'s returned size. A test asserts the adapter cannot be
   constructed without a governor instance.
3. **The governor's cap is unmodifiable by any model, prompt, or config.**
   `hermes/governor.py` stays byte-frozen (5% cap, max 3 positions, no scaling
   after wins). Confidence is not an input.

## Consequences
The money path is guarded in code, not just prose. The order symbols appear in
this repo only in tests (searching for them) and ADR text — never in package code.
See [[ADR-029]] (the shadow book runs under the same leash).
