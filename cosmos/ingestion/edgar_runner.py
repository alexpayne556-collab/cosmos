"""
EDGAR filing observation runner (OQ-EDGAR-RSS-RUNNER).

Polls SEC EDGAR THROUGH the fair-access `EdgarPoller` (Drill-3 intact: declared
UA, <=5 req/s, 403/429 backoff, NO identity rotation), parses the archived Atom
feed, and records filings as pure OBSERVATIONS in `filing_observations` — never
predictions, never directives (Ruling 2). Reader/research lane, in a store
physically separate from the graded prediction ledger (ADR-026 firewall).

Lane note (per the 2026-07-29 ruling): SEC filings -> `filing_observations`;
Spark's news/catalysts/macro theses -> `market_observations` (the sheets bridge);
only fully-formed prediction rows -> `predictions` via verify_intake + ledger.

This does NOT resolve OQ-RECONCILE-HEADLESS (that OQ is Robinhood 15s BARS).
"""
from __future__ import annotations

import pathlib
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .. import paths
from ..edgar_poller import EdgarPoller
from ..edgar_rss import parse_feed

DEFAULT_FEED = (
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent"
    "&type=&company=&owner=include&count=100&output=atom"
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS filing_observations (
    accession_no TEXT PRIMARY KEY,      -- SEC accession; natural dedup key (idempotent re-poll)
    form_type TEXT NOT NULL,            -- 8-K, S-3, 424B5 ... descriptive, NOT a directive
    ticker TEXT,                        -- NULL when the feed omits it (never fabricated)
    company TEXT,
    title TEXT,
    filing_url TEXT,                    -- the one literal source URL (Names Law)
    pub_date TEXT,
    canon_tag TEXT NOT NULL,            -- provenance/reader tag, e.g. 'EDGAR_FILING'
    source TEXT NOT NULL,
    observed_at TEXT NOT NULL
);
"""


def open_observations_db(db_path=None) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path) if db_path is not None else str(paths.OBSERVATIONS_DB))
    con.executescript(SCHEMA)
    return con


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class EdgarObservationRunner:
    """Non-interactive SEC-filing observation runner. `poller`/`feed_url` are
    injectable so the whole engine is testable offline (fixture Atom in, rows out)."""

    def __init__(self, db_conn: sqlite3.Connection, *, poller: Optional[EdgarPoller] = None,
                 feed_url: str = DEFAULT_FEED, canon_tag: str = "EDGAR_FILING"):
        self.conn = db_conn
        self.poller = poller or EdgarPoller()
        self.feed_url = feed_url
        self.canon_tag = canon_tag
        with self.conn:
            self.conn.executescript(SCHEMA)

    def run_ingest(self, *, rng=None) -> Dict[str, Any]:
        result = self.poller.poll(self.feed_url, rng=rng)   # Drill-3 fair-access lives inside poll()
        archived = result.get("archived_path")
        filings = parse_feed(pathlib.Path(archived).read_bytes()) if archived else []
        now = _now_iso()
        new_count = 0
        with self.conn:
            for f in filings:
                acc = f.get("accession_number")
                if not acc:
                    continue
                if self.conn.execute(
                        "SELECT 1 FROM filing_observations WHERE accession_no=?", (acc,)).fetchone():
                    continue  # idempotent re-poll
                self.conn.execute(
                    "INSERT INTO filing_observations (accession_no, form_type, ticker, company, "
                    "title, filing_url, pub_date, canon_tag, source, observed_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (acc, f.get("form_type") or "EDGAR", f.get("ticker"), f.get("company"),
                     f.get("title"), f.get("url"), f.get("pub_date"), self.canon_tag,
                     "SEC_EDGAR_RSS", now))
                new_count += 1
        return {
            "poll_timestamp_utc": now,
            "mode": result.get("mode"),
            "filings_parsed": len(filings),
            "new_observations_logged": new_count,
        }
