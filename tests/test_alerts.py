from __future__ import annotations

import json

import pytest

from cosmos import alerts, paths


def _read(path):
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def test_emit_writes_local_and_buffer():
    rec = alerts.emit_alert("HEARTBEAT_OK", "all good", severity="INFO", age=12)
    assert rec is not None
    logged = _read(paths.ALERTS_PATH)
    assert logged[-1]["kind"] == "HEARTBEAT_OK"
    assert logged[-1]["fields"]["age"] == 12
    buffered = _read(paths.STAGING_MIRROR / "_alerts_buffer.jsonl")
    assert buffered[-1]["kind"] == "HEARTBEAT_OK"


def test_once_per_day_dedupe():
    first = alerts.emit_alert("SETUP_INCOMPLETE", "tab missing", severity="WARN", once_per_day=True)
    second = alerts.emit_alert("SETUP_INCOMPLETE", "tab missing", severity="WARN", once_per_day=True)
    assert first is not None
    assert second is None
    assert len(_read(paths.ALERTS_PATH)) == 1


def test_invalid_severity_raises():
    with pytest.raises(ValueError):
        alerts.emit_alert("X", "bad", severity="FATAL")
