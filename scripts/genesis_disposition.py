"""
ADR-030 step 4 — one-time disposition of the ten Section-5 GENESIS rows.

Sets brier_eligibility per the ADR table, withdraws AMKR's Brier (retaining its
outcome grade), and logs a death certificate for the first Brier number. Also
prints the gate's INDEPENDENT verdict on AMKR as a cross-check.
"""
import pathlib
import sys
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from cosmos import ledger, reconcile          # noqa: E402
from cosmos.persistence import atomic_write_text  # noqa: E402

con = ledger.connect()
print(f"GENESIS import: {ledger.genesis_import(con)} rows")

# --- gate cross-check on AMKR (the matured row) ---------------------------- #
amkr_bar = [{"high_price": "60.72", "low_price": "54.92", "close_price": "55.18",
             "begins_at": "2026-07-28T05:08:00Z"}]   # extended breach of 58.50
t0d, t0at = ledger.t0_distribution(con, "gen-amkr")
amkr_pred = next(p for p in ledger.open_predictions(con) if p["prediction_id"] == "gen-amkr")
gate = reconcile.grade(amkr_pred, amkr_bar, t0_distribution=t0d,
                       distribution_logged_at=t0at, prediction_logged_at=amkr_pred["ts_logged"])
print(f"AMKR gate verdict: rule={gate.first_touch_rule} eligibility={gate.brier_eligibility} "
      f"brier={gate.brier}  (distribution stamped {t0at}, outcome determined {gate.outcome_determined_at})")

# --- explicit disposition per the ADR-030 table ---------------------------- #
# AMKR: resolved, outcome RETAINED, Brier WITHDRAWN.
con.execute(
    "UPDATE predictions SET resolved=1, outcome_class='down', first_touch_rule='INVALIDATION_FIRST', "
    "settle_price=55.18, outcome_determined_at='2026-07-28T05:08:00Z', brier=NULL, brier_excluded=1, "
    "brier_eligibility='EXCLUDED_POST_HOC' WHERE prediction_id='gen-amkr'")
DISPOSITION = {
    "gen-apld": "ELIGIBLE_LATE_PRIOR", "gen-ba": "ELIGIBLE_LATE_PRIOR",
    "gen-pypl": "ELIGIBLE_LATE_PRIOR", "gen-ko": "ELIGIBLE_LATE_PRIOR",
    "gen-stx": "ELIGIBLE_LATE_PRIOR",
    "gen-cls": "EXCLUDED_NO_DISTRIBUTION", "gen-ne": "EXCLUDED_NO_DISTRIBUTION",
    "gen-cdns": "EXCLUDED_NO_DISTRIBUTION", "gen-smh": "EXCLUDED_NO_DISTRIBUTION",
}
for pid, elig in DISPOSITION.items():
    con.execute("UPDATE predictions SET brier_eligibility=?, brier_excluded=? WHERE prediction_id=?",
                (elig, int(elig.startswith("EXCLUDED")), pid))
con.commit()

# --- exclusion counts per generator ---------------------------------------- #
per_gen = defaultdict(Counter)
for g, t, e in con.execute("SELECT generator_id, ticker, brier_eligibility FROM predictions"):
    per_gen[g][e] += 1
print("\n=== brier_eligibility per generator (after disposition) ===")
for g in sorted(per_gen):
    c = per_gen[g]
    excl = sum(v for k, v in c.items() if k.startswith("EXCLUDED"))
    print(f"  {g:<13} {dict(c)}  -> EXCLUDED {excl}/{sum(c.values())}")

print("\n=== Brier aggregates (both, always — ADR-030 R4) ===")
print(" ", reconcile.brier_aggregates(con))

# --- death certificate ----------------------------------------------------- #
cert = """# DEATH CERTIFICATE

- id:            DC-2026-07-28-001
- killed_on:     2026-07-28
- subject:       AMKR first Brier score (~0.892), computed 2026-07-28 pre-ADR-030
- cause_of_death: prior-commitment violation (ADR-030 R1). The distribution was
                 authored on 2026-07-28, AFTER AMKR had already resolved
                 INVALIDATION_FIRST in the extended session (official close 60.71
                 -> extended print 55.18, through the 58.50 invalidation).
- disposition:   EXCLUDED_POST_HOC. The gate reached the same verdict independently.
- what_survives: AMKR's outcome grade (down / INVALIDATION_FIRST), the extended-
                 session prints, and the empirical LULD confirmation. All are
                 measured facts and remain in the atlas. Only the score is withdrawn.
- ratified_by:   tyr
- adr:           ADR-030
"""
out = pathlib.Path(r"C:\cosmos_savant\data\death_certificates\2026-07-28_first_brier.md")
out.parent.mkdir(parents=True, exist_ok=True)
atomic_write_text(out, cert)
print(f"\ndeath certificate written: {out}")
