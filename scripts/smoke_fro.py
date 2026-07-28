"""
Phase-1 instrument smoke test — FRO.
Proves the hands->memory path: live Robinhood MCP reads (captured verbatim
by the operator) are archived raw to /data/staging_mirror as JSONL, read
back off disk, and parsed. No network here; the raw payloads are the exact
tool responses from get_equity_quotes / get_equity_historicals / get_equity_fundamentals.
"""
import json, pathlib, hashlib
from datetime import datetime, timezone

BASE = pathlib.Path(r"C:\cosmos_savant\data\staging_mirror")
BASE.mkdir(parents=True, exist_ok=True)
pathlib.Path(r"C:\cosmos_savant\data\quarantine").mkdir(parents=True, exist_ok=True)

# --- raw payloads exactly as returned by the Robinhood MCP (2026-07-27 session) ---
QUOTE = r'''{"results":[{"quote":{"symbol":"FRO","last_trade_price":"38.580000","venue_last_trade_time":"2026-07-27T19:59:58.456455168Z","last_non_reg_trade_price":"38.600000","venue_last_non_reg_trade_time":"2026-07-28T01:57:49.760204411Z","adjusted_previous_close":"38.590000","previous_close":"38.590000","previous_close_date":"2026-07-27","bid_price":"37.600000","venue_bid_time":"2026-07-28T01:57:50.76292Z","ask_price":"38.600000","venue_ask_time":"2026-07-28T01:57:50.76292Z","has_traded":true,"state":"active"},"close":{"symbol":"FRO","date":"2026-07-27","price":"38.59","interpolated":false,"source":"sip-list-exchange-close"}}]}'''
HIST = r'''{"results":[{"symbol":"FRO","interval":"15second","bounds":"regular","bars":[{"begins_at":"2026-07-27T19:55:00Z","open_price":"38.660000","close_price":"38.670000","high_price":"38.670000","low_price":"38.660000","volume":635,"session":"reg"},{"begins_at":"2026-07-27T19:55:15Z","open_price":"38.670000","close_price":"38.640000","high_price":"38.680000","low_price":"38.640000","volume":2480,"session":"reg"},{"begins_at":"2026-07-27T19:55:30Z","open_price":"38.640000","close_price":"38.650000","high_price":"38.650000","low_price":"38.640000","volume":571,"session":"reg"},{"begins_at":"2026-07-27T19:55:45Z","open_price":"38.655000","close_price":"38.660000","high_price":"38.660000","low_price":"38.650000","volume":881,"session":"reg"},{"begins_at":"2026-07-27T19:56:00Z","open_price":"38.660000","close_price":"38.650000","high_price":"38.660000","low_price":"38.650000","volume":768,"session":"reg"},{"begins_at":"2026-07-27T19:56:15Z","open_price":"38.660000","close_price":"38.640000","high_price":"38.660000","low_price":"38.630000","volume":2320,"session":"reg"},{"begins_at":"2026-07-27T19:56:30Z","open_price":"38.640000","close_price":"38.640000","high_price":"38.645000","low_price":"38.640000","volume":1010,"session":"reg"},{"begins_at":"2026-07-27T19:56:45Z","open_price":"38.630000","close_price":"38.640000","high_price":"38.640000","low_price":"38.630000","volume":1887,"session":"reg"},{"begins_at":"2026-07-27T19:57:00Z","open_price":"38.640000","close_price":"38.650000","high_price":"38.680000","low_price":"38.640000","volume":2894,"session":"reg"},{"begins_at":"2026-07-27T19:57:15Z","open_price":"38.645000","close_price":"38.615000","high_price":"38.650000","low_price":"38.590000","volume":17783,"session":"reg"},{"begins_at":"2026-07-27T19:57:30Z","open_price":"38.615000","close_price":"38.625000","high_price":"38.645000","low_price":"38.610000","volume":3624,"session":"reg"},{"begins_at":"2026-07-27T19:57:45Z","open_price":"38.625000","close_price":"38.630000","high_price":"38.640000","low_price":"38.620500","volume":3485,"session":"reg"},{"begins_at":"2026-07-27T19:58:00Z","open_price":"38.630000","close_price":"38.620000","high_price":"38.630000","low_price":"38.600000","volume":2868,"session":"reg"},{"begins_at":"2026-07-27T19:58:15Z","open_price":"38.625000","close_price":"38.610000","high_price":"38.625000","low_price":"38.610000","volume":5252,"session":"reg"},{"begins_at":"2026-07-27T19:58:30Z","open_price":"38.600000","close_price":"38.565000","high_price":"38.610000","low_price":"38.565000","volume":2830,"session":"reg"},{"begins_at":"2026-07-27T19:58:45Z","open_price":"38.570000","close_price":"38.565000","high_price":"38.575000","low_price":"38.565000","volume":3006,"session":"reg"},{"begins_at":"2026-07-27T19:59:00Z","open_price":"38.565000","close_price":"38.530000","high_price":"38.565000","low_price":"38.525000","volume":11692,"session":"reg"},{"begins_at":"2026-07-27T19:59:15Z","open_price":"38.530000","close_price":"38.600000","high_price":"38.600000","low_price":"38.530000","volume":6365,"session":"reg"},{"begins_at":"2026-07-27T19:59:30Z","open_price":"38.605000","close_price":"38.570000","high_price":"38.605000","low_price":"38.560000","volume":7390,"session":"reg"},{"begins_at":"2026-07-27T19:59:45Z","open_price":"38.570000","close_price":"38.580000","high_price":"38.605000","low_price":"38.570000","volume":8886,"session":"reg"}]}]}'''
FUND = r'''{"results":[{"symbol":"FRO","open":"38.300000","high":"39.290000","low":"38.060000","volume":"1583667.000000","market_cap":"9247838216.431890","pb_ratio":"2.912410","pe_ratio":"9.144361","shares_outstanding":"239705500.685119","float":"143155939.166000","high_52_weeks":"43.100000","low_52_weeks":"18.260000","average_volume_30_days":"2457399.465680","dividend_yield":"8.420769","sector":"Transportation","industry":"Marine Shipping"}]}'''

