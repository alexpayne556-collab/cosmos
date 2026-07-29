"""
Reconcile — the ADR-007 grader with the ADR-030 Prior-Commitment Gate.

First-touch on 15-second bars INCLUDING the extended session, and — critically —
a Brier score is earned ONLY if the t0 distribution was committed BEFORE the
outcome could be observed (`outcome_determined_at`). A distribution written after
the fact is a description, not a forecast; the gate refuses to score it.

Scoring is in the generator's direction-agnostic bucket space (RULE_TO_BUCKET).
Murphy refuses to run on degenerate input (ADR-030 R5).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, List, Optional, Sequence, Tuple

OUTCOME_CLASSES = ("up", "down", "no_move")            # market-direction labels
OUTCOME_BUCKETS = ("hit_target_first", "hit_invalidation_first", "expire_in_range")
RULE_TO_BUCKET = {
    "TARGET_FIRST": "hit_target_first",
    "INVALIDATION_FIRST": "hit_invalidation_first",
    "AMBIGUOUS_BOTH_TOUCHED": "hit_invalidation_first",   # ambiguous == loss side
    "EXPIRY_SETTLE": "expire_in_range",
}
ALPHA = 0.10
BACKFILL_GENERATOR = "backfill_historical"

# ADR-030 R4 eligibility enum
ELIGIBLE = "ELIGIBLE"
ELIGIBLE_LATE_PRIOR = "ELIGIBLE_LATE_PRIOR"
EXCLUDED_POST_HOC = "EXCLUDED_POST_HOC"
EXCLUDED_NO_DISTRIBUTION = "EXCLUDED_NO_DISTRIBUTION"
EXCLUDED_BACKFILL = "EXCLUDED_BACKFILL"
EXCLUDED_NO_ENTRY = "EXCLUDED_NO_ENTRY"
SCORED = (ELIGIBLE, ELIGIBLE_LATE_PRIOR)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_ts(s):
    if not s:
        return None
    s2 = s.strip().replace("Z", "+00:00").replace(" ", "T")
    try:
        d = datetime.fromisoformat(s2)
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


@dataclass
class Resolution:
    resolved: bool
    outcome_class: Optional[str]
    first_touch_rule: str
    settle_price: Optional[float]
    brier: Optional[float]
    brier_excluded: bool
    brier_eligibility: str = ELIGIBLE
    outcome_determined_at: Optional[str] = None
    prior_lag_hours: Optional[float] = None


def first_touch(direction: str, bars: Sequence[dict], target: float, invalidation: float):
    """Scan 15s bars in order. Returns (outcome_class, rule, outcome_determined_at).
    outcome_determined_at is the begins_at of the breaching bar (ADR-030 R1)."""
    for b in bars:
        hi = float(b["high_price"]); lo = float(b["low_price"]); at = b.get("begins_at")
        if direction == "up":
            hit, inval = hi >= target, lo <= invalidation
        else:
            hit, inval = lo <= target, hi >= invalidation
        if hit and inval:
            return ("down" if direction == "up" else "up", "AMBIGUOUS_BOTH_TOUCHED", at)
        if hit:
            return ("up" if direction == "up" else "down", "TARGET_FIRST", at)
        if inval:
            return ("down" if direction == "up" else "up", "INVALIDATION_FIRST", at)
    return (None, "PENDING", None)


def multiclass_brier(distribution: dict, outcome: str, classes=OUTCOME_BUCKETS) -> float:
    """One-hot multi-class Brier over `classes`: sum_c (p_c - y_c)^2. 0.0 best, 2.0 worst."""
    return sum((distribution.get(c, 0.0) - (1.0 if c == outcome else 0.0)) ** 2 for c in classes)


def brier_eligibility(*, generator_id, entry_triggered, t0_distribution,
                      distribution_logged_at, prediction_logged_at, outcome_determined_at) -> str:
    """ADR-030 R4. The clock that matters is the market's (outcome_determined_at),
    not the grader's."""
    if generator_id == BACKFILL_GENERATOR:
        return EXCLUDED_BACKFILL
    if not entry_triggered:
        return EXCLUDED_NO_ENTRY
    if t0_distribution is None:
        return EXCLUDED_NO_DISTRIBUTION
    d, o, p = _parse_ts(distribution_logged_at), _parse_ts(outcome_determined_at), _parse_ts(prediction_logged_at)
    if d is not None and o is not None and d >= o:
        return EXCLUDED_POST_HOC
    if d is not None and p is not None and d > p:
        return ELIGIBLE_LATE_PRIOR
    return ELIGIBLE


