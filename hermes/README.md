# HERMES PHASE 1 — proven working 2026-07-04
Ran end-to-end in a live container against real market data before delivery.

## Files
- ledger.py     — SQLite schema + prediction logger (permanent memory, never resets)
- reconcile.py  — grades matured predictions vs real prices, EWMA weight updates
                  (alpha=0.10, min 10 samples before a weight is EARNED),
                  every change logged with a reason in weight_change_log
- governor.py   — sizing rules: 5% cap, max 3 positions, no scaling after wins.
                  Confidence is NOT an input. Structurally separate from signals.
- seed_demo.py  — backdated demo predictions (delete for production use)
- hermes.db     — the demo run's ledger (inspect with any SQLite browser)

## Proof-run results (60 real resolved predictions, BBAI/KTOS/INSW/FRO/NAT/VG)
- Base rate discovered: naive "+5% in 14d" long hits ~30% of the time.
  That is the bar every real signal must beat.
- Calibration caught overconfidence with no human input: two signals with
  IDENTICAL picks, one claiming 60%, one claiming 80% -> avg Brier 0.313 vs
  0.500. The ledger learned the humbler forecaster was less wrong.
- Governor blocked: a half-the-bankroll bet (148 -> 14), a post-win
  scale-up (30 -> 14), and a 4th simultaneous position (-> 0).

## Deploy on desktop (C:\Users\alexp\AppData\Local\hermes)
1. Copy these files next to sensory_v2.py (same folder or package).
2. Point real signals at ledger.log_prediction(...) — replace the toys.
3. Task Scheduler: run `python reconcile.py` nightly after close.
4. All order sizing goes through governor.approve(). No exceptions,
   especially the exciting ones.
5. Paper predictions only until >=10 resolved per signal (EARNED status).