fetched_at = datetime.now(timezone.utc).isoformat()
records = [
    {"kind": "quote",          "symbol": "FRO", "tool": "get_equity_quotes",       "fetched_at_utc": fetched_at, "payload": json.loads(QUOTE)},
    {"kind": "historicals_15s","symbol": "FRO", "tool": "get_equity_historicals",  "fetched_at_utc": fetched_at, "payload": json.loads(HIST)},
    {"kind": "fundamentals",   "symbol": "FRO", "tool": "get_equity_fundamentals", "fetched_at_utc": fetched_at, "payload": json.loads(FUND)},
]

# WRITE raw archive (Section 8.1: archived as raw JSONL before parsing)
raw_path = BASE / "smoke_FRO_20260727T2000Z.jsonl"
with raw_path.open("w", encoding="utf-8") as f:
    for r in records:
        f.write(json.dumps(r) + "\n")

# READ BACK off disk and verify round-trip
loaded = [json.loads(l) for l in raw_path.read_text(encoding="utf-8").splitlines() if l.strip()]
assert len(loaded) == 3, "record count mismatch"
q    = loaded[0]["payload"]["results"][0]
bars = loaded[1]["payload"]["results"][0]["bars"]
fd   = loaded[2]["payload"]["results"][0]

interp = sum(1 for b in bars if b.get("interpolated"))
nonreg = sum(1 for b in bars if b["session"] != "reg")
first_open = float(bars[0]["open_price"]); last_close = float(bars[-1]["close_price"])
win_move = (last_close - first_open) / first_open * 100
win_vol  = sum(b["volume"] for b in bars)

parsed = {
    "symbol": "FRO", "fetched_at_utc": fetched_at,
    "official_close_verified": {"price": float(q["close"]["price"]), "date": q["close"]["date"], "source": q["close"]["source"]},
    "last_trade_price": float(q["quote"]["last_trade_price"]),
    "bars_15s": {"count": len(bars), "interpolated": interp, "non_regular": nonreg,
                 "window": [bars[0]["begins_at"], bars[-1]["begins_at"]],
                 "window_move_pct": round(win_move, 3), "window_volume": win_vol},
    "precursor_snapshot": {"float": float(fd["float"]), "market_cap": float(fd["market_cap"]),
                           "shares_outstanding": float(fd["shares_outstanding"]),
                           "pe": float(fd["pe_ratio"]), "pb": float(fd["pb_ratio"]),
                           "div_yield_pct": float(fd["dividend_yield"]),
                           "avg_vol_30d": float(fd["average_volume_30_days"]),
                           "range_52w": [float(fd["low_52_weeks"]), float(fd["high_52_weeks"])],
                           "sector": fd["sector"], "industry": fd["industry"]},
    "content_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest()[:16],
}
parsed_path = BASE / "smoke_FRO_20260727T2000Z.parsed.json"
parsed_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")

ps = parsed["precursor_snapshot"]
print("=== SMOKE TEST -- FRO -- hands proven on live data ===")
print(f"archive written : {raw_path}  ({raw_path.stat().st_size} bytes, sha256:{parsed['content_sha256']})")
print(f"read-back       : {len(loaded)} records reloaded from disk OK")
print(f"official close  : ${parsed['official_close_verified']['price']}  ({parsed['official_close_verified']['date']}, {parsed['official_close_verified']['source']})  [verify-station lane]")
print(f"live last trade : ${parsed['last_trade_price']}")
print(f"15s bars        : {len(bars)} bars, interpolated={interp}, non-reg={nonreg}, window {bars[0]['begins_at'][11:19]}-{bars[-1]['begins_at'][11:19]}Z")
print(f"window move/vol : {win_move:+.3f}% on {win_vol:,} sh")
print(f"precursor       : float={ps['float']:,.0f}  cap=${ps['market_cap']/1e9:.2f}B  PE={ps['pe']:.2f}  divYld={ps['div_yield_pct']:.2f}%  52w={ps['range_52w']}")
print(f"parsed written  : {parsed_path}")
print("--- /data/staging_mirror listing ---")
for p in sorted(BASE.iterdir()):
    print(f"  {p.name:<40} {p.stat().st_size:>7} bytes")
