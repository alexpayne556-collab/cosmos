"""
Canonical filesystem locations (Section 8.1).

All local state lives under /data. Bookkeeping is LOCAL — we never write
run-tracking into the Google Sheet. Paths are module-level so tests can
monkeypatch them onto a tmp directory for full isolation.
"""
from __future__ import annotations

import pathlib

REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[1]

DATA_DIR: pathlib.Path = REPO_ROOT / "data"
STAGING_MIRROR: pathlib.Path = DATA_DIR / "staging_mirror"   # raw JSONL archive before parsing
QUARANTINE: pathlib.Path = DATA_DIR / "quarantine"           # malformed / unauthorized payloads
ALERTS_PATH: pathlib.Path = DATA_DIR / "alerts.jsonl"        # load-bearing local alert log
ALERT_DEDUPE_STATE: pathlib.Path = DATA_DIR / "alert_dedupe.json"
PROCESSED_RUNS: pathlib.Path = DATA_DIR / "processed_runs.json"
DUCKDB_PATH: pathlib.Path = DATA_DIR / "cosmos.duckdb"       # (reserved; sqlite is the shipped store)
LEDGER_DB: pathlib.Path = DATA_DIR / "cosmos.sqlite"         # descendant event store (ADR-001 migration; sqlite)
SHADOW_BOOK_DB: pathlib.Path = DATA_DIR / "shadow_book.sqlite"  # ADR-029 paper book
OBSERVATIONS_DB: pathlib.Path = DATA_DIR / "observations.sqlite"  # reader/research lane (ADR-026 firewall)

SCHEMAS_DIR: pathlib.Path = REPO_ROOT / "schemas"
CREDENTIALS_DIR: pathlib.Path = REPO_ROOT / "credentials"    # service_account.json (gitignored)


def ensure_dirs() -> None:
    """Idempotently create the directories the runtime writes into."""
    for d in (DATA_DIR, STAGING_MIRROR, QUARANTINE):
        d.mkdir(parents=True, exist_ok=True)
