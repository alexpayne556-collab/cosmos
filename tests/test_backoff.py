from __future__ import annotations

import random

import pytest

from cosmos import backoff


def test_ratified_schedules_differ():
    # Drill 3 (EDGAR) 30s->2m->10m ; Drill 2 (Sheets) 30s->2m->8m
    assert backoff.SEC_EDGAR_PROFILE.base_delays == (30.0, 120.0, 600.0)
    assert backoff.SHEETS_PROFILE.base_delays == (30.0, 120.0, 480.0)


def test_ceiling_clamps_to_last_step():
    p = backoff.SEC_EDGAR_PROFILE
    assert p.ceiling(1) == 30.0
    assert p.ceiling(3) == 600.0
    assert p.ceiling(9) == 600.0  # clamps


def test_full_jitter_within_bounds():
    rng = random.Random(1234)
    for attempt in (1, 2, 3):
        ceiling = backoff.SEC_EDGAR_PROFILE.ceiling(attempt)
        for _ in range(200):
            d = backoff.compute_delay(backoff.SEC_EDGAR_PROFILE, attempt, rng=rng)
            assert 0.0 <= d <= ceiling


def test_jitter_none_returns_ceiling():
    prof = backoff.BackoffProfile("x", (10.0,), 1, jitter="none")
    assert backoff.compute_delay(prof, 1) == 10.0


def test_retry_succeeds_after_transient_failures():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("transient")
        return "ok"

    slept = []
    out = backoff.retry(flaky, backoff.SEC_EDGAR_PROFILE,
                        sleep=slept.append, rng=random.Random(0))
    assert out == "ok"
    assert calls["n"] == 3
    assert len(slept) == 2                       # slept before attempts 2 and 3, not after
    assert all(0.0 <= s <= 600.0 for s in slept)


def test_retry_exhausts_and_raises():
    def always_fail():
        raise RuntimeError("nope")

    slept = []
    with pytest.raises(backoff.RetryExhausted) as ei:
        backoff.retry(always_fail, backoff.SHEETS_PROFILE,
                      sleep=slept.append, rng=random.Random(0))
    assert isinstance(ei.value.last_exc, RuntimeError)
    assert len(slept) == 2                       # max_attempts=3 -> 2 sleeps
