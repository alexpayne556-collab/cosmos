from __future__ import annotations

import pytest

from cosmos import verify_intake as vi
from cosmos.quarantine import QuarantineReason


def test_clean_generator_payload_accepted(valid_prediction):
    r = vi.intake(valid_prediction())
    assert r.accepted is True
    assert r.violations == []
    assert r.claim_accuracy_charge == 0.0
    assert r.record["ticker"] == "FRO"


def test_self_verified_price_stripped(valid_prediction):
    r = vi.intake(valid_prediction(verified_price=40.0))
    assert "verified_price" not in r.record          # stripped
    assert any(v["reason"] == QuarantineReason.SELF_VERIFIED.value for v in r.violations)
    assert r.quarantine_paths and r.claim_accuracy_charge > 0.0


def test_fundamental_overwrite(valid_prediction):
    r = vi.intake(valid_prediction(float=1.4e8))
    assert "float" not in r.record
    assert any(v["reason"] == QuarantineReason.FUNDAMENTAL_OVERWRITE.value for v in r.violations)


def test_confabulated_history(valid_prediction):
    r = vi.intake(valid_prediction(run_date="2026-05-26"))
    assert "run_date" not in r.record
    assert any(v["reason"] == QuarantineReason.CONFABULATED_HISTORY.value for v in r.violations)


def test_distribution_must_sum_to_one(valid_prediction):
    r = vi.intake(valid_prediction(distribution={"up": 0.6, "down": 0.3}))  # 0.9
    assert r.accepted is False
    assert any("distribution sums" in e for e in r.errors)


def test_distribution_within_tolerance_accepted(valid_prediction):
    r = vi.intake(valid_prediction(distribution={"up": 0.6005, "down": 0.3, "no_move": 0.0995}))
    assert r.accepted is True


def test_missing_required_field(valid_prediction):
    p = valid_prediction()
    del p["thesis"]
    r = vi.intake(p)
    assert r.accepted is False
    assert any("thesis" in e for e in r.errors)


def test_duplicate_prediction_id_rejected(valid_prediction):
    seen = set()
    first = vi.intake(valid_prediction(prediction_id="dup-1"), seen_ids=seen)
    assert first.accepted is True
    second = vi.intake(valid_prediction(prediction_id="dup-1"), seen_ids=seen)
    assert second.accepted is False
    assert any("duplicate prediction_id" in e for e in second.errors)
    assert second.quarantine_paths


def test_anchor_relative_last_close():
    target, inval = vi.anchor_relative(38.59, 5.0, -3.0)
    assert target == pytest.approx(40.5195, abs=1e-4)
    assert inval == pytest.approx(37.4323, abs=1e-4)
