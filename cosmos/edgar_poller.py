"""
SEC EDGAR poller (ADR-026, originator: gemini_spark; Drill 3 corrected —
load-bearing ethics).

Fair-access compliant:
  * Declared compliant User-Agent, <= 5 requests/second.
  * On HTTP 403/429: honor the block completely — exponential backoff with full
    jitter (SEC_EDGAR_PROFILE: 30s -> 2m -> 10m), then switch to the SEC's
    official daily bulk index. Alert the human (SEC_EDGAR_BULK_FALLBACK).
  * NEVER rotate identity or spoof the User-Agent to evade a block. The retry
    and the fallback use the SAME declared UA. This line is load-bearing.

Raw responses are archived atomically to /data/staging_mirror before parsing;
each success result carries `archived_path` so a caller parses the byte-for-byte
archived artifact (never a second fetch — the transport owns the UA).
The HTTP layer is injectable (`fetch`) so the whole policy is testable offline.
"""
from __future__ import annotations

import time
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, Optional, Tuple

from . import alerts, backoff, paths
from .persistence import atomic_write_bytes

DEFAULT_USER_AGENT = "CosmosSavant/1.0 (operator contact: ops@cosmos-savant.local)"
MAX_REQ_PER_SEC = 5
BULK_INDEX_URL = "https://www.sec.gov/Archives/edgar/daily-index/"


class HTTPStatusError(Exception):
    def __init__(self, status: int):
        super().__init__(f"HTTP {status}")
        self.status = status


# fetch signature: (url) -> (status_code:int, body:bytes)
FetchFn = Callable[[str], Tuple[int, bytes]]


@dataclass
class EdgarPoller:
    user_agent: str = DEFAULT_USER_AGENT
    min_interval: float = 1.0 / MAX_REQ_PER_SEC
    fetch: Optional[FetchFn] = None
    sleep: Callable[[float], None] = time.sleep
    _last_request_monotonic: float = field(default=0.0, repr=False)

    def __post_init__(self) -> None:
        if self.fetch is None:
            self.fetch = self._urllib_fetch

    # ---- transport (default) --------------------------------------------
    def _urllib_fetch(self, url: str) -> Tuple[int, bytes]:
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.getcode(), resp.read()

    def _throttle(self) -> None:
        now = time.monotonic()
        wait = self.min_interval - (now - self._last_request_monotonic)
        if wait > 0:
            self.sleep(wait)
        self._last_request_monotonic = time.monotonic()

    def _safe_fetch(self, url: str) -> Tuple[int, bytes]:
        try:
            return self.fetch(url)
        except HTTPStatusError as exc:
            return exc.status, b""

    # ---- public API ------------------------------------------------------
    def poll(self, url: str, *, rng=None) -> dict:
        """Poll a live EDGAR endpoint. Returns a result dict describing the mode;
        success modes carry `archived_path` (the raw body on disk)."""
        self._throttle()
        status, body = self._safe_fetch(url)
        if status == 200:
            archived = self._archive(url, body)
            return {"mode": "LIVE", "status": 200, "bytes": len(body),
                    "archived_path": archived, "user_agent": self.user_agent}
        if status in (403, 429):
            return self._handle_block(url, status, rng=rng)
        raise HTTPStatusError(status)

    def _handle_block(self, url: str, status: int, *, rng=None) -> dict:
        alerts.emit_alert("SEC_EDGAR_BLOCK",
                          f"HTTP {status} on {url}; honoring block, backing off",
                          severity="WARN", status=status)
        profile = backoff.SEC_EDGAR_PROFILE
        for attempt in range(1, profile.max_attempts + 1):
            self.sleep(backoff.compute_delay(profile, attempt, rng=rng))
            self._throttle()
            status2, body = self._safe_fetch(url)   # SAME user_agent — no rotation
            if status2 == 200:
                archived = self._archive(url, body)
                return {"mode": "LIVE_RECOVERED", "status": 200, "attempts": attempt,
                        "archived_path": archived, "user_agent": self.user_agent}
        return self._bulk_fallback(rng=rng)

    def _bulk_fallback(self, *, rng=None) -> dict:
        alerts.emit_alert(
            "SEC_EDGAR_BULK_FALLBACK",
            "switching to SEC daily bulk index (master.idx); "
            "real-time 15-min detection -> daily batch cadence",
            severity="CRITICAL",
        )
        self._throttle()
        status, body = self._safe_fetch(BULK_INDEX_URL)   # STILL the same UA
        if status == 200:
            archived = self._archive(BULK_INDEX_URL, body)
            return {"mode": "BULK_FALLBACK", "status": 200,
                    "archived_path": archived, "user_agent": self.user_agent}
        return {"mode": "BULK_FALLBACK_DEGRADED", "status": status,
                "user_agent": self.user_agent}

    # ---- archive ---------------------------------------------------------
    def _archive(self, url: str, body: bytes) -> str:
        paths.ensure_dirs()
        safe = "".join(c if c.isalnum() else "_" for c in url)[-80:]
        out = paths.STAGING_MIRROR / f"edgar_{safe}.raw"
        atomic_write_bytes(out, body)
        return str(out)
