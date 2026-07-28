"""
Execution interlock + Shadow Book (ADR-028 / ADR-029).

The frozen hermes governor is the ONLY authority on HOW MUCH. Every adapter —
paper today, live if ever — must be constructed WITH a governor and must act
ONLY on the size `governor.approve()` returns. Confidence is not an input; the
cap is unmodifiable by any model, prompt, or config.
"""
from __future__ import annotations

import sqlite3
import sys
import time
from dataclasses import dataclass
from typing import Any, Optional

from .. import paths


def load_hermes_governor():
    """Import the FROZEN governor from /hermes without modifying it. The governor
    imports `ledger` flat, so /hermes goes on sys.path. No side effects at import."""
    hermes_dir = paths.REPO_ROOT / "hermes"
    if str(hermes_dir) not in sys.path:
        sys.path.insert(0, str(hermes_dir))
    import governor  # noqa: E402  (frozen module, byte-identical to the vault)
    return governor


SHADOW_SCHEMA = """
CREATE TABLE IF NOT EXISTS sizing_log (
    id INTEGER PRIMARY KEY, ts TEXT, ticker TEXT,
    requested_dollars REAL, approved_dollars REAL, rule_applied TEXT
);
CREATE TABLE IF NOT EXISTS paper_fills (
    id INTEGER PRIMARY KEY, ts TEXT, ticker TEXT, side TEXT,
    requested_dollars REAL, approved_dollars REAL, rule_applied TEXT,
    signal_ts TEXT, signal_price REAL, fill_price REAL, entry_slippage_pct REAL,
    -- path-dependent metrics, filled by the paper reconcile (need bars): None until then
    realized_return_pct REAL, max_adverse_excursion_pct REAL, exit_efficiency_pct REAL
);
"""


def open_shadow_book(db_path=None) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path) if db_path is not None else str(paths.SHADOW_BOOK_DB))
    con.executescript(SHADOW_SCHEMA)
    return con


@dataclass
class PaperFill:
    ticker: str
    approved_dollars: float          # the ONLY size acted on — governor's word
    rule: str
    requested_dollars: Optional[float] = None
    signal_ts: Optional[str] = None
    signal_price: Optional[float] = None
    fill_price: Optional[float] = None
    entry_slippage_pct: Optional[float] = None
    # scored separately from Brier, by the paper reconcile (ADR-029). None until measured.
    realized_return_pct: Optional[float] = None
    max_adverse_excursion_pct: Optional[float] = None
    exit_efficiency_pct: Optional[float] = None


class PaperExecutionAdapter:
    """ADR-029 Shadow Book. Fully agentic PAPER execution — practicing under the
    leash is the point. MUST pass through governor.approve() and act ONLY on the
    returned size. Scored on paper metrics (slippage / MAE / exit efficiency /
    realized return after governor sizing), NEVER on prediction Brier. The
    paper->live transition is a written orchestrator decision per strategy family,
    never automatic, never proposed by a model."""

    def __init__(self, governor: Any, con: sqlite3.Connection, bankroll: float):
        if governor is None:
            raise ValueError(
                "PaperExecutionAdapter requires a governor — the leash is not optional (ADR-028)"
            )
        if not hasattr(governor, "approve"):
            raise TypeError("governor must expose approve() — pass the frozen hermes governor")
        self.governor = governor
        self.con = con
        self.bankroll = bankroll

    def submit_paper(self, ticker: str, requested_dollars: float, open_positions: int, *,
                     last_approved: Optional[float] = None,
                     signal_ts: Optional[str] = None,
                     signal_price: Optional[float] = None,
                     fill_price: Optional[float] = None,
                     side: str = "buy") -> PaperFill:
        # THE interlock: size is whatever the governor returns — never the ask.
        approved, rule = self.governor.approve(
            self.con, ticker, requested_dollars, self.bankroll, open_positions, last_approved
        )
        slippage = None
        if signal_price and fill_price and signal_price > 0:
            slippage = round((fill_price - signal_price) / signal_price * 100.0, 4)
        fill = PaperFill(
            ticker=ticker, approved_dollars=approved, rule=rule,
            requested_dollars=requested_dollars, signal_ts=signal_ts,
            signal_price=signal_price, fill_price=fill_price, entry_slippage_pct=slippage,
        )
        self.con.execute(
            "INSERT INTO paper_fills (ts,ticker,side,requested_dollars,approved_dollars,"
            "rule_applied,signal_ts,signal_price,fill_price,entry_slippage_pct) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (time.strftime("%Y-%m-%d %H:%M:%S"), ticker, side, requested_dollars, approved,
             rule, signal_ts, signal_price, fill_price, slippage),
        )
        self.con.commit()
        return fill
