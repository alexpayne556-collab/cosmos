"""
scripts/smoke_keys.py — Phase 2 (BLOOD) capability smoke test.

ONE cheap authenticated call per provider -> a MEASURED / FAILED capability
table. This is the Gate-2 artifact. Reusable: re-run after Tyr rotates the keys.

STANDING LAW 6 (keys): booleans + statuses only, NEVER a key value. Two guards:
  * keys go into the request URL/headers but the printed URL is never emitted;
  * a final _scrub() pass replaces every loaded key value with '***' in EVERY
    string printed — several providers echo the offending token back in the
    error body, and this output lands in a PUBLIC repo's chat.

MEASURED is an AFFIRMATIVE predicate, not HTTP 200. Many of these APIs return
200 with an error/limit body (Alpha Vantage, FMP, NewsData, Polygon, a Finnhub
dud). So MEASURED := 200 AND the expected data key present with real content;
anything ambiguous is NOT MEASURED. That is the "a wrong number that looks
measured is worse than no number" rule applied to our own capability table.

Notes are tri-state so a working key on a paywalled endpoint is not condemned:
  OK                    call succeeded, real data returned
  AUTH-FAIL             the key was rejected
  PLAN-OR-RATE-LIMIT    the key is valid but the endpoint/quota is restricted

NOTE: these are the PRE-ROTATION (chat-exposed) keys. This measures the
PLUMBING — capability survives rotation; only the secret changes. Re-run after
rotation to confirm the new secrets.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from cosmos import config  # noqa: E402

TIMEOUT = 20


def _get(url, headers=None):
    """(status, body). Raises only on network-level failure (caught by run())."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read(65536).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(65536).decode("utf-8", "replace")


def _json(body):
    try:
        return json.loads(body)
    except Exception:
        return None


# ---- one affirmative check per provider; each returns (verdict, note, status) ----

def chk_gemini(key):
    # AQ.* is NOT a standard AIza key; try three auth mechanisms, report which works.
    base = "https://generativelanguage.googleapis.com/v1beta/models"
    attempts = [("query", base + "?key=" + key, None),
                ("x-goog-api-key", base, {"x-goog-api-key": key}),
                ("bearer", base, {"Authorization": "Bearer " + key})]
    last = (None, "query")
    for mech, url, hdr in attempts:
        st, body = _get(url, hdr)
        j = _json(body)
        if st == 200 and isinstance(j, dict) and j.get("models"):
            return "MEASURED", f"OK via {mech} ({len(j['models'])} models)", st
        last = (st, mech)
    return "FAILED", f"AUTH-FAIL (all mechanisms; last {last[1]} http {last[0]})", last[0]


def chk_fred(key):
    st, body = _get("https://api.stlouisfed.org/fred/series/observations"
                    f"?series_id=BAMLH0A0HYM2&api_key={key}&file_type=json&limit=1")
    j = _json(body)
    if st == 200 and isinstance(j, dict) and j.get("observations"):
        return "MEASURED", "OK (1 obs BAMLH0A0HYM2)", st
    if st == 400:
        return "FAILED", "AUTH-FAIL (400 api_key not registered)", st
    return "FAILED", f"http {st}", st


def chk_datagov(key):
    st, body = _get(f"https://api.nasa.gov/planetary/apod?api_key={key}")
    j = _json(body)
    if st == 200 and isinstance(j, dict) and (j.get("url") or j.get("title")):
        return "MEASURED", "OK (NASA APOD via api.data.gov)", st
    st2, body2 = _get(f"https://api.govinfo.gov/collections?api_key={key}")  # 2nd data.gov service
    j2 = _json(body2)
    if st2 == 200 and isinstance(j2, dict) and j2.get("collections"):
        return "MEASURED", "OK (GovInfo; NASA rejected)", st2
    return "FAILED", f"AUTH-FAIL (NASA {st}, GovInfo {st2})", st


