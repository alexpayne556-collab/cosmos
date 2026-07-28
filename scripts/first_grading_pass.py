"""
First automated grading pass (loop demonstration on live data).

GENESIS-imports the ten Section-5 rows, then reconciles. AMKR is the one matured
row: its invalidation (58.50) was gapped through in the extended session — the
decisive, instrument-sourced fact is the live quote's extended print (last
non-reg 55.18, bid 54.92 at 2026-07-28T05:08Z). We feed the grader an
extended-session bar summarizing that (high 60.72 < 63.50 target; low 54.92 <=
58.50 invalidation) -> INVALIDATION_FIRST -> LOSS.

CAVEAT (honest): this uses the extended low from the quote, not the full Jul-27
15s series (~3,800 bars). Outcome direction is unambiguous (close 60.71 never
reached target; extended breach of invalidation). Brier is None — the GENESIS
generators never supplied a distribution and the verify station will not
fabricate one (ADR-002; OQ-GENESIS-DISTRIBUTIONS).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from cosmos import ledger, reconcile  # noqa: E402

con = ledger.connect()  # real data/cosmos.sqlite (gitignored)
n = ledger.genesis_import(con)
print(f"GENESIS: imported {n} rows (idempotent re-runs add 0)")

AMKR_EXTENDED_BAR = [{
    "high_price": "60.72", "low_price": "54.92", "close_price": "55.18",
    "begins_at": "2026-07-28T05:08:00Z",
}]


def bar_provider(pred):
    return AMKR_EXTENDED_BAR if pred["ticker"] == "AMKR" else []


summary = reconcile.reconcile(con, bar_provider, now_ts="2026-07-28T06:00:00Z")
print("resolved   :", summary["resolved"])
print("weight_delta:", summary["weight_changes"])
print("\n=== ledger state (resolved first) ===")
print(f"{'ticker':<6}{'gen':<14}{'res':>4}{'outcome':>9}{'rule':>22}{'brier':>8}  dist")
for t, g, r, oc, ft, br, dist in con.execute(
        "SELECT ticker, generator_id, resolved, outcome_class, first_touch_rule, brier, distribution "
        "FROM predictions ORDER BY resolved DESC, ticker"):
    print(f"{t:<6}{g:<14}{r:>4}{str(oc):>9}{str(ft):>22}{str(br):>8}  {dist}")
