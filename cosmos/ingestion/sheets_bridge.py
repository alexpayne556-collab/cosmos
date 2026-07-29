"""
Google Sheets staging bridge (OQ-SHEETS-BRIDGE) — ADR-002 + ADR-030 compliant.

Lane ruling (2026-07-29): Spark's news / catalysts / macro theses enter as
OBSERVATIONS in `market_observations` (reader lane). ONLY a fully-formed prediction
row with an explicit probability distribution enters `predictions`, and ONLY through
`verify_intake.intake()` -> `ledger.log_prediction()` (write-authority + the ADR-030
Prior-Commitment Gate). There is NO raw INSERT into predictions, ever.

Anchor sequencing (ruling): a prediction is logged at t0 with its distribution
(locking the gate; `distribution_logged_at` stamped now) and prices PENDING_VERIFY
(anchor_close/target/invalidation = NULL). A later verify-lane enrichment fills the
prices via `ledger.enrich_prices()` WITHOUT altering t0 or backdating the stamp.

The Sheet reader and the anchor fetch are injected, so the bridge is fully testable
offline. A live read needs `credentials/service_account.json` (config.py); absent it
the bridge emits SETUP_INCOMPLETE once/day and does nothing — never crashes (§8.2).
"""
from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from .. import alerts, config, ledger, verify_intake
from ..verify_intake import Station, anchor_relative

OBS_SCHEMA = """
CREATE TABLE IF NOT EXISTS market_observations (
    observation_id TEXT PRIMARY KEY,
    ticker TEXT,                        -- NULL allowed; never fabricated
    headline TEXT NOT NULL,             -- cause / thesis text (no numbers)
    source TEXT NOT NULL,
    category TEXT NOT NULL,             -- CATALYST / MACRO / NEWS ... descriptive, NOT a directive
    source_url TEXT,
    canon_tag TEXT NOT NULL,            -- HYPOTHESIS / LITERATURE (reader canon)
    observation_logged_at TEXT NOT NULL
);
"""

_DIST_TOL = 0.01  # looser than intake's ±0.001; intake does the strict check


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_prediction_row(row: dict) -> bool:
    """Lane discriminator (ruling): a PREDICTION carries an explicit probability
    vector (sum~1) + a direction + relative offsets. Everything else is a reader
    OBSERVATION and must NOT touch the ledger."""
    dist = row.get("distribution")
    return (
        isinstance(dist, dict) and dist
        and abs(sum(dist.values()) - 1.0) < _DIST_TOL
        and row.get("direction") in ("up", "down", "no_move")
        and "offset_target_pct" in row
    )


class SheetsBridgeAdapter:
    def __init__(self, ledger_con: sqlite3.Connection, obs_con: sqlite3.Connection,
                 *, reader: Optional[Callable[[], List[dict]]] = None):
        self.ledger = ledger_con
        self.obs = obs_con
        self.reader = reader
        with self.obs:
            self.obs.executescript(OBS_SCHEMA)

    # ---- live read (needs a service account) ----------------------------
    def poll_live(self) -> Dict[str, Any]:
        if self.reader is None and not config.has_google_service_account():
            alerts.emit_alert(
                "SETUP_INCOMPLETE",
                "Sheets bridge: credentials/service_account.json absent; cannot read the Sheet",
                severity="WARN", once_per_day=True)
            return {"status": "SETUP_INCOMPLETE", "rows_processed": 0}
        if self.reader is None:
            raise RuntimeError("live Sheet reader not wired; inject `reader` or add a service account")
        return self.process_staging_rows(self.reader())

    # ---- the gate-routed core (testable offline) ------------------------
    def process_staging_rows(self, rows: List[dict]) -> Dict[str, Any]:
        seen = ledger.all_prediction_ids(self.ledger)
        accepted = quarantined = observations = 0
        for row in rows:
            if not is_prediction_row(row):
                self._record_observation(row)
                observations += 1
                continue
            result = verify_intake.intake(row, actor=Station.GENERATOR, seen_ids=seen)
            if not result.accepted:
                quarantined += 1
                continue
            rec = result.record
            try:
                ledger.log_prediction(
                    self.ledger,
                    prediction_id=rec["prediction_id"], ticker=rec["ticker"],
                    direction=rec["direction"], price_mode=rec.get("price_mode", "RELATIVE_PCT"),
                    generator_id=rec.get("generator_id", "gemini_spark"),
                    strategy_family=rec.get("strategy_family", "sheet_staging"),
                    distribution=rec.get("distribution"), thesis=rec.get("thesis"),
                    canon_tags=rec.get("canon_tags", []), source_urls=rec.get("source_urls", []),
                    anchor_close=None, target_price=None, invalidation_price=None,  # PENDING_VERIFY @ t0
                    expiry_timestamp=rec.get("expiry_timestamp"))
                accepted += 1
            except ledger.DuplicatePredictionError:
                quarantined += 1   # the authoritative backstop — never a silent INSERT OR IGNORE
        return {"rows_processed": len(rows), "accepted": accepted,
                "observations": observations, "quarantined": quarantined}

    def _record_observation(self, row: dict) -> None:
        headline = row.get("headline") or row.get("thesis") or ""
        oid = row.get("observation_id") or hashlib.sha256(
            (str(row.get("ticker", "")) + headline + str(row.get("source_url", ""))).encode("utf-8")
        ).hexdigest()[:24]
        with self.obs:
            if self.obs.execute("SELECT 1 FROM market_observations WHERE observation_id=?",
                                (oid,)).fetchone():
                return
            self.obs.execute(
                "INSERT INTO market_observations (observation_id, ticker, headline, source, "
                "category, source_url, canon_tag, observation_logged_at) VALUES (?,?,?,?,?,?,?,?)",
                (oid, row.get("ticker"), headline, row.get("source", "SPARK_SHEET"),
                 row.get("category", "OBSERVATION"), row.get("source_url"),
                 row.get("canon_tag", "HYPOTHESIS"), _now_iso()))

    # ---- verify-lane enrichment (t0 immutable) --------------------------
    def enrich_prediction(self, prediction_id: str, *, anchor_close: float,
                          offset_target_pct: float, offset_invalidation_pct: float) -> bool:
        """Fill prices from an agent-fetched anchor_close (last official close preceding
        release). Computes absolutes via anchor_relative, then ledger.enrich_prices —
        which never touches ts_logged / distribution_logged_at / the t0 distribution."""
        target, invalidation = anchor_relative(anchor_close, offset_target_pct, offset_invalidation_pct)
        return ledger.enrich_prices(self.ledger, prediction_id, anchor_close=anchor_close,
                                    target_price=target, invalidation_price=invalidation)
