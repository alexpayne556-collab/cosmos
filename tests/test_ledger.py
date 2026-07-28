from __future__ import annotations

import pytest

from cosmos import ledger


def test_log_and_reject_duplicate():
    con = ledger.connect(":memory:")
    ledger.log_prediction(con, prediction_id="p1", ticker="FRO", direction="up",
                          price_mode="RELATIVE_PCT", generator_id="gemini_spark",
                          distribution={"up": 0.6, "down": 0.3, "no_move": 0.1},
                          target_price=40.5, invalidation_price=37.4)
    with pytest.raises(ledger.DuplicatePredictionError):
        ledger.log_prediction(con, prediction_id="p1", ticker="FRO", direction="up",
                              price_mode="RELATIVE_PCT")


def test_open_predictions_parses_distribution():
    con = ledger.connect(":memory:")
    ledger.log_prediction(con, prediction_id="p2", ticker="X", direction="up",
                          price_mode="ABSOLUTE", distribution={"up": 1.0, "down": 0.0, "no_move": 0.0})
    ops = ledger.open_predictions(con)
    assert ops[0]["distribution"] == {"up": 1.0, "down": 0.0, "no_move": 0.0}


def test_genesis_import_idempotent_and_complete():
    con = ledger.connect(":memory:")
    assert ledger.genesis_import(con) == 10        # ten Section-5 rows
    assert ledger.genesis_import(con) == 0         # re-import is a no-op (dup rejected)
    amkr = con.execute(
        "SELECT direction, target_price, invalidation_price, distribution "
        "FROM predictions WHERE ticker='AMKR'").fetchone()
    assert amkr[0] == "up" and amkr[1] == 63.5 and amkr[2] == 58.5
    assert amkr[3] is None                          # generator distribution NOT fabricated
