"""
HERMES PHASE 1 — RECONCILIATION ENGINE
Finds matured predictions, fetches real prices, grades them,
updates signal weights (slow EWMA + min-sample guard), logs every change.
This script is what turns the diary into a mind.
"""
import time, urllib.request, csv, io
from datetime import datetime, timedelta
import ledger

ALPHA = 0.10        # EWMA learning rate: slow. One bad week can't kill a signal.
MIN_SAMPLES = 10    # below this, weight stays provisional (still logged, flagged)

def stooq_closes(ticker):
    """Free daily closes via Yahoo chart API (Stooq 503s from here).
    Name kept for compatibility. Returns {date: close}."""
    import json
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/"
           f"{ticker.upper()}?range=1y&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    d = json.load(urllib.request.urlopen(req, timeout=20))
    r = d["chart"]["result"][0]
    out = {}
    for ts, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]):
        if c is not None:
            out[datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")] = float(c)
    return out

def close_on_or_after(closes, date_str, max_slip=5):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    for i in range(max_slip + 1):
        k = (d + timedelta(days=i)).strftime("%Y-%m-%d")
        if k in closes:
            return k, closes[k]
    return None, None

def reconcile(con, today=None, verbose=True):
    today = today or time.strftime("%Y-%m-%d")
    rows = con.execute(
        """SELECT id,ts_logged,ticker,signal,direction,horizon_days,
                  entry_price,target_move_pct,stated_confidence
           FROM predictions WHERE resolved=0""").fetchall()
    price_cache, n_resolved = {}, 0
    for (pid, ts_logged, ticker, signal, direction, horizon,
         entry, target, conf) in rows:
        mature = (datetime.strptime(ts_logged[:10], "%Y-%m-%d")
                  + timedelta(days=horizon)).strftime("%Y-%m-%d")
        if mature > today:
            continue  # not ripe yet
        if ticker not in price_cache:
            try:
                price_cache[ticker] = stooq_closes(ticker)
            except Exception as e:
                print(f"  [skip] {ticker}: price fetch failed ({e})")
                continue
        exit_date, exit_px = close_on_or_after(price_cache[ticker], mature)
        if exit_px is None:
            continue
        move = (exit_px - entry) / entry * 100.0
        hit = int(move >= target) if direction == "up" else int(move <= -target)
        brier = (conf - hit) ** 2
        con.execute(
            """UPDATE predictions SET resolved=1, ts_resolved=?, exit_price=?,
               realized_move_pct=?, hit=?, brier=? WHERE id=?""",
            (exit_date, exit_px, round(move, 2), hit, round(brier, 4), pid))
        # --- weight update: slow EWMA toward realized hit rate ---
        old_w, n, sb = con.execute(
            "SELECT weight,n_resolved,sum_brier FROM signal_weights WHERE signal=?",
            (signal,)).fetchone()
        new_w = old_w + ALPHA * (hit - old_w)
        con.execute(
            """UPDATE signal_weights SET weight=?, n_resolved=?, sum_brier=?,
               last_updated=? WHERE signal=?""",
            (round(new_w, 4), n + 1, sb + brier, today, signal))
        flag = "" if n + 1 >= MIN_SAMPLES else " [provisional: n<10]"
        reason = (f"{ticker} {direction} {target:+.1f}% in {horizon}d: "
                  f"realized {move:+.2f}% -> {'HIT' if hit else 'MISS'}"
                  f" (claimed p={conf:.2f}, brier={brier:.3f}){flag}")
        con.execute(
            """INSERT INTO weight_change_log (ts,signal,old_weight,new_weight,
               prediction_id,reason) VALUES (?,?,?,?,?,?)""",
            (today, signal, round(old_w, 4), round(new_w, 4), pid, reason))
        n_resolved += 1
        if verbose:
            print(f"  #{pid:>3} {signal:<28} {reason}")
    con.commit()
    return n_resolved

def report(con):
    print("\n=== SIGNAL LEDGER (the mind's current beliefs) ===")
    print(f"{'signal':<28}{'weight':>8}{'n':>5}{'avg_brier':>11}  status")
    for s, w, n, sb in con.execute(
            "SELECT signal,weight,n_resolved,sum_brier FROM signal_weights "
            "ORDER BY weight DESC"):
        ab = sb / n if n else float("nan")
        status = "EARNED" if n >= 10 else "provisional"
        print(f"{s:<28}{w:>8.3f}{n:>5}{ab:>11.3f}  {status}")

if __name__ == "__main__":
    con = ledger.connect()
    print(f"Reconciling as of {time.strftime('%Y-%m-%d')} ...")
    n = reconcile(con)
    print(f"\n{n} predictions resolved.")
    report(con)
