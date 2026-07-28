"""
Verify-station audit of Spark's 9 exemplar tickers (OQ-SPARK-DECAY-ARC).
Reads the saved daily-bar payload, derives behavior metrics, cross-references
the 2026-07-27 fundamentals snapshot, and proposes a taxonomy class per ticker.
The instrument decides; Spark's decay numbers never enter this file.
"""
import json, sys, pathlib

hist_path = sys.argv[1]
raw = json.loads(pathlib.Path(hist_path).read_text(encoding="utf-8"))
results = {r["symbol"]: r["bars"] for r in raw["data"]["results"]}

# fundamentals snapshot pulled 2026-07-27 (verify-station lane)
FUND = {
 "CVGI": {"last":4.53,  "cap":180.7e6,"float":26.6e6,"pe":-8.74, "sector":"Producer Mfg",     "hi52":5.88, "lo52":1.29, "hi_dt":"2026-06-03","lo_dt":"2025-11-07","status":"",           "av30d":620182},
 "AIRS": {"last":4.69,  "cap":342.8e6,"float":6.75e6,"pe":-26.51,"sector":"Health Tech",      "hi52":12.00,"lo52":1.51, "hi_dt":"2025-10-27","lo_dt":"2026-03-02","status":"",           "av30d":454217},
 "VTIX": {"last":2.17,  "cap":71.4e6, "float":20.5e6,"pe":-4.23, "sector":"Electronic Tech",  "hi52":92.74,"lo52":1.47, "hi_dt":"2026-01-27","lo_dt":"2026-07-27","status":"",           "av30d":951212},
 "LGVN": {"last":0.6142,"cap":19.4e6, "float":26.1e6,"pe":-0.53, "sector":"Biotech",          "hi52":1.75, "lo52":0.475,"hi_dt":"2025-08-04","lo_dt":"2026-03-06","status":"Noncompliant","av30d":267298},
 "STAK": {"last":2.55,  "cap":123.2e6,"float":None,   "pe":None,  "sector":"Oilfield/China",  "hi52":12.00,"lo52":0.29, "hi_dt":"2026-07-24","lo_dt":"2026-02-05","status":"",           "av30d":7934235},
 "BDSX": {"last":21.86, "cap":246.7e6,"float":4.66e6,"pe":-5.52, "sector":"Diagnostics",      "hi52":24.92,"lo52":5.26, "hi_dt":"2026-07-01","lo_dt":"2026-01-09","status":"",           "av30d":78722},
 "QTTB": {"last":15.14, "cap":453.6e6,"float":9.5e6, "pe":5.71,  "sector":"Biotech",          "hi52":23.57,"lo52":1.57, "hi_dt":"2026-07-14","lo_dt":"2025-08-11","status":"",           "av30d":2502073},
 "RXT":  {"last":3.865, "cap":981.4e6,"float":98e6,  "pe":-6.34, "sector":"Tech Services",    "hi52":8.60, "lo52":0.393,"hi_dt":"2026-06-17","lo_dt":"2026-02-12","status":"",           "av30d":16200043},
 "DAIO": {"last":3.075, "cap":28.9e6, "float":7.9e6, "pe":-3.69, "sector":"Industrial Mach",  "hi52":4.49, "lo52":2.16, "hi_dt":"2026-05-29","lo_dt":"2026-04-06","status":"",           "av30d":45217},
}

def analyze(bars):
    closes = [float(b["close_price"]) for b in bars]
    n = len(closes)
    first, last = closes[0], closes[-1]
    ret = (last - first) / first * 100
    peak, maxdd = closes[0], 0.0
    for c in closes:
        peak = max(peak, c)
        maxdd = min(maxdd, (c - peak) / peak * 100)
    ups = sum(1 for i in range(1, n) if (closes[i]-closes[i-1])/closes[i-1] >= 0.15)
    dns = sum(1 for i in range(1, n) if (closes[i]-closes[i-1])/closes[i-1] <= -0.15)
    return dict(n=n, first=round(first,3), last=round(last,3), ret=round(ret,1),
                maxdd=round(maxdd,1), ups=ups, dns=dns,
                hi=round(max(closes),3), lo=round(min(closes),3))

def propose_class(f, m):
    off_high = 1 - f["last"]/f["hi52"]          # fraction below 52w high
    rng_pos = (f["last"]-f["lo52"])/(f["hi52"]-f["lo52"]) if f["hi52"]>f["lo52"] else 0
    spikes = m["ups"] + m["dns"]
    if off_high >= 0.75 or f["status"] == "Noncompliant":
        return "DILUTION_CYCLE / COLLAPSE", f"{off_high*100:.0f}% off 52w high" + (", NONCOMPLIANT" if f["status"]=="Noncompliant" else "")
    if spikes >= 3:
        return "SERIAL_CATALYST", f"{m['ups']}x +15% & {m['dns']}x -15% single-day moves in window"
    if m["ret"] >= 40 and rng_pos >= 0.6 and spikes <= 2:
        return "SUSTAINED_REGIME", f"+{m['ret']:.0f}% window, {rng_pos*100:.0f}% up its 52w range, few spikes"
    if f["av30d"] < 100000 and (f["hi52"]/f["lo52"]) < 2.5 and abs(m["ret"]) < 30:
        return "STRUCTURAL_NOISE", f"thin ({f['av30d']/1000:.0f}k/d), tight 52w band, flat window"
    return "AMBIGUOUS", f"window {m['ret']:+.0f}%, {spikes} spikes, {rng_pos*100:.0f}% up range"

print(f"{'SYM':<6}{'bars':>5}{'winRet%':>8}{'maxDD%':>8}{'+15d':>5}{'-15d':>5}{'lo..hi(win)':>18}  {'off52wHi':>9}  PROPOSED CLASS")
audit = {}
for sym, f in FUND.items():
    bars = results.get(sym, [])
    if not bars:
        print(f"{sym:<6}  NO BARS RETURNED"); continue
    m = analyze(bars)
    cls, why = propose_class(f, m)
    off_high = (1 - f["last"]/f["hi52"]) * 100
    print(f"{sym:<6}{m['n']:>5}{m['ret']:>8.1f}{m['maxdd']:>8.1f}{m['ups']:>5}{m['dns']:>5}"
          f"{('%.2f..%.2f'%(m['lo'],m['hi'])):>18}  {off_high:>8.0f}%  {cls}  [{why}]")
    audit[sym] = {"exists": True, "metrics": m, "fundamentals": f, "proposed_class": cls, "rationale": why}

out = pathlib.Path(r"C:\cosmos_savant\data\verify")
out.mkdir(parents=True, exist_ok=True)
(out / "spark_ticker_audit_2026-07-28.json").write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")
print("\nwrote", out / "spark_ticker_audit_2026-07-28.json")