def chk_polygon(key):
    st, body = _get(f"https://api.polygon.io/v3/reference/tickers?limit=1&apiKey={key}")
    j = _json(body)
    if st == 200 and isinstance(j, dict) and j.get("status") == "OK" and j.get("results"):
        return "MEASURED", "OK (reference/tickers)", st
    if st in (401, 403):
        return "FAILED", f"AUTH-FAIL (http {st})", st
    if st == 429:
        return "FAILED", "PLAN-OR-RATE-LIMIT (429)", st
    return "FAILED", f"http {st}", st


def chk_fmp(key):
    st = None
    for label, url in [("v3", f"https://financialmodelingprep.com/api/v3/quote-short/AAPL?apikey={key}"),
                       ("stable", f"https://financialmodelingprep.com/stable/quote?symbol=AAPL&apikey={key}")]:
        st, body = _get(url)
        j = _json(body)
        if st == 200 and isinstance(j, list) and j and isinstance(j[0], dict) and "price" in j[0]:
            return "MEASURED", f"OK ({label} quote AAPL)", st
        if isinstance(j, dict) and "Error Message" in j:
            low = j["Error Message"].lower()
            if "legacy" in low:
                continue  # legacy v3 retired 2025-08-31; fall through to the stable domain
            if any(w in low for w in ("limit", "plan", "upgrade", "exclusive", "subscription")):
                return "FAILED", f"PLAN-OR-RATE-LIMIT ({label})", st
            return "FAILED", f"AUTH-FAIL ({label})", st
        if st in (401, 403):
            return "FAILED", f"AUTH-FAIL ({label} http {st})", st
    return "FAILED", f"http/endpoint (v3+stable failed, last {st})", st


