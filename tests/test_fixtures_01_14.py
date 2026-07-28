"""
Fixtures 1-14 (ADR-016, originator: gemini_spark for 1-4 — from his own
failures). Permanent regression guards: each pins a real failure so it can
never silently return.

STATUS: RECONSTRUCTED from the failure fingerprints in the constitution
(Sections 1/4) and the ratified addenda. Pending ratification against Gemini's
exact Round-12 enumeration -> OQ-FIXTURES-1. Every fixture below asserts against
live Phase-0 code (no stubs). Full first-touch grading over a 15s bar SERIES is
the ADR-007 reconcile upgrade (Phase 3); fixture 14 pins the deterministic
single-bar structural rule that exists today.
"""
from __future__ import annotations

import random

import pytest

from cosmos import backoff, oracle, paths, persistence, verify_intake as vi
from cosmos.checkpoints import CheckpointMatchRule, CheckpointPredicate, evaluate_checkpoint_rule, evaluate_document
from cosmos.grading import Grade, structural_gate, is_loss
from cosmos.quarantine import QuarantineReason, quarantine
from cosmos import schema_validation as sv


def _gen(**over):
    p = {
        "ticker": "FRO", "direction": "up", "offset_target_pct": 5.0,
        "offset_invalidation_pct": -3.0,
        "distribution": {"up": 0.6, "down": 0.3, "no_move": 0.1},
        "thesis": "t", "canon_tags": ["LITERATURE"],
        "source_urls": ["https://x"], "price_mode": "RELATIVE_PCT",
    }
    p.update(over)
    return p


# 1 — distribution must sum to 1.0 +/- 0.001
def test_fx01_distribution_sum_to_one():
    assert vi.intake(_gen(distribution={"up": 0.5, "down": 0.3})).accepted is False
    assert vi.intake(_gen()).accepted is True


# 2 — generator writing an absolute price -> SELF_VERIFIED, stripped
def test_fx02_self_verified_quarantine():
    r = vi.intake(_gen(target_price=40.0))
    assert "target_price" not in r.record
    assert r.violations[0]["reason"] == QuarantineReason.SELF_VERIFIED.value


# 3 — generator writing fundamentals -> FUNDAMENTAL_OVERWRITE
def test_fx03_fundamental_overwrite():
    r = vi.intake(_gen(market_cap=9.2e9))
    assert any(v["reason"] == QuarantineReason.FUNDAMENTAL_OVERWRITE.value for v in r.violations)


# 4 — generator writing run history -> CONFABULATED_HISTORY
def test_fx04_confabulated_history():
    r = vi.intake(_gen(run_magnitude_pct=26.0))
    assert any(v["reason"] == QuarantineReason.CONFABULATED_HISTORY.value for v in r.violations)


# 5 — RELATIVE_PCT anchors to the last official close (ADR-001)
def test_fx05_relative_pct_anchor():
    target, inval = vi.anchor_relative(38.59, 5.0, -3.0)
    assert target == pytest.approx(40.5195, abs=1e-4)
    assert inval == pytest.approx(37.4323, abs=1e-4)


# 6 — checkpoint literal is escaped (BRK.B != BRKXB)
def test_fx06_literal_not_regex():
    rule = CheckpointMatchRule(CheckpointPredicate.NEWS_HEADLINE_MATCH, ("HEADLINE",), "BRK.B")
    assert evaluate_checkpoint_rule(rule, "BRKXB") is False


# 7 — invalid regex is quarantined, never crashes
def test_fx07_invalid_regex_quarantined():
    rule = CheckpointMatchRule(CheckpointPredicate.EDGAR_FILING_CONTAINS, ("8-K",), "(unbalanced", is_regex=True)
    assert evaluate_checkpoint_rule(rule, "x") is False
    assert list(paths.QUARANTINE.glob("*INVALID_REGEX*.json"))


# 8 — scope pre-filter skips out-of-scope documents
def test_fx08_scope_filter():
    rule = CheckpointMatchRule(CheckpointPredicate.EDGAR_FILING_CONTAINS, ("8-K",), "award")
    assert evaluate_document(rule, {"scope": "HEADLINE", "text": "award"}) is None


# 9 — oracle 4x2 classification (ACUTE + INVERTED -> credit crisis)
def test_fx09_oracle_matrix():
    s = oracle.classify(9.0, -0.7)
    assert s.regime == "CREDIT_CRISIS" and s.asset_class == "DEFENSIVE"


# 10 — backoff full jitter stays within the ratified ceilings
def test_fx10_backoff_bounds():
    rng = random.Random(7)
    for a in (1, 2, 3):
        d = backoff.compute_delay(backoff.SEC_EDGAR_PROFILE, a, rng=rng)
        assert 0 <= d <= backoff.SEC_EDGAR_PROFILE.ceiling(a)


# 11 — atomic persistence round-trips with matching hash
def test_fx11_atomic_persistence(tmp_path):
    import hashlib
    d = b"payload"
    h = persistence.atomic_write_bytes(tmp_path / "x.bin", d)
    assert h == hashlib.sha256(d).hexdigest()
    assert (tmp_path / "x.bin").read_bytes() == d


# 12 — quarantine manifest carries reason + errors + hash, schema-valid
def test_fx12_quarantine_manifest():
    p = quarantine({"k": "v"}, reason=QuarantineReason.MALFORMED_ROW, errors=["boom"])
    import json
    m = json.loads(p.read_text())
    assert m["reason"] == "MALFORMED_ROW" and m["errors"] == ["boom"]
    assert sv.is_valid(m, "quarantine_manifest.schema.json")


# 13 — EDGAR block never rotates identity (ethics load-bearing)
def test_fx13_no_identity_rotation():
    from cosmos.edgar_poller import EdgarPoller, BULK_INDEX_URL
    def fetch(url):
        return (200, b"idx") if url == BULK_INDEX_URL else (403, b"")
    poller = EdgarPoller(fetch=fetch, sleep=lambda d: None)
    ua0 = poller.user_agent
    res = poller.poll("https://sec.gov/x", rng=random.Random(0))
    assert res["user_agent"] == ua0 == poller.user_agent


# 14 — a bar touching BOTH target and invalidation grades AMBIGUOUS -> loss
def test_fx14_ambiguous_both_touched_is_loss():
    g = structural_gate("up", bar_high=41.0, bar_low=37.0,
                        target_price=40.0, invalidation_price=37.4)
    assert g == Grade.AMBIGUOUS_BOTH_TOUCHED
    assert is_loss(g) is True
    # a clean hit is not a loss
    assert structural_gate("up", 41.0, 39.0, 40.0, 37.4) == Grade.HIT
