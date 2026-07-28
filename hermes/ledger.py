"""
HERMES PHASE 1 — THE LEDGER
Permanent memory. Nothing here ever resets.
Tables: predictions, signal_weights, weight_change_log, sizing_log
"""
import sqlite3, time

DB = "hermes.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY,
    ts_logged TEXT NOT NULL,          -- when the prediction was made
    ticker TEXT NOT NULL,
    signal TEXT NOT NULL,             -- which hypothesis/signal produced it
    direction TEXT NOT NULL,          -- 'up' or 'down'
    horizon_days INTEGER NOT NULL,    -- when it matures
    entry_price REAL NOT NULL,        -- price at prediction time
    target_move_pct REAL NOT NULL,    -- what counts as a hit (e.g. 5.0 = +5%)
    stated_confidence REAL NOT NULL,  -- what the signal claimed (0-1)
    reasoning TEXT,                   -- why (audit trail)
    -- filled in by reconciliation:
    resolved INTEGER DEFAULT 0,
    ts_resolved TEXT,
    exit_price REAL,
    realized_move_pct REAL,
    hit INTEGER,                      -- 1/0 after resolution
    brier REAL                        -- (confidence - outcome)^2
);

CREATE TABLE IF NOT EXISTS signal_weights (
    signal TEXT PRIMARY KEY,
    weight REAL NOT NULL DEFAULT 0.5,     -- EWMA hit-rate estimate
    n_resolved INTEGER NOT NULL DEFAULT 0,
    sum_brier REAL NOT NULL DEFAULT 0.0,  -- calibration: lower avg = better
    last_updated TEXT
);

CREATE TABLE IF NOT EXISTS weight_change_log (
    id INTEGER PRIMARY KEY,
    ts TEXT NOT NULL,
    signal TEXT NOT NULL,
    old_weight REAL, new_weight REAL,
    prediction_id INTEGER,            -- which outcome caused the change
    reason TEXT                        -- audit: WHY the mind changed
);

CREATE TABLE IF NOT EXISTS sizing_log (
    id INTEGER PRIMARY KEY,
    ts TEXT NOT NULL,
    ticker TEXT, requested_dollars REAL, approved_dollars REAL,
    rule_applied TEXT                  -- which governor rule fired
);
"""

def connect(db=DB):
    con = sqlite3.connect(db)
    con.executescript(SCHEMA)
    return con

def log_prediction(con, ticker, signal, direction, horizon_days,
                   entry_price, target_move_pct, confidence,
                   reasoning="", ts=None):
    ts = ts or time.strftime("%Y-%m-%d %H:%M:%S")
    cur = con.execute(
        """INSERT INTO predictions
           (ts_logged,ticker,signal,direction,horizon_days,entry_price,
            target_move_pct,stated_confidence,reasoning)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (ts, ticker, signal, direction, horizon_days, entry_price,
         target_move_pct, confidence, reasoning))
    con.execute(
        "INSERT OR IGNORE INTO signal_weights (signal,last_updated) VALUES (?,?)",
        (signal, ts))
    con.commit()
    return cur.lastrowid
