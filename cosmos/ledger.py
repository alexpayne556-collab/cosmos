"""
Descendant event store (ADR-001 migration; sqlite — measured beats elegant).

Inherits Hermes' append-only discipline and the duplicate-`prediction_id`
rejection contract (design-inherited, code-new). Generator/verify/oracle/
reconcile lanes are filled only by their owners (ADR-002).

ADR-030 (Prior-Commitment Gate): distributions live in an append-only child
table `prediction_distributions`. seq 0 is the t0 commitment Brier scores;
later revisions are retained. Intake stamps `distribution_logged_at` itself —
generators never supply it (that field is stripped + quarantined SELF_STAMPED
at intake).
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Tuple

from . import paths


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


SCHEMA = """
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id TEXT PRIMARY KEY,           -- duplicate rejected
    ts_logged TEXT NOT NULL,                  -- prediction_logged_at
    generator_id TEXT,
    ticker TEXT NOT NULL,
    direction TEXT NOT NULL,                  -- up | down | no_move
    price_mode TEXT NOT NULL,                 -- ABSOLUTE | RELATIVE_PCT
    strategy_family TEXT,
    horizon_days INTEGER,
    distribution TEXT,                        -- JSON latest view (t0 lives in the child table)
    distribution_logged_at TEXT,              -- t0 stamp (intake-written)
    thesis TEXT,
    canon_tags TEXT,
    source_urls TEXT,
    -- verify-station lane (absolute prices; instrument-written):
    anchor_close REAL, entry_price REAL, target_price REAL, invalidation_price REAL,
    expiry_timestamp TEXT,
    -- oracle lane:
    regime TEXT, asset_class TEXT, credit_strain TEXT,
    -- reconcile lane (filled at resolution):
    resolved INTEGER NOT NULL DEFAULT 0, ts_resolved TEXT,
    outcome_class TEXT, first_touch_rule TEXT, settle_price REAL,
    outcome_determined_at TEXT,
    brier REAL, brier_excluded INTEGER NOT NULL DEFAULT 0,
    brier_eligibility TEXT, prior_lag_hours REAL
);
CREATE TABLE IF NOT EXISTS prediction_distributions (
    prediction_id TEXT NOT NULL,
    seq INTEGER NOT NULL,                      -- 0 == t0 commitment (Brier scores this)
    distribution_json TEXT NOT NULL,
    distribution_logged_at TEXT NOT NULL,      -- intake/reconcile stamped, never generator-supplied
    source_station TEXT,
    PRIMARY KEY (prediction_id, seq)
);
CREATE TABLE IF NOT EXISTS weights (
    key TEXT PRIMARY KEY,
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
    """Append a prediction (belief before outcome). Rejects a duplicate
    prediction_id. Writes the distribution as seq 0 of the append-only child
    table, stamping distribution_logged_at itself (ADR-030 R3)."""
    ts = ts or _now_iso()
    if con.execute("SELECT 1 FROM predictions WHERE prediction_id=?", (prediction_id,)).fetchone():
        raise DuplicatePredictionError(prediction_id)
    dist_at = ts if distribution is not None else None
    con.execute(
        "INSERT INTO predictions (prediction_id, ts_logged, generator_id, ticker, direction, "
        "price_mode, strategy_family, horizon_days, distribution, distribution_logged_at, thesis, "
        "canon_tags, source_urls, anchor_close, entry_price, target_price, invalidation_price, "
        "expiry_timestamp, regime, asset_class, credit_strain) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (prediction_id, ts, generator_id, ticker, direction, price_mode, strategy_family,
         horizon_days, json.dumps(distribution) if distribution is not None else None, dist_at,
         thesis, json.dumps(canon_tags or []), json.dumps(source_urls or []),
         anchor_close, entry_price, target_price, invalidation_price, expiry_timestamp,
         regime, asset_class, credit_strain),
    )
    if distribution is not None:
        con.execute(
            "INSERT INTO prediction_distributions (prediction_id, seq, distribution_json, "
            "distribution_logged_at, source_station) VALUES (?,?,?,?,?)",
            (prediction_id, 0, json.dumps(distribution), ts, generator_id),
        )
    con.commit()
    return prediction_id


def revise_distribution(con, prediction_id: str, distribution: dict, *,
                        source_station: Optional[str] = None, ts: Optional[str] = None) -> int:
    """Append a distribution revision (ADR-030 R2). Never mutates seq 0. Returns
    the new seq. Retained for the future revision-skill metric (OQ-REVISION-SKILL)."""
    ts = ts or _now_iso()
    row = con.execute("SELECT MAX(seq) FROM prediction_distributions WHERE prediction_id=?",
                      (prediction_id,)).fetchone()
    next_seq = 0 if row is None or row[0] is None else row[0] + 1
    con.execute(
        "INSERT INTO prediction_distributions (prediction_id, seq, distribution_json, "
        "distribution_logged_at, source_station) VALUES (?,?,?,?,?)",
        (prediction_id, next_seq, json.dumps(distribution), ts, source_station),
    )
    # keep predictions.distribution as the latest view
    con.execute("UPDATE predictions SET distribution=? WHERE prediction_id=?",
                (json.dumps(distribution), prediction_id))
    con.commit()
    return next_seq


