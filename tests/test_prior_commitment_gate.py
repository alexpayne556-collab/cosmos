"""ADR-030 — the Prior-Commitment Gate. Fixtures F15-F20, written failing-first."""
from __future__ import annotations

import pytest

from cosmos import ledger, reconcile, verify_intake as vi
from cosmos import schema_validation as sv

DIST = {"hit_target_first": 0.6, "hit_invalidation_first": 0.3, "expire_in_range": 0.1}


def _bar(hi, lo, close, at="2026-07-27T14:00:00Z"):
    return {"high_price": str(hi), "low_price": str(lo), "close_price": str(close), "begins_at": at}


def _pred(**over):
    p = {"generator_id": "gemini_spark", "direction": "up",
         "target_price": 63.5, "invalidation_price": 58.5}
    p.update(over)
    return p


# F15 — distribution committed at/after outcome_determined_at -> EXCLUDED_POST_HOC, no Brier
def test_f15_post_hoc_excluded():
    r = reconcile.grade(_pred(), [_bar(64, 62, 63.8)],
                        t0_distribution=DIST,
                        distribution_logged_at="2026-07-27T15:00:00Z",   # after the 14:00 touch
                        prediction_logged_at="2026-07-27T09:00:00Z")
    assert r.brier_eligibility == "EXCLUDED_POST_HOC"
    assert r.brier is None


# F16 — committed after prediction but before outcome -> ELIGIBLE_LATE_PRIOR, scored, lag recorded
def test_f16_late_prior_scored():
    r = reconcile.grade(_pred(), [_bar(64, 62, 63.8)],
                        t0_distribution=DIST,
                        distribution_logged_at="2026-07-27T12:00:00Z",   # before the 14:00 touch
                        prediction_logged_at="2026-07-27T09:00:00Z")
    assert r.brier_eligibility == "ELIGIBLE_LATE_PRIOR"
    assert r.brier == pytest.approx(0.26)          # target-first hit, DIST=0.6/0.3/0.1
    assert r.prior_lag_hours == pytest.approx(3.0)  # 12:00 - 09:00


# F17 — generator supplies distribution_logged_at -> stripped, SELF_STAMPED, value retained
def test_f17_self_stamped_stripped():
    payload = {
        "prediction_id": "ss1", "generator_id": "gemini_spark", "ticker": "FRO", "direction": "up",
        "offset_target_pct": 5.0, "offset_invalidation_pct": -3.0, "distribution": DIST,
        "thesis": "t", "canon_tags": ["LITERATURE"], "source_urls": ["https://x"],
        "price_mode": "RELATIVE_PCT",
        "distribution_logged_at": "2020-01-01T00:00:00Z",   # backdated self-stamp
    }
    r = vi.intake(payload)
    assert "distribution_logged_at" not in r.record
    v = [x for x in r.violations if x["field"] == "distribution_logged_at"]
    assert v and v[0]["reason"] == "SELF_STAMPED"
    assert v[0]["value"] == "2020-01-01T00:00:00Z"      # retained as forensics


# F18 — revise_distribution appends seq 1; Brier still scores seq 0
def test_f18_revision_scores_seq0():
    con = ledger.connect(":memory:")
    a = {"hit_target_first": 0.6, "hit_invalidation_first": 0.3, "expire_in_range": 0.1}
    b = {"hit_target_first": 0.9, "hit_invalidation_first": 0.05, "expire_in_range": 0.05}
    ledger.log_prediction(con, prediction_id="rev1", ticker="X", direction="up",
                          price_mode="ABSOLUTE", distribution=a, ts="2026-07-27T09:00:00Z")
    ledger.revise_distribution(con, "rev1", b, source_station="gemini_spark")
    d0, _at0 = ledger.t0_distribution(con, "rev1")
    assert d0 == a                                       # seq 0 unchanged by the revision
    n = con.execute("SELECT COUNT(*) FROM prediction_distributions WHERE prediction_id='rev1'").fetchone()[0]
    assert n == 2


# F19 — murphy guards degenerate input
def test_f19_murphy_guard():
    res, reason = reconcile.murphy_decomposition([(0.8, 1), (0.8, 0), (0.2, 1), (0.2, 0), (0.8, 1)])
    assert res is None and reason                        # n=5, 2 distinct -> refused
    pairs = [(round(0.15 * (i % 4 + 1), 2), i % 2) for i in range(20)]  # n=20, 4 distinct
    res2, reason2 = reconcile.murphy_decomposition(pairs)
    assert res2 is not None


# F20 — row without a distribution rejected under schema v1.0.2
def test_f20_distribution_required_v102():
    row = {"ticker": "FRO", "direction": "up", "offset_target_pct": 5.0,
           "offset_invalidation_pct": -3.0, "thesis": "t", "canon_tags": ["x"],
           "source_urls": ["https://x"], "price_mode": "RELATIVE_PCT"}  # no distribution
    errs = sv.validate_against(row, "prediction_row.v1.0.2.schema.json")
    assert any("distribution" in e for e in errs)
