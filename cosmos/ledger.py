"""
Descendant event store (ADR-001 migration; sqlite — measured beats elegant).

Inherits Hermes' append-only discipline and the duplicate-`prediction_id`
rejection CONTRACT (design-inherited, code-new — the ancestor never implemented
it). Generator/verify/oracle/reconcile lanes are filled only by their owners
(ADR-002). Resolution is an in-place UPDATE of the reconcile lane
(OQ-LEDGER-APPENDONLY: revisit event-sourcing later).
"""
from __future__ import annotations

import json
import sqlite3
import time
from typing import Optional

from . import paths

SCHEMA = """
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id TEXT PRIMARY KEY,           -- duplicate rejected
    ts_logged TEXT NOT NULL,
    generator_id TEXT,
    ticker TEXT NOT NULL,
    direction TEXT NOT NULL,                  -- up | down | no_move
    price_mode TEXT NOT NULL,                 -- ABSOLUTE | RELATIVE_PCT
    strategy_family TEXT,
    horizon_days INTEGER,
    distribution TEXT,                        -- JSON {up,down,no_move}; NULL if generator omitted
    thesis TEXT,
    canon_tags TEXT,                          -- JSON
    source_urls TEXT,                         -- JSON
    -- verify-station lane (absolute prices; instrument-written):
    anchor_close REAL, entry_price REAL, target_price REAL, invalidation_price REAL,
    expiry_timestamp TEXT,
    -- oracle lane:
    regime TEXT, asset_class TEXT, credit_strain TEXT,
    -- reconcile lane (filled at resolution):
    resolved INTEGER NOT NULL DEFAULT 0, ts_resolved TEXT,
    outcome_class TEXT, first_touch_rule TEXT, settle_price REAL,
    brier REAL, brier_excluded INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS weights (
    key TEXT PRIMARY KEY,                     -- generator_id (extendable to generator x class)
    weight REAL NOT NULL DEFAULT 0.5,
    n_resolved INTEGER NOT NULL DEFAULT 0,
    sum_brier REAL NOT NULL DEFAULT 0.0,
    last_updated TEXT
);
CREATE TABLE IF NOT EXISTS weight_change_log (
    id INTEGER PRIMARY KEY, ts TEXT, key TEXT,
    old_weight REAL, new_weight REAL, prediction_id TEXT, reason TEXT
);
"""


class DuplicatePredictionError(Exception):
    pass


def connect(db=None) -> sqlite3.Connection:
    con = sqlite3.connect(str(db) if db is not None else str(paths.LEDGER_DB))
    con.executescript(SCHEMA)
    return con


def log_prediction(con, *, prediction_id: str, ticker: str, direction: str, price_mode: str,
                   generator_id: Optional[str] = None, strategy_family: Optional[str] = None,
                   horizon_days: Optional[int] = None, distribution: Optional[dict] = None,
                   thesis: Optional[str] = None, canon_tags=None, source_urls=None,
                   anchor_close: Optional[float] = None, entry_price: Optional[float] = None,
                   target_price: Optional[float] = None, invalidation_price: Optional[float] = None,
                   expiry_timestamp: Optional[str] = None, regime: Optional[str] = None,
                   asset_class: Optional[str] = None, credit_strain: Optional[str] = None,
                   ts: Optional[str] = None) -> str:
    """Append a prediction. Rejects a duplicate prediction_id (the design-inherited
    contract). Belief written BEFORE the outcome — reconcile fills the rest."""
    ts = ts or time.strftime("%Y-%m-%d %H:%M:%S")
    if con.execute("SELECT 1 FROM predictions WHERE prediction_id=?", (prediction_id,)).fetchone():
        raise DuplicatePredictionError(prediction_id)
    con.execute(
        "INSERT INTO predictions (prediction_id, ts_logged, generator_id, ticker, direction, "
        "price_mode, strategy_family, horizon_days, distribution, thesis, canon_tags, source_urls, "
        "anchor_close, entry_price, target_price, invalidation_price, expiry_timestamp, "
        "regime, asset_class, credit_strain) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (prediction_id, ts, generator_id, ticker, direction, price_mode, strategy_family,
         horizon_days, json.dumps(distribution) if distribution is not None else None, thesis,
         json.dumps(canon_tags or []), json.dumps(source_urls or []),
         anchor_close, entry_price, target_price, invalidation_price, expiry_timestamp,
         regime, asset_class, credit_strain),
    )
    con.commit()
    return prediction_id


def open_predictions(con):
    cols = ("prediction_id", "generator_id", "ticker", "direction", "price_mode", "distribution",
            "anchor_close", "entry_price", "target_price", "invalidation_price", "expiry_timestamp")
    rows = con.execute(f"SELECT {','.join(cols)} FROM predictions WHERE resolved=0").fetchall()
    out = []
    for r in rows:
        d = dict(zip(cols, r))
        d["distribution"] = json.loads(d["distribution"]) if d["distribution"] else None
        out.append(d)
    return out


