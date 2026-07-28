"""
Seed the ledger with BACKDATED predictions on real Wolf Pack universe
tickers (sub-$200, catalyst names). Entry prices are pulled from real
historical closes; reconciliation then grades them against what the
market ACTUALLY did. Two toy signals compete so the weight divergence
is visible: 'insider_cluster_toy' (predicts +5% in 10d) vs
'coinflip_toy' (same claim, deliberately naive) — the ledger should
learn to trust whichever actually performed, with zero hand-tuning.
"""
import ledger
from reconcile import stooq_closes, close_on_or_after

TICKERS = ["bbai", "ktos", "insw", "fro", "nat", "vg"]
DATES = ["2026-04-06", "2026-04-20", "2026-05-04", "2026-05-18", "2026-06-01"]

con = ledger.connect()
n = 0
for t in TICKERS:
    try:
        closes = stooq_closes(t)
    except Exception as e:
        print(f"skip {t}: {e}")
        continue
    for d in DATES:
        day, px = close_on_or_after(closes, d)
        if px is None:
            continue
        # Signal A: direction 'up', +5% in 10 trading-ish days, claims 60%
        ledger.log_prediction(con, t.upper(), "insider_cluster_toy", "up",
                              14, px, 5.0, 0.60,
                              reasoning=f"toy: cluster-buy proxy @ {day}",
                              ts=day + " 16:00:00")
        # Signal B: same bet but claims 80% — overconfident coinflip
        ledger.log_prediction(con, t.upper(), "coinflip_toy", "up",
                              14, px, 5.0, 0.80,
                              reasoning=f"toy: naive optimism @ {day}",
                              ts=day + " 16:00:00")
        n += 2
print(f"Seeded {n} backdated predictions across {len(TICKERS)} real tickers.")