def t0_distribution(con, prediction_id: str) -> Tuple[Optional[dict], Optional[str]]:
    """Return the (distribution, distribution_logged_at) of seq 0, or (None, None).
    This is the ONLY distribution Brier scores (ADR-030 R2)."""
    row = con.execute(
        "SELECT distribution_json, distribution_logged_at FROM prediction_distributions "
        "WHERE prediction_id=? AND seq=0", (prediction_id,)).fetchone()
    if not row:
        return None, None
    return json.loads(row[0]), row[1]


def open_predictions(con):
    cols = ("prediction_id", "ts_logged", "generator_id", "ticker", "direction", "price_mode",
            "distribution", "anchor_close", "entry_price", "target_price", "invalidation_price",
            "expiry_timestamp")
    rows = con.execute(f"SELECT {','.join(cols)} FROM predictions WHERE resolved=0").fetchall()
    out = []
    for r in rows:
        d = dict(zip(cols, r))
        d["distribution"] = json.loads(d["distribution"]) if d["distribution"] else None
        out.append(d)
    return out


# --------------------------------------------------------------------------- #
#  GENESIS — the ten Section-5 live rows.                                      #
# --------------------------------------------------------------------------- #
GENESIS_ROWS = [
    ("claude", "gen-cls",  "CLS",  "up",      "ABSOLUTE",     342.50, 360.00, 318.23),
    ("claude", "gen-apld", "APLD", "up",      "ABSOLUTE",      27.80,  29.60,  26.36),
    ("claude", "gen-ne",   "NE",   "down",    "ABSOLUTE",      40.02,  38.00,  41.60),
    ("claude", "gen-cdns", "CDNS", "up",      "ABSOLUTE",     352.25, 362.00, 340.00),
    ("claude", "gen-amkr", "AMKR", "up",      "ABSOLUTE",      60.50,  63.50,  58.50),
    ("claude", "gen-smh",  "SMH",  "up",      "ABSOLUTE",     545.78, 557.00, 536.00),
    ("gemini_spark", "gen-ba",   "BA",   "down", "RELATIVE_PCT", 211.50, 198.81, 217.85),
    ("gemini_spark", "gen-pypl", "PYPL", "up",   "RELATIVE_PCT",  56.07,  61.12,  53.27),
    ("gemini_spark", "gen-ko",   "KO",   "no_move", "RELATIVE_PCT", 84.07, None, None),
    ("gemini_spark", "gen-stx",  "STX",  "up",   "RELATIVE_PCT", None,   None,  None),
]

# Ratified generator distributions (delivered 2026-07-28). Bucket schema
# {hit_target_first, hit_invalidation_first, expire_in_range}. Only 6 of 10 rows
# covered; CLS/NE/CDNS/SMH have none. Per ADR-030 these are dispositioned by the
# gate (AMKR -> EXCLUDED_POST_HOC as its distribution was written after the breach).
GENESIS_DISTRIBUTIONS = {
    "AMKR": {"hit_target_first": 0.58, "hit_invalidation_first": 0.27, "expire_in_range": 0.15},
    "APLD": {"hit_target_first": 0.58, "hit_invalidation_first": 0.27, "expire_in_range": 0.15},
    "BA":   {"hit_target_first": 0.55, "hit_invalidation_first": 0.30, "expire_in_range": 0.15},
    "PYPL": {"hit_target_first": 0.58, "hit_invalidation_first": 0.27, "expire_in_range": 0.15},
    "KO":   {"hit_target_first": 0.20, "hit_invalidation_first": 0.20, "expire_in_range": 0.60},
    "STX":  {"hit_target_first": 0.62, "hit_invalidation_first": 0.23, "expire_in_range": 0.15},
}
# Supplied in the same drop but attached to NO prediction row (OQ-UNATTACHED-PRIORS).
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
                distribution=GENESIS_DISTRIBUTIONS.get(ticker),   # seq 0 via t0 path; 6/10 covered
                thesis="Section-5 live-state import (GENESIS)",
                canon_tags=["GENESIS"], source_urls=[],
                anchor_close=(entry if mode == "RELATIVE_PCT" else None),
                entry_price=(entry if mode == "ABSOLUTE" else None),
                target_price=target, invalidation_price=inval,
                expiry_timestamp=None,
            )
            n += 1
        except DuplicatePredictionError:
            pass
    return n
