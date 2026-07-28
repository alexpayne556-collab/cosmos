"""Test isolation: every test gets its own /data tree in a tmp dir, so alerts,
quarantine, and staging writes never touch the real event store."""
from __future__ import annotations

import pytest

from cosmos import paths


@pytest.fixture(autouse=True)
def isolate_data(tmp_path, monkeypatch):
    d = tmp_path / "data"
    monkeypatch.setattr(paths, "DATA_DIR", d)
    monkeypatch.setattr(paths, "STAGING_MIRROR", d / "staging_mirror")
    monkeypatch.setattr(paths, "QUARANTINE", d / "quarantine")
    monkeypatch.setattr(paths, "ALERTS_PATH", d / "alerts.jsonl")
    monkeypatch.setattr(paths, "ALERT_DEDUPE_STATE", d / "alert_dedupe.json")
    monkeypatch.setattr(paths, "PROCESSED_RUNS", d / "processed_runs.json")
    paths.ensure_dirs()
    yield


@pytest.fixture
def valid_prediction():
    """Factory for a write-authority-clean generator payload (distribution=1.0)."""
    def _make(**overrides):
        p = {
            "prediction_id": "pred-0001",
            "generator_id": "gemini_spark",
            "ticker": "FRO",
            "direction": "up",
            "offset_target_pct": 5.0,
            "offset_invalidation_pct": -3.0,
            "distribution": {"up": 0.6, "down": 0.3, "no_move": 0.1},
            "thesis": "Hormuz tanker rate spike; VLCC spot cash flow.",
            "canon_tags": ["LITERATURE"],
            "source_urls": ["https://frontline.example/ir"],
            "price_mode": "RELATIVE_PCT",
            "strategy_family": "swing",
            "horizon_days": 10,
        }
        p.update(overrides)
        return p
    return _make
