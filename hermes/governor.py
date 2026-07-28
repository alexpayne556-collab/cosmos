"""
HERMES PHASE 1 — SIZING GOVERNOR
Deterministic. Auditable. Structurally separate from signal scoring.
The organ that decides HOW MUCH must never be reachable by the organ
that is excited about HOW GOOD. Confidence is not an input here.
"""
import time
import ledger

MAX_FRACTION = 0.05        # hard cap: 5% of bankroll per position
MAX_OPEN_POSITIONS = 3
NO_SCALING_AFTER_WINS = True   # next bet sized off the RULE, not the high

def approve(con, ticker, requested_dollars, bankroll,
            open_positions, last_approved=None):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    cap = round(bankroll * MAX_FRACTION, 2)
    approved, rule = requested_dollars, "within_limits"
    if open_positions >= MAX_OPEN_POSITIONS:
        approved, rule = 0.0, f"REJECT: max {MAX_OPEN_POSITIONS} open positions"
    elif requested_dollars > cap:
        approved, rule = cap, f"CAPPED to {MAX_FRACTION:.0%} of bankroll (${cap})"
    if (NO_SCALING_AFTER_WINS and last_approved is not None
            and approved > last_approved):
        approved, rule = last_approved, \
            f"NO-SCALING rule: held to last size ${last_approved} (wins don't vote)"
    con.execute(
        "INSERT INTO sizing_log (ts,ticker,requested_dollars,approved_dollars,"
        "rule_applied) VALUES (?,?,?,?,?)",
        (ts, ticker, requested_dollars, approved, rule))
    con.commit()
    return approved, rule

if __name__ == "__main__":
    con = ledger.connect()
    bank = 296.0  # current Robinhood roll
    print(f"Bankroll ${bank:.2f} | cap/position ${bank*MAX_FRACTION:.2f}\n")
    tests = [
        ("BBAI",  14.0, 0, None),    # normal ask
        ("KTOS", 148.0, 1, 14.0),    # the half-the-house ask
        ("INSW",  30.0, 1, 14.0),    # post-win scale-up attempt
        ("FRO",   14.0, 3, 14.0),    # too many positions open
    ]
    for tick, ask, open_n, last in tests:
        ok, rule = approve(con, tick, ask, bank, open_n, last)
        print(f"  {tick:<5} asked ${ask:>7.2f} -> approved ${ok:>6.2f}  [{rule}]")
