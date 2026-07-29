from __future__ import annotations

import sqlite3

import pytest

from cosmos import ledger
from cosmos.ingestion.sheets_bridge import SheetsBridgeAdapter, is_prediction_row

DIST = {"hit_target_first": 0.6, "hit_invalidation_first": 0.3, "expire_in_range": 0.1}


def _pred_row(**over):
    r = {"prediction_id": "sheet-1", "generator_id": "gemini_spark", "ticker": "FRO",
         "direction": "up", "offset_target_pct": 5.0, "offset_invalidation_pct": -3.0,
         "distribution": dict(DIST), "thesis": "Hormuz tanker spike", "canon_tags": ["LITERATURE"],
         "source_urls": ["https://x"], "price_mode": "RELATIVE_PCT"}
    r.update(over)
    return r


def _bridge():
    return SheetsBridgeAdapter(ledger.connect(":memory:"), sqlite3.connect(":memory:"))


def test_lane_discriminator():
    assert is_prediction_row(_pred_row()) is True
    assert is_prediction_row({"ticker": "RKLB", "thesis": "catalyst"}) is False  # no distribution


def test_prediction_logged_pending_verify_with_t0_locked():
    b = _bridge()
    r = b.process_staging_rows([_pred_row()])
    assert r == {"rows_processed": 1, "accepted": 1, "observations": 0, "quarantined": 0}
    row = b.ledger.execute(
        "SELECT anchor_close, target_price, invalidation_price, distribution_logged_at "
        "FROM predictions WHERE prediction_id='sheet-1'").fetchone()
    assert row[0] is None and row[1] is None and row[2] is None   # prices PENDING_VERIFY
    assert row[3] is not None                                      # t0 distribution stamp locked
    assert b.ledger.execute(
        "SELECT 1 FROM prediction_distributions WHERE prediction_id='sheet-1' AND seq=0").fetchone()


def test_observation_goes_to_observations_not_ledger():
    b = _bridge()
    r = b.process_staging_rows([{"ticker": "RKLB", "thesis": "Neutron cadence catalyst",
                                 "source_url": "https://spacenews", "category": "CATALYST"}])
    assert r["observations"] == 1 and r["accepted"] == 0
    assert b.ledger.execute("SELECT COUNT(*) FROM predictions").fetchone()[0] == 0   # no ghost prediction
    assert b.obs.execute("SELECT COUNT(*) FROM market_observations").fetchone()[0] == 1


def test_verify_lane_field_stripped_row_still_logs_clean():
    b = _bridge()
    r = b.process_staging_rows([_pred_row(target_price=40.0)])   # generator supplying a verify price
    assert r["accepted"] == 1
    # intake stripped it; the ledger price stays PENDING_VERIFY, not the sheet-supplied 40.0
    assert b.ledger.execute(
        "SELECT target_price FROM predictions WHERE prediction_id='sheet-1'").fetchone()[0] is None


def test_duplicate_rejected_not_double_logged():
    b = _bridge()
    b.process_staging_rows([_pred_row()])
    r2 = b.process_staging_rows([_pred_row()])          # same prediction_id, second poll
    assert r2["quarantined"] == 1 and r2["accepted"] == 0
    assert b.ledger.execute(
        "SELECT COUNT(*) FROM predictions WHERE prediction_id='sheet-1'").fetchone()[0] == 1


def test_missing_distribution_is_observation_not_doomed_prediction():
    b = _bridge()
    row = _pred_row()
    del row["distribution"]
    r = b.process_staging_rows([row])
    assert r["observations"] == 1 and r["accepted"] == 0   # never lands as EXCLUDED_NO_DISTRIBUTION


def test_enrichment_fills_prices_without_altering_t0():
    b = _bridge()
    b.process_staging_rows([_pred_row(prediction_id="sheet-2")])
    before = b.ledger.execute(
        "SELECT ts_logged, distribution_logged_at FROM predictions WHERE prediction_id='sheet-2'").fetchone()
    ok = b.enrich_prediction("sheet-2", anchor_close=38.59,
                             offset_target_pct=5.0, offset_invalidation_pct=-3.0)
    assert ok
    after = b.ledger.execute(
        "SELECT ts_logged, distribution_logged_at, anchor_close, target_price, invalidation_price "
        "FROM predictions WHERE prediction_id='sheet-2'").fetchone()
    assert after[0] == before[0] and after[1] == before[1]     # t0 UNCHANGED — the whole point
    assert after[2] == pytest.approx(38.59)
    assert after[3] == pytest.approx(40.5195) and after[4] == pytest.approx(37.4323)
