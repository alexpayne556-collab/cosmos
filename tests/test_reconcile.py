from __future__ import annotations

import pytest

from cosmos import ledger, reconcile, verify_intake as vi


def _bar(hi, lo, close):
    return {"high_price": str(hi), "low_price": str(lo), "close_price": str(close),
            "begins_at": "2026-07-27T14:00:00Z"}


# ---- first-touch -----------------------------------------------------------
AT = "2026-07-27T14:00:00Z"   # the _bar timestamp -> outcome_determined_at


def test_first_touch_target_first_long():
    assert reconcile.first_touch("up", [_bar(64, 62, 63.8)], 63.5, 58.5) == ("up", "TARGET_FIRST", AT)


def test_first_touch_invalidation_first_long():
    assert reconcile.first_touch("up", [_bar(60, 58, 58.2)], 63.5, 58.5) == ("down", "INVALIDATION_FIRST", AT)


def test_first_touch_ambiguous_is_loss():
    assert reconcile.first_touch("up", [_bar(64, 58, 60)], 63.5, 58.5) == ("down", "AMBIGUOUS_BOTH_TOUCHED", AT)


def test_first_touch_short_direction():
    assert reconcile.first_touch("down", [_bar(39, 37, 37.5)], 38.0, 41.6) == ("down", "TARGET_FIRST", AT)
    assert reconcile.first_touch("down", [_bar(42, 40, 41.5)], 38.0, 41.6) == ("up", "INVALIDATION_FIRST", AT)


def test_first_touch_pending():
    assert reconcile.first_touch("up", [_bar(61, 59, 60)], 63.5, 58.5) == (None, "PENDING", None)


# ---- Brier + Murphy --------------------------------------------------------
def _dist(a, b, c):
    return {"hit_target_first": a, "hit_invalidation_first": b, "expire_in_range": c}


def test_multiclass_brier_bounds():
    assert reconcile.multiclass_brier(_dist(1.0, 0.0, 0.0), "hit_target_first") == 0.0
    assert reconcile.multiclass_brier(_dist(0.0, 1.0, 0.0), "hit_target_first") == 2.0
    assert reconcile.multiclass_brier(_dist(0.6, 0.3, 0.1), "hit_target_first") == pytest.approx(0.26)


def test_amkr_like_invalidation_brier():
    pred = {"generator_id": "claude", "direction": "up",
            "distribution": _dist(0.58, 0.27, 0.15),
            "target_price": 63.5, "invalidation_price": 58.5}
    r = reconcile.grade(pred, [_bar(60.72, 54.92, 55.18)])   # extended breach of 58.5
    assert r.outcome_class == "down" and r.first_touch_rule == "INVALIDATION_FIRST"
    assert r.brier == pytest.approx(0.58 ** 2 + (0.27 - 1) ** 2 + 0.15 ** 2)  # ~0.8918


def test_murphy_identity_holds():
    pairs = [(round(0.1 * (i % 5 + 1), 2), i % 2) for i in range(20)]  # n=20, 5 distinct forecasts
    d, reason = reconcile.murphy_decomposition(pairs)
    assert d is not None
    mse = sum((p - y) ** 2 for p, y in pairs) / len(pairs)
    assert d["brier"] == pytest.approx(mse)
    assert d["brier"] == pytest.approx(d["reliability"] - d["resolution"] + d["uncertainty"])


# ---- grade exclusions ------------------------------------------------------
def test_expired_no_entry_excluded():
    pred = {"generator_id": "g", "direction": "up", "distribution": {"up": 1, "down": 0, "no_move": 0},
            "target_price": 10, "invalidation_price": 8}
    r = reconcile.grade(pred, [], entry_triggered=False)
    assert r.first_touch_rule == "EXPIRED_NO_ENTRY" and r.brier_excluded and r.brier is None


def test_backfill_excluded_from_brier():
    pred = {"generator_id": reconcile.BACKFILL_GENERATOR, "direction": "up",
            "distribution": {"up": 0.6, "down": 0.3, "no_move": 0.1}, "target_price": 63.5,
            "invalidation_price": 58.5}
    r = reconcile.grade(pred, [_bar(64, 62, 63.8)])
    assert r.outcome_class == "up" and r.brier_excluded and r.brier is None


def test_pending_when_not_matured():
    pred = {"generator_id": "g", "direction": "up", "distribution": None,
            "target_price": 63.5, "invalidation_price": 58.5, "expiry_timestamp": "2026-12-31T00:00:00Z"}
    r = reconcile.grade(pred, [_bar(61, 59, 60)], now_ts="2026-07-28T00:00:00Z")
    assert r.resolved is False and r.first_touch_rule == "PENDING"


# ---- THE LOOP: write -> measure -> grade -> weight-change ------------------
def test_full_loop_closes():
    con = ledger.connect(":memory:")

    # WRITE — a schema-complete generator belief through the write-authority gate
    payload = {
        "prediction_id": "loop-1", "generator_id": "gemini_spark", "ticker": "FRO", "direction": "up",
        "offset_target_pct": 5.0, "offset_invalidation_pct": -3.0,
        "distribution": {"hit_target_first": 0.6, "hit_invalidation_first": 0.3, "expire_in_range": 0.1},
        "thesis": "t", "canon_tags": ["LITERATURE"], "source_urls": ["https://x"],
        "price_mode": "RELATIVE_PCT",
    }
    assert vi.intake(payload).accepted

    # VERIFY station anchors absolutes off the last official close (38.59)
    target, inval = vi.anchor_relative(38.59, 5.0, -3.0)     # 40.5195 / 37.4323
    ledger.log_prediction(con, prediction_id="loop-1", ticker="FRO", direction="up",
                          price_mode="RELATIVE_PCT", generator_id="gemini_spark",
                          distribution=payload["distribution"], anchor_close=38.59,
                          target_price=target, invalidation_price=inval,
                          expiry_timestamp="2026-08-01T00:00:00Z",
                          ts="2026-07-27T10:00:00Z")   # prior committed BEFORE the 14:00Z touch -> ELIGIBLE

    # MEASURE — synthetic 15s bars where the target is touched first
    bars = [_bar(40.60, 38.20, 40.55)]
    summary = reconcile.reconcile(con, lambda pred: bars if pred["ticker"] == "FRO" else [],
                                  now_ts="2026-07-28T00:00:00Z")

    # GRADE landed
    row = con.execute("SELECT resolved, outcome_class, first_touch_rule, brier "
                      "FROM predictions WHERE prediction_id='loop-1'").fetchone()
    assert row[0] == 1 and row[1] == "up" and row[2] == "TARGET_FIRST"
    assert row[3] == pytest.approx(0.26)

    # WEIGHT changed from the 0.5 prior; change logged
    w = con.execute("SELECT weight, n_resolved FROM weights WHERE key='gemini_spark'").fetchone()
    assert w is not None and w[1] == 1
    assert w[0] == pytest.approx(0.5 + 0.10 * ((1 - 0.26 / 2) - 0.5), abs=1e-4)  # EWMA toward correctness
    assert con.execute("SELECT count(*) FROM weight_change_log WHERE prediction_id='loop-1'").fetchone()[0] == 1
    assert summary["weight_changes"]
