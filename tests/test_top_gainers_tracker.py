from __future__ import annotations

import pytest

from cosmos.top_gainers_tracker import (
    GainerClass, GainerFeatures, PROFILES,
    classify_gainer, expected_return_from_atlas,
)


def test_no_hardcoded_expected_returns():
    # OQ-SPARK-DECAY-ARC: every class profile must start unpopulated.
    assert all(p.expected_return is None for p in PROFILES.values())


def test_dilution_collapse_vtix_like():
    f = GainerFeatures(off_52w_high_frac=0.98, window_return_pct=-70, max_drawdown_pct=-74,
                       up_spike_days=1, down_spike_days=4, avg_daily_volume=951212,
                       range_position=0.01)
    r = classify_gainer(f)
    assert r.gainer_class == GainerClass.DILUTION_CYCLE
    assert r.expected_return is None


def test_noncompliant_forces_dilution_lgvn_like():
    f = GainerFeatures(off_52w_high_frac=0.65, window_return_pct=-39, max_drawdown_pct=-48,
                       up_spike_days=0, down_spike_days=0, avg_daily_volume=267298,
                       range_position=0.29, noncompliant=True)
    assert classify_gainer(f).gainer_class == GainerClass.DILUTION_CYCLE


def test_serial_catalyst_qttb_like():
    f = GainerFeatures(off_52w_high_frac=0.36, window_return_pct=127, max_drawdown_pct=-33,
                       up_spike_days=3, down_spike_days=2, avg_daily_volume=2502073,
                       range_position=0.62)
    r = classify_gainer(f)
    assert r.gainer_class == GainerClass.SERIAL_CATALYST
    assert r.expected_return is None


def test_sustained_regime_bdsx_like():
    f = GainerFeatures(off_52w_high_frac=0.12, window_return_pct=48, max_drawdown_pct=-37,
                       up_spike_days=2, down_spike_days=0, avg_daily_volume=78722,
                       range_position=0.84)
    assert classify_gainer(f).gainer_class == GainerClass.SUSTAINED_REGIME


def test_structural_noise_daio_like():
    f = GainerFeatures(off_52w_high_frac=0.32, window_return_pct=27, max_drawdown_pct=-27,
                       up_spike_days=1, down_spike_days=0, avg_daily_volume=45217,
                       range_position=0.39)
    assert classify_gainer(f).gainer_class == GainerClass.STRUCTURAL_NOISE


def test_overlap_recorded_stak_like():
    # violent pump that ALSO collapsed: primary DILUTION, but SERIAL_CATALYST flagged
    f = GainerFeatures(off_52w_high_frac=0.79, window_return_pct=147, max_drawdown_pct=-84,
                       up_spike_days=12, down_spike_days=8, avg_daily_volume=7934235,
                       range_position=0.19)
    r = classify_gainer(f)
    assert r.gainer_class == GainerClass.DILUTION_CYCLE
    assert GainerClass.SERIAL_CATALYST in r.overlap_flags


def test_expected_return_only_from_atlas():
    assert expected_return_from_atlas([]) is None
    assert expected_return_from_atlas([4.5, 1.1, -3.2]) == pytest.approx((4.5 + 1.1 - 3.2) / 3)
