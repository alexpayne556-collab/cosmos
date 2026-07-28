"""
Load-bearing alerting (Section: Load-Bearing Alerting + Section 8.2).

The PRIMARY alert path is LOCAL and always operational: every alert is
appended to /data/alerts.jsonl AND mirrored to a staging buffer. Remote
channels (Sheet, and the CLAIMED Google Tasks queue) are best-effort layers
on top; local logging never depends on them.

Section 8.2 escalation rule is encoded by severity:
    INFO      nothing arrived / normal
    WARN      arrived-broken / degraded (e.g. heartbeat > 7200s)
    CRITICAL  pipe down (e.g. heartbeat > 14400s, bulk fallback)

`once_per_day=True` implements the SETUP_INCOMPLETE "once per day, not per
poll" rule.
"""
from __future__ import annotations

import datetime
import json
import pathlib
from typing import Optional

from . import paths
from .persistence import atomic_write_json

VALID_SEVERITIES = ("INFO", "WARN", "CRITICAL")


def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _append_line(path: pathlib.Path, obj: dict) -> None:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, default=str) + "\n")


def _dedupe_first_today(kind: str, day: str) -> bool:
    """Return True the first time (kind, day) is seen; False thereafter."""
    state_path = paths.ALERT_DEDUPE_STATE
    state: dict = {}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            state = {}
    key = f"{kind}:{day}"
    if state.get(key):
        return False
    state[key] = True
    atomic_write_json(state_path, state)
    return True


def emit_alert(kind: str, message: str, *,
               severity: str = "INFO",
               once_per_day: bool = False,
               buffer: bool = True,
               **fields) -> Optional[dict]:
    """Emit a structured alert. Returns the record, or None if suppressed by
    once_per_day dedupe."""
    if severity not in VALID_SEVERITIES:
        raise ValueError(f"invalid severity {severity!r}; expected one of {VALID_SEVERITIES}")
    paths.ensure_dirs()
    now = _now_utc()
    if once_per_day and not _dedupe_first_today(kind, now.strftime("%Y-%m-%d")):
        return None
    record = {
        "ts_utc": now.isoformat(),
        "kind": kind,
        "severity": severity,
        "message": message,
    }
    if fields:
        record["fields"] = fields
    # 1) load-bearing local log FIRST
    _append_line(paths.ALERTS_PATH, record)
    # 2) mirror into the local staging buffer
    if buffer:
        _append_line(paths.STAGING_MIRROR / "_alerts_buffer.jsonl", record)
    return record