def _hours_between(a, b):
    da, db = _parse_ts(a), _parse_ts(b)
    if da is None or db is None:
        return None
    return round((db - da).total_seconds() / 3600.0, 4)


def _finalize(gen, dist, outcome, rule, settle, determined_at, dist_at, pred_at) -> Resolution:
    elig = brier_eligibility(generator_id=gen, entry_triggered=True, t0_distribution=dist,
                             distribution_logged_at=dist_at, prediction_logged_at=pred_at,
                             outcome_determined_at=determined_at)
    excluded = elig.startswith("EXCLUDED")
    brier = None
    bucket = RULE_TO_BUCKET.get(rule)
    if elig in SCORED and dist is not None and bucket is not None:
        brier = multiclass_brier(dist, bucket)
    lag = _hours_between(pred_at, dist_at) if elig == ELIGIBLE_LATE_PRIOR else None
    return Resolution(True, outcome, rule, settle, brier, excluded, elig, determined_at, lag)


def grade(prediction: dict, bars: Sequence[dict], *, now_ts: Optional[str] = None,
          entry_triggered: bool = True, t0_distribution=None,
          distribution_logged_at: Optional[str] = None,
          prediction_logged_at: Optional[str] = None) -> Resolution:
    """Grade one prediction. Brier is scored off the t0 distribution only, and only
    if it passes the Prior-Commitment Gate."""
    gen = prediction.get("generator_id")
    direction = prediction["direction"]
    dist = t0_distribution if t0_distribution is not None else prediction.get("distribution")
    target = prediction.get("target_price")
    inval = prediction.get("invalidation_price")

    if not entry_triggered:
        return Resolution(True, None, "EXPIRED_NO_ENTRY", None, None, True, EXCLUDED_NO_ENTRY,
                          prediction.get("expiry_timestamp"), None)

    if direction == "no_move" or target is None or inval is None:
        return Resolution(False, None, "PENDING", None, None, False, ELIGIBLE, None, None)

    outcome, rule, determined_at = first_touch(direction, bars, float(target), float(inval))

    if outcome is None:
        expiry = prediction.get("expiry_timestamp")
        now = now_ts or _now_iso()
        pe, pn = _parse_ts(expiry), _parse_ts(now)
        if pe is not None and pn is not None and pe <= pn and bars:
            settle = float(bars[-1]["close_price"])
            return _finalize(gen, dist, "no_move", "EXPIRY_SETTLE", settle, expiry,
                             distribution_logged_at, prediction_logged_at)
        return Resolution(False, None, "PENDING", None, None, False, ELIGIBLE, None, None)

    settle = float(bars[-1]["close_price"]) if bars else None
    return _finalize(gen, dist, outcome, rule, settle, determined_at,
                     distribution_logged_at, prediction_logged_at)


def murphy_decomposition(pairs: Sequence[tuple]):
    """ADR-030 R5: returns (decomposition_dict, reason) or (None, reason) when the
    input is degenerate. Requires n >= 20 AND >= 3 distinct forecast values."""
    n = len(pairs)
    distinct = len({p for p, _ in pairs})
    if n < 20 or distinct < 3:
        return None, f"insufficient: n={n} (need >=20), distinct_forecasts={distinct} (need >=3)"
    ybar = sum(y for _, y in pairs) / n
    uncertainty = ybar * (1.0 - ybar)
    groups = defaultdict(list)
    for p, y in pairs:
        groups[p].append(y)
    reliability = resolution = 0.0
    for p, ys in groups.items():
        nk = len(ys); ybar_k = sum(ys) / nk
        reliability += nk / n * (p - ybar_k) ** 2
        resolution += nk / n * (ybar_k - ybar) ** 2
    return ({"reliability": reliability, "resolution": resolution, "uncertainty": uncertainty,
             "brier": reliability - resolution + uncertainty}, "ok")


