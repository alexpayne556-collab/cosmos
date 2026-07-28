"""
Execution package — the ONLY place a live order adapter may ever live (ADR-028).

Interlock invariants (enforced by tests/test_order_interlock.py):
  * No module in `cosmos/` may import or call the broker's equity/option
    order-placement endpoints except a file explicitly named in the interlock
    allow-list. No such live adapter exists yet. (The endpoint symbols are
    deliberately NOT written anywhere in package code, so the strict grep guard
    stays strict.)
  * Every execution adapter is governor-gated: it cannot be constructed without
    a governor and acts ONLY on `governor.approve()`'s returned size.

Today this package contains only the SHADOW BOOK (ADR-029): fully-agentic PAPER
execution, under the same leash. No language-model output reaches money.
"""
