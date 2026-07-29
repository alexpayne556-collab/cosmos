from __future__ import annotations

from cosmos.edgar_poller import EdgarPoller
from cosmos.ingestion.edgar_runner import EdgarObservationRunner, open_observations_db
from tests.test_edgar_rss import SAMPLE_ATOM


def _runner():
    # inject a fetch so EdgarPoller (Drill-3 machinery intact) archives fixture bytes,
    # which the runner reads back and parses — no network.
    poller = EdgarPoller(fetch=lambda url: (200, SAMPLE_ATOM), sleep=lambda d: None)
    return EdgarObservationRunner(open_observations_db(":memory:"), poller=poller)


def test_logs_filings_as_observations():
    r = _runner()
    summary = r.run_ingest()
    assert summary["new_observations_logged"] == 2      # id-less entry skipped
    row = r.conn.execute(
        "SELECT form_type, ticker, company, canon_tag FROM filing_observations "
        "ORDER BY accession_no").fetchone()
    assert row[0] == "8-K" and row[1] is None and row[2] == "ACME CORP"
    assert row[3] == "EDGAR_FILING"                     # provenance tag, not a directive


def test_idempotent_repoll():
    r = _runner()
    r.run_ingest()
    assert r.run_ingest()["new_observations_logged"] == 0


def test_no_directive_or_prediction_columns():
    r = _runner()
    cols = [c[1] for c in r.conn.execute("PRAGMA table_info(filing_observations)").fetchall()]
    for forbidden in ("action_tag", "direction", "distribution", "brier", "target_price"):
        assert forbidden not in cols                    # observations != directives/predictions


def test_separate_from_prediction_ledger():
    r = _runner()
    assert r.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'").fetchone() is None