def _update_weight(con, key, brier, prediction_id):
    correctness = 1.0 - brier / 2.0
    row = con.execute("SELECT weight, n_resolved, sum_brier FROM weights WHERE key=?", (key,)).fetchone()
    old_w, n, sb = row if row else (0.5, 0, 0.0)
    new_w = old_w + ALPHA * (correctness - old_w)
    ts = _now_iso()
    con.execute(
        "INSERT INTO weights (key, weight, n_resolved, sum_brier, last_updated) VALUES (?,?,?,?,?) "
        "ON CONFLICT(key) DO UPDATE SET weight=excluded.weight, n_resolved=excluded.n_resolved, "
        "sum_brier=excluded.sum_brier, last_updated=excluded.last_updated",
        (key, round(new_w, 4), n + 1, sb + brier, ts))
    con.execute(
        "INSERT INTO weight_change_log (ts, key, old_weight, new_weight, prediction_id, reason) "
        "VALUES (?,?,?,?,?,?)",
        (ts, key, round(old_w, 4), round(new_w, 4), prediction_id,
         f"brier={brier:.3f} correctness={correctness:.3f}"))
    con.commit()
    return old_w, new_w


def reconcile(con, bar_provider: Callable[[dict], List[dict]], *, now_ts: Optional[str] = None):
    """Grade every matured open prediction, scoring t0 distributions through the gate."""
    from . import ledger as ledgermod
    resolved, weight_changes = [], []
    for pred in ledgermod.open_predictions(con):
        bars = bar_provider(pred) or []
        t0_dist, t0_at = ledgermod.t0_distribution(con, pred["prediction_id"])
        res = grade(pred, bars, now_ts=now_ts, t0_distribution=t0_dist,
                    distribution_logged_at=t0_at, prediction_logged_at=pred.get("ts_logged"))
        if not res.resolved:
            continue
        con.execute(
            "UPDATE predictions SET resolved=1, ts_resolved=?, outcome_class=?, first_touch_rule=?, "
            "settle_price=?, brier=?, brier_excluded=?, brier_eligibility=?, outcome_determined_at=?, "
            "prior_lag_hours=? WHERE prediction_id=?",
            (_now_iso(), res.outcome_class, res.first_touch_rule, res.settle_price, res.brier,
             int(res.brier_excluded), res.brier_eligibility, res.outcome_determined_at,
             res.prior_lag_hours, pred["prediction_id"]))
        con.commit()
        resolved.append((pred["prediction_id"], res.outcome_class, res.first_touch_rule,
                         res.brier_eligibility, res.brier))
        if res.brier is not None and res.brier_eligibility in SCORED:
            old_w, new_w = _update_weight(con, pred["generator_id"], res.brier, pred["prediction_id"])
            weight_changes.append((pred["generator_id"], old_w, new_w))
    return {"resolved": resolved, "weight_changes": weight_changes}


def brier_aggregates(con) -> dict:
    """Both aggregates, always together (ADR-030 R4): headline = ELIGIBLE only;
    inclusive = ELIGIBLE + ELIGIBLE_LATE_PRIOR."""
    rows = con.execute(
        "SELECT brier, brier_eligibility FROM predictions "
        "WHERE resolved=1 AND brier IS NOT NULL").fetchall()
    headline = [b for b, e in rows if e == ELIGIBLE]
    inclusive = [b for b, e in rows if e in SCORED]

    def agg(xs):
        return {"n": len(xs), "mean_brier": round(sum(xs) / len(xs), 4) if xs else None}

    return {"headline_eligible_only": agg(headline), "inclusive_with_late_prior": agg(inclusive)}