# --------------------------------------------------------------------------- #
#  GENESIS — import the ten Section-5 live rows (first boot). Absolute prices  #
#  are instrument-written (Round 12). Distributions were NOT supplied by the   #
#  generators -> NULL (write-authority: the verify station will not fabricate  #
#  a generator's probability vector). See OQ-GENESIS-DISTRIBUTIONS.            #
# --------------------------------------------------------------------------- #
GENESIS_ROWS = [
    # generator, id, ticker, direction, price_mode, entry/anchor, target, invalidation
    ("claude", "gen-cls",  "CLS",  "up",      "ABSOLUTE",     342.50, 360.00, 318.23),
    ("claude", "gen-apld", "APLD", "up",      "ABSOLUTE",      27.80,  29.60,  26.36),
    ("claude", "gen-ne",   "NE",   "down",    "ABSOLUTE",      40.02,  38.00,  41.60),
    ("claude", "gen-cdns", "CDNS", "up",      "ABSOLUTE",     352.25, 362.00, 340.00),
    ("claude", "gen-amkr", "AMKR", "up",      "ABSOLUTE",      60.50,  63.50,  58.50),
    ("claude", "gen-smh",  "SMH",  "up",      "ABSOLUTE",     545.78, 557.00, 536.00),
    ("gemini_spark", "gen-ba",   "BA",   "down", "RELATIVE_PCT", 211.50, 198.81, 217.85),
    ("gemini_spark", "gen-pypl", "PYPL", "up",   "RELATIVE_PCT",  56.07,  61.12,  53.27),
    ("gemini_spark", "gen-ko",   "KO",   "no_move", "RELATIVE_PCT", 84.07, None, None),  # band 81.97-86.17
    ("gemini_spark", "gen-stx",  "STX",  "up",   "RELATIVE_PCT", None,   None,  None),   # ANCHOR_PENDING Jul 28 close
]


# Ratified generator distributions (OQ-GENESIS-DISTRIBUTIONS), delivered 2026-07-28.
# Direction-agnostic schema {hit_target_first, hit_invalidation_first, expire_in_range},
# sum == 1.00. VERIFY-STATION NOTE: the drop covered only 6 of the 10 GENESIS rows;
# CLS / NE / CDNS / SMH still have NO distribution and cannot score Brier
# (OQ-GENESIS-DISTRIBUTIONS-MISSING4 — the verify station will not fabricate them).
GENESIS_DISTRIBUTIONS = {
    "AMKR": {"hit_target_first": 0.58, "hit_invalidation_first": 0.27, "expire_in_range": 0.15},
    "APLD": {"hit_target_first": 0.58, "hit_invalidation_first": 0.27, "expire_in_range": 0.15},
    "BA":   {"hit_target_first": 0.55, "hit_invalidation_first": 0.30, "expire_in_range": 0.15},
    "PYPL": {"hit_target_first": 0.58, "hit_invalidation_first": 0.27, "expire_in_range": 0.15},
    "KO":   {"hit_target_first": 0.20, "hit_invalidation_first": 0.20, "expire_in_range": 0.60},
    "STX":  {"hit_target_first": 0.62, "hit_invalidation_first": 0.23, "expire_in_range": 0.15},
}
# Supplied in the same drop but attached to NO prediction row (board names + names
# not in Section 5). Retained as priors only; they score nothing until a belief exists.
UNATTACHED_PRIORS = {
    "FRO":  {"hit_target_first": 0.60, "hit_invalidation_first": 0.25, "expire_in_range": 0.15},
    "INSW": {"hit_target_first": 0.58, "hit_invalidation_first": 0.27, "expire_in_range": 0.15},
    "KTOS": {"hit_target_first": 0.55, "hit_invalidation_first": 0.30, "expire_in_range": 0.15},
    "ASTS": {"hit_target_first": 0.62, "hit_invalidation_first": 0.23, "expire_in_range": 0.15},
    "RKLB": {"hit_target_first": 0.60, "hit_invalidation_first": 0.25, "expire_in_range": 0.15},
    "LUNR": {"hit_target_first": 0.56, "hit_invalidation_first": 0.29, "expire_in_range": 0.15},
    "AEM":  {"hit_target_first": 0.57, "hit_invalidation_first": 0.28, "expire_in_range": 0.15},
    "FNV":  {"hit_target_first": 0.55, "hit_invalidation_first": 0.30, "expire_in_range": 0.15},
    "NEM":  {"hit_target_first": 0.54, "hit_invalidation_first": 0.31, "expire_in_range": 0.15},
    "UHS":  {"hit_target_first": 0.52, "hit_invalidation_first": 0.33, "expire_in_range": 0.15},
    "NXPI": {"hit_target_first": 0.56, "hit_invalidation_first": 0.29, "expire_in_range": 0.15},
    "KLAC": {"hit_target_first": 0.60, "hit_invalidation_first": 0.25, "expire_in_range": 0.15},
    "ENPH": {"hit_target_first": 0.55, "hit_invalidation_first": 0.30, "expire_in_range": 0.15},
    "F":    {"hit_target_first": 0.20, "hit_invalidation_first": 0.20, "expire_in_range": 0.60},
}


def genesis_import(con) -> int:
    n = 0
    for gen, pid, ticker, direction, mode, entry, target, inval in GENESIS_ROWS:
        try:
            log_prediction(
                con, prediction_id=pid, ticker=ticker, direction=direction, price_mode=mode,
                generator_id=gen, strategy_family="genesis",
                distribution=GENESIS_DISTRIBUTIONS.get(ticker),  # 6/10 covered; rest NULL (flagged)
                thesis="Section-5 live-state import (GENESIS)",
                canon_tags=["GENESIS"], source_urls=[],
                anchor_close=(entry if mode == "RELATIVE_PCT" else None),
                entry_price=(entry if mode == "ABSOLUTE" else None),
                target_price=target, invalidation_price=inval,
                expiry_timestamp=None,  # horizons unspecified in Section 5
            )
            n += 1
        except DuplicatePredictionError:
            pass  # idempotent re-import
    return n
