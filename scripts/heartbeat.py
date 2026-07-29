"""
scripts/heartbeat.py — liveness beat for the Cosmos Savant ledger.

Spec (Tyr, 2026-07-29, pasted directly). NOTE: the cited `HANDOFF_2026-07-28.md`
never landed in the repo (a chat-side artifact); this is built to the spec Tyr
pasted, NOT reconstructed from a phantom document.

  1. Open data/cosmos.sqlite; create a `heartbeat` table if absent
     (ts_utc, ledger_rows, resolved, pending, status, note).
  2. Count total predictions, resolved, pending.
  3. Append ONE row. status = "NO_NEW_DATA" when nothing matured — a valid result,
     NOT a failure.
  4. Print the row. Exit 0 on success, non-zero on a real error; never exit 0 on a
     silent failure.

Two properties beyond the literal steps, both load-bearing:
  * Append-only. A beat never UPDATEs/DELETEs a prior heartbeat row, so running
    twice appends exactly two rows and mutates neither (spec step 5).
  * "Matured" is defined as `resolved` RISING since the last heartbeat. The first
    beat therefore establishes a baseline and reports NO_NEW_DATA rather than a
    false MATURED off pre-existing GENESIS resolutions. The spec named the status
    but did not pin the predicate; this is the one interpretive choice, surfaced
    to Tyr rather than assumed silently.

Counts come straight from the ledger (measured) and are never invented; a beat
that finds an empty ledger is NO_NEW_DATA, not an error.
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from cosmos import ledger  # noqa: E402

HEARTBEAT_SCHEMA = """
CREATE TABLE IF NOT EXISTS heartbeat (
    ts_utc      TEXT,
    ledger_rows INTEGER,
    resolved    INTEGER,
    pending     INTEGER,
    status      TEXT,
    note        TEXT
);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_table(con) -> None:
    con.executescript(HEARTBEAT_SCHEMA)


def counts(con):
    """(total, resolved, pending) straight from the ledger. pending is derived as
    total - resolved so the three always reconcile even if `resolved` ever held a
    value other than 0/1."""
    total = con.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    resolved = con.execute("SELECT COUNT(*) FROM predictions WHERE resolved <> 0").fetchone()[0]
    return total, resolved, total - resolved


def classify(con, resolved: int):
    """(status, note). NO_NEW_DATA when nothing matured since the last beat."""
    row = con.execute("SELECT resolved FROM heartbeat ORDER BY rowid DESC LIMIT 1").fetchone()
    if row is None:
        return "NO_NEW_DATA", f"first heartbeat; baseline resolved={resolved}"
    prev = row[0]
    delta = resolved - prev
    if delta > 0:
        return "MATURED", f"{delta} newly resolved since last heartbeat"
    if delta == 0:
        return "NO_NEW_DATA", f"no maturation since last heartbeat (resolved={resolved})"
    return "ANOMALY", f"resolved fell {prev}->{resolved}; append-only ledger should not shrink"


def beat(con) -> dict:
    """Read counts, classify, append exactly ONE heartbeat row, return it as a
    dict. Never mutates a prior row."""
    ensure_table(con)
    total, resolved, pending = counts(con)
    status, note = classify(con, resolved)
    ts = _now_iso()
    con.execute(
        "INSERT INTO heartbeat (ts_utc, ledger_rows, resolved, pending, status, note) "
        "VALUES (?,?,?,?,?,?)",
        (ts, total, resolved, pending, status, note),
    )
    con.commit()
    return {"ts_utc": ts, "ledger_rows": total, "resolved": resolved,
            "pending": pending, "status": status, "note": note}


def main() -> int:
    con = ledger.connect()  # real data/cosmos.sqlite (gitignored); ledger schema ensured
    try:
        row = beat(con)
    finally:
        con.close()
    print(json.dumps(row, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # a real error must never masquerade as exit 0
        print(f"heartbeat FAILED: {exc!r}", file=sys.stderr)
        raise SystemExit(1)
