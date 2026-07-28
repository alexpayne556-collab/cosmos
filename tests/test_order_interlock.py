"""ADR-028 — the money-path interlock is enforced here, not merely promised."""
from __future__ import annotations

import pytest

from cosmos import paths
from cosmos.execution.adapter import (
    PaperExecutionAdapter, open_shadow_book, load_hermes_governor,
)

# The order-endpoint symbols. If a live adapter is ever built, name its file here.
ORDER_SYMBOLS = ("place_equity_order", "place_option_order")
INTERLOCK_ALLOWLIST = set()  # empty: no live adapter exists yet


def test_no_order_endpoint_reference_in_package():
    pkg = paths.REPO_ROOT / "cosmos"
    offenders = []
    for p in pkg.rglob("*.py"):
        rel = p.relative_to(paths.REPO_ROOT).as_posix()
        if rel in INTERLOCK_ALLOWLIST:
            continue
        text = p.read_text(encoding="utf-8")
        for sym in ORDER_SYMBOLS:
            if sym in text:
                offenders.append((rel, sym))
    assert offenders == [], f"order endpoint referenced outside allow-list: {offenders}"


def test_adapter_cannot_be_built_without_governor():
    con = open_shadow_book(":memory:")
    with pytest.raises(ValueError):
        PaperExecutionAdapter(governor=None, con=con, bankroll=296.0)


def test_adapter_acts_only_on_governor_size():
    class CappingGovernor:
        def approve(self, con, ticker, requested, bankroll, open_n, last=None):
            approved = min(requested, 14.0)
            con.execute(
                "INSERT INTO sizing_log (ts,ticker,requested_dollars,approved_dollars,rule_applied)"
                " VALUES (?,?,?,?,?)", ("t", ticker, requested, approved, "CAPPED"))
            con.commit()
            return approved, "CAPPED"

    con = open_shadow_book(":memory:")
    adapter = PaperExecutionAdapter(CappingGovernor(), con, 296.0)
    fill = adapter.submit_paper("BBAI", 148.0, 0)
    assert fill.approved_dollars == 14.0            # acted on approved, NOT the $148 ask
    assert fill.requested_dollars == 148.0


def test_real_frozen_governor_gates_the_shadow_book():
    gov = load_hermes_governor()                    # the byte-frozen 5% governor
    con = open_shadow_book(":memory:")
    adapter = PaperExecutionAdapter(gov, con, 296.0)  # 5% cap = $14.80
    fill = adapter.submit_paper("KTOS", 148.0, 1, last_approved=14.0)
    assert fill.approved_dollars <= 14.8            # half-the-house ask blocked by the frozen cap
    # and a 4th position is rejected outright
    fill4 = adapter.submit_paper("FRO", 14.0, 3, last_approved=14.0)
    assert fill4.approved_dollars == 0.0