def chk_alpha_vantage(key):
    st, body = _get(f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM&apikey={key}")
    j = _json(body)
    if st == 200 and isinstance(j, dict):
        gq = j.get("Global Quote")
        if gq and gq.get("05. price"):
            return "MEASURED", "OK (GLOBAL_QUOTE IBM)", st
        for k in ("Information", "Note", "Error Message"):
            if k in j:
                low = j[k].lower()
                if any(w in low for w in ("rate limit", "premium", "per day", "thank you", "25 requests")):
                    return "FAILED", "PLAN-OR-RATE-LIMIT", st
                if any(w in low for w in ("invalid", "apikey", "api key")):
                    return "FAILED", "AUTH-FAIL", st
                return "FAILED", "AMBIGUOUS (200 non-data body)", st
    return "FAILED", f"http {st}", st


def chk_eodhd(key):
    st, body = _get(f"https://eodhd.com/api/real-time/AAPL.US?api_token={key}&fmt=json")
    j = _json(body)
    if st == 200 and isinstance(j, dict) and ("close" in j or "code" in j):
        return "MEASURED", "OK (real-time AAPL.US)", st
    if st in (401, 403):
        return "FAILED", f"AUTH-FAIL (http {st})", st
    return "FAILED", f"http {st}", st


def _finnhub_quote(key):
    st, body = _get(f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={key}")
    j = _json(body)
    return (st == 200 and isinstance(j, dict) and j.get("c") not in (None, 0)), st


def chk_finnhub(key):
    ok, st = _finnhub_quote(key)
    if ok:
        return "MEASURED", "OK (quote AAPL, full key)", st
    if len(key) >= 40:                       # the pasted value looked like two 20-char keys
        ok2, st2 = _finnhub_quote(key[:20])
        if ok2:
            return "MEASURED", "OK (quote AAPL via FIRST-20-CHARS; full string was two keys)", st2
    if st == 401:
        return "FAILED", "AUTH-FAIL (401, full and split)", st
    if st == 429:
        return "FAILED", "PLAN-OR-RATE-LIMIT (429)", st
    return "FAILED", f"http {st}", st


def chk_fda(key):
    st, body = _get(f"https://api.fda.gov/drug/event.json?api_key={key}&limit=1")
    j = _json(body)
    if st == 200 and isinstance(j, dict) and j.get("results"):
        return "MEASURED", "OK (drug/event; key accepted - openFDA also serves keyless)", st
    if st in (401, 403):
        return "FAILED", "AUTH-FAIL", st
    if st == 429:
        return "FAILED", "PLAN-OR-RATE-LIMIT (429)", st
    return "FAILED", f"http {st}", st


def chk_newsdata(key):
    st, body = _get(f"https://newsdata.io/api/1/latest?apikey={key}&q=stocks&size=1")
    j = _json(body)
    if st == 200 and isinstance(j, dict) and j.get("status") == "success":
        return "MEASURED", "OK (latest?q=stocks)", st
    if isinstance(j, dict) and j.get("status") == "error":
        low = json.dumps(j.get("results") or "").lower()
        if any(w in low for w in ("unauthorized", "apikey", "invalid")):
            return "FAILED", "AUTH-FAIL", st
        if any(w in low for w in ("limit", "plan", "upgrade", "size")):
            return "FAILED", "PLAN-OR-RATE-LIMIT", st
        return "FAILED", "AMBIGUOUS", st
    if st in (401, 403):
        return "FAILED", "AUTH-FAIL", st
    return "FAILED", f"http {st}", st


def chk_tiingo(key):
    st, body = _get(f"https://api.tiingo.com/tiingo/daily/aapl?token={key}",
                    headers={"Content-Type": "application/json"})
    j = _json(body)
    if st == 200 and isinstance(j, dict) and j.get("ticker"):
        return "MEASURED", "OK (daily/aapl metadata)", st
    if st in (401, 403):
        return "FAILED", "AUTH-FAIL", st
    return "FAILED", f"http {st}", st


PROVIDERS = [
    ("gemini",        "GEMINI_API_KEY",        chk_gemini),
    ("fred",          "FRED_API_KEY",          chk_fred),
    ("data.gov",      "DATA_GOV_API_KEY",      chk_datagov),
    ("polygon",       "POLYGON_API_KEY",       chk_polygon),
    ("fmp",           "FMP_API_KEY",           chk_fmp),
    ("alpha_vantage", "ALPHA_VANTAGE_API_KEY", chk_alpha_vantage),
    ("eodhd",         "EODHD_API_KEY",         chk_eodhd),
    ("finnhub",       "FINNHUB_API_KEY",       chk_finnhub),
    ("fda",           "FDA_API_KEY",           chk_fda),
    ("newsdata",      "NEWSDATA_API_KEY",      chk_newsdata),
    ("tiingo",        "TIINGO_API_KEY",        chk_tiingo),
]


def _scrub(text, secrets):
    for v in secrets:
        if v:
            text = text.replace(v, "***")
    return text


def run():
    config.load_credentials()
    secrets = [os.getenv(env) or "" for _, env, _ in PROVIDERS]
    rows = []
    for label, env, fn in PROVIDERS:
        key = os.getenv(env)
        if not key:
            rows.append((label, "MISSING", "no key loaded in env", ""))
            continue
        try:
            verdict, note, st = fn(key)
        except urllib.error.URLError as e:
            verdict, note, st = "FAILED", f"NETWORK ({e.reason})", ""
        except Exception as e:                       # never let one provider abort the sweep
            verdict, note, st = "FAILED", f"ERROR ({type(e).__name__})", ""
        rows.append((label, verdict, _scrub(str(note), secrets), st))

    print(f"{'PROVIDER':14} {'VERDICT':9} {'HTTP':5} NOTE")
    print("-" * 72)
    for label, verdict, note, st in rows:
        print(f"{label:14} {verdict:9} {str(st):5} {note}")
    n = sum(1 for r in rows if r[1] == "MEASURED")
    print("-" * 72)
    print(f"{n}/{len(rows)} MEASURED")
    return rows


if __name__ == "__main__":
    run()
