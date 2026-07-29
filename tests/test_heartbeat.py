"""Heartbeat liveness beat (scripts/heartbeat.py) — Tyr spec 2026-07-29.

Loaded by path (scripts/ is not a package) so packaging quirks can't hide it.
The load-bearing invariant (spec step 5): running twice appends exactly two rows
and mutates neither. NO_NEW_DATA is a valid result, never an error.
"""
from __future__ import annotations

import importlib.util
import pathlib

from cosmos import ledger, paths

_HB_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "heartbeat.py"
_COLS = "rowid, ts_utc, ledger_rows, resolved, pending, status, note"


def _load_heartbeat():
    spec = importlib.util.spec_from_file_location("heartbeat_under_test", _HB_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)      # FileNotFoundError here == red before the script exists
    return mod


heartbeat = _load_heartbeat()


def _seed(con, pid, *, resolved=0):
    ledger.log_prediction(
        con, prediction_id=pid, ticker="FRO", direction="up", price_mode="RELATIVE_PCT",
        generator_id="gemini_spark",
        distribution={"hit_target_first": 0.6, "hit_invalidation_first": 0.3, "expire_in_range": 0.1})
    if resolved:
        con.execute("UPDATE predictions SET resolved=1 WHERE prediction_id=?", (pid,))
        con.commit()


def test_counts_reflect_ledger():
    con = ledger.connect(":memory:")
    _seed(con, "a", resolved=1)
    _seed(con, "b", resolved=0)
    row = heartbeat.beat(con)
    assert row["ledger_rows"] == 2 and row["resolved"] == 1 and row["pending"] == 1
    assert row["ledger_rows"] == row["resolved"] + row["pending"]   # always reconcile


def test_running_twice_appends_two_rows_mutates_neither():
    con = ledger.connect(":memory:")
    _seed(con, "a", resolved=1)
    _seed(con, "b", resolved=0)
    heartbeat.beat(con)
    snap = con.execute(f"SELECT {_COLS} FROM heartbeat ORDER BY rowid").fetchall()
    assert len(snap) == 1
    heartbeat.beat(con)
    after = con.execute(f"SELECT {_COLS} FROM heartbeat ORDER BY rowid").fetchall()
    assert len(after) == 2            # exactly two rows
    assert after[0] == snap[0]        # first row byte-identical — the second beat mutated nothing


def test_no_new_data_is_valid_not_error_on_empty_ledger():
    con = ledger.connect(":memory:")
    row = heartbeat.beat(con)
    assert row["ledger_rows"] == 0 and row["status"] == "NO_NEW_DATA"   # empty is DATA, not failure


def test_first_beat_is_baseline_then_matured_when_resolved_rises():
    con = ledger.connect(":memory:")
    _seed(con, "a", resolved=0)
    r1 = heartbeat.beat(con)
    assert r1["status"] == "NO_NEW_DATA"        # first beat sets a baseline, not a false MATURED
    con.execute("UPDATE predictions SET resolved=1 WHERE prediction_id='a'")
    con.commit()
    r2 = heartbeat.beat(con)
    assert r2["status"] == "MATURED" and "1 newly resolved" in r2["note"]


def test_main_returns_zero_and_appends_one_row(capsys):
    # conftest isolate_data has already monkeypatched paths.LEDGER_DB to a tmp file
    assert heartbeat.main() == 0                       # exit 0 only on real success
    assert '"status"' in capsys.readouterr().out       # step 4: it prints the row
    con = ledger.connect(paths.LEDGER_DB)
    assert con.execute("SELECT COUNT(*) FROM heartbeat").fetchone()[0] == 1
