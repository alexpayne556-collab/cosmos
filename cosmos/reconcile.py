"""
Reconcile — the ADR-007 grader (descendant of Hermes reconcile.py).

First-touch on 15-second bars INCLUDING the extended session (04:00-20:00 ET).
Rules (ratified point-3 spec):
  * TARGET_FIRST / INVALIDATION_FIRST by first touch.
  * A bar breaching BOTH -> AMBIGUOUS_BOTH_TOUCHED = loss (never the optimistic side).
  * Neither touched by expiry -> EXPIRY_SETTLE at the last official close preceding
    expiry_timestamp -> no_move.
  * EXPIRED_NO_ENTRY (a trigger that never fired) -> excluded from Brier, tracked
    as trigger-conversion rate.
  * backfill rows (generator_id == 'backfill_historical') -> excluded from Brier;
    atlas + lag distributions only.
Scoring: multi-class Brier over a one-hot outcome vector (perfect 0.0, worst 2.0)
+ Murphy decomposition (reliability - resolution + uncertainty).

The bar fetch is injected (`bar_provider`) — the Robinhood MCP is an agent tool,
not a library, so the desk/agent supplies bars; tests supply synthetic bars. The
grader itself is pure and deterministic.
"""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

OUTCOME_CLASSES = ("up", "down", "no_move")            # market-direction labels (readability)
# Brier is scored in the generator's direction-agnostic bucket space
# (matches the ratified GENESIS distribution schema, OQ-GENESIS-DISTRIBUTIONS):
OUTCOME_BUCKETS = ("hit_target_first", "hit_invalidation_first", "expire_in_range")
RULE_TO_BUCKET = {
    "TARGET_FIRST": "hit_target_first",
    "INVALIDATION_FIRST": "hit_invalidation_first",
    "AMBIGUOUS_BOTH_TOUCHED": "hit_invalidation_first",  # ambiguous == loss side
    "EXPIRY_SETTLE": "expire_in_range",
}
ALPHA = 0.10  # EWMA weight learning rate (inherited from Hermes)
BACKFILL_GENERATOR = "backfill_historical"


@dataclass
class Resolution:
    resolved: bool
    outcome_class: Optional[str]
    first_touch_rule: str          # TARGET_FIRST|INVALIDATION_FIRST|AMBIGUOUS_BOTH_TOUCHED|EXPIRY_SETTLE|EXPIRED_NO_ENTRY|PENDING
    settle_price: Optional[float]
    brier: Optional[float]
    brier_excluded: bool


def first_touch(direction: str, bars: Sequence[dict], target: float, invalidation: float):
    """Scan 15s bars in order. Returns (outcome_class, rule). outcome_class is the
    realized MARKET direction (up/down); rule records how it resolved."""
    for b in bars:
        hi = float(b["high_price"]); lo = float(b["low_price"])
        if direction == "up":
            hit, inval = hi >= target, lo <= invalidation
        else:  # short
            hit, inval = lo <= target, hi >= invalidation
        if hit and inval:
            # both in one bar -> ambiguous -> the adverse (invalidation) side, = loss
            return ("down" if direction == "up" else "up", "AMBIGUOUS_BOTH_TOUCHED")
        if hit:
            return ("up" if direction == "up" else "down", "TARGET_FIRST")
        if inval:
            return ("down" if direction == "up" else "up", "INVALIDATION_FIRST")
    return (None, "PENDING")


def multiclass_brier(distribution: dict, outcome: str, classes=OUTCOME_BUCKETS) -> float:
    """One-hot multi-class Brier over `classes`: sum_c (p_c - y_c)^2. Perfect 0.0,
    worst 2.0. `outcome` is the realized class (an OUTCOME_BUCKETS member)."""
    return sum((distribution.get(c, 0.0) - (1.0 if c == outcome else 0.0)) ** 2
               for c in classes)


def murphy_decomposition(pairs: Sequence[tuple]) -> dict:
    """Murphy (1973) decomposition of the binary Brier over (p, y) pairs, y in {0,1}.
    Brier == reliability - resolution + uncertainty (identity holds exactly)."""
    n = len(pairs)
    if n == 0:
        return {"reliability": 0.0, "resolution": 0.0, "uncertainty": 0.0, "brier": 0.0}
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
    return {"reliability": reliability, "resolution": resolution,
            "uncertainty": uncertainty, "brier": reliability - resolution + uncertainty}


def grade(prediction: dict, bars: Sequence[dict], *, now_ts: Optional[str] = None,
          entry_triggered: bool = True) -> Resolution:
    """Grade one prediction against its bar series."""
    gen = prediction.get("generator_id")
    direction = prediction["direction"]
    dist = prediction.get("distribution")
    target = prediction.get("target_price")
    inval = prediction.get("invalidation_price")

    # EXPIRED_NO_ENTRY: a triggered setup whose entry never fired -> excluded from Brier
    if not entry_triggered:
        return Resolution(True, None, "EXPIRED_NO_ENTRY", None, None, True)

    # no_move / band rows and rows lacking thresholds: nothing to first-touch here
    if direction == "no_move" or target is None or inval is None:
        return Resolution(False, None, "PENDING", None, None, False)

    outcome, rule = first_touch(direction, bars, float(target), float(inval))

    if outcome is None:
        expiry = prediction.get("expiry_timestamp")
        now = now_ts or time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if expiry and expiry <= now and bars:
            settle = float(bars[-1]["close_price"])
            outcome, rule = "no_move", "EXPIRY_SETTLE"
            return _score(gen, dist, outcome, rule, settle)
        return Resolution(False, None, "PENDING", None, None, False)  # not matured

    settle = float(bars[-1]["close_price"]) if bars else None
    return _score(gen, dist, outcome, rule, settle)


def _score(gen, dist, outcome, rule, settle) -> Resolution:
    excluded = (gen == BACKFILL_GENERATOR)          # backfill: atlas + lag only, never Brier
    brier = None
    bucket = RULE_TO_BUCKET.get(rule)
    if not excluded and dist is not None and bucket is not None:
        brier = multiclass_brier(dist, bucket)      # scored in bucket space
    return Resolution(True, outcome, rule, settle, brier, excluded)


def _update_weight(con, key, brier, prediction_id, reason_suffix=""):
    """EWMA a generator's weight toward correctness = 1 - brier/2 (brier in [0,2])."""
    correctness = 1.0 - brier / 2.0
    row = con.execute("SELECT weight, n_resolved, sum_brier FROM weights WHERE key=?", (key,)).fetchone()
    old_w, n, sb = row if row else (0.5, 0, 0.0)
    new_w = old_w + ALPHA * (correctness - old_w)
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    con.execute(
        "INSERT INTO weights (key, weight, n_resolved, sum_brier, last_updated) VALUES (?,?,?,?,?) "
        "ON CONFLICT(key) DO UPDATE SET weight=excluded.weight, n_resolved=excluded.n_resolved, "
        "sum_brier=excluded.sum_brier, last_updated=excluded.last_updated",
        (key, round(new_w, 4), n + 1, sb + brier, ts))
    con.execute(
        "INSERT INTO weight_change_log (ts, key, old_weight, new_weight, prediction_id, reason) "
        "VALUES (?,?,?,?,?,?)",
        (ts, key, round(old_w, 4), round(new_w, 4), prediction_id,
         f"brier={brier:.3f} correctness={correctness:.3f}{reason_suffix}"))
    con.commit()
    return old_w, new_w


def reconcile(con, bar_provider: Callable[[dict], List[dict]], *, now_ts: Optional[str] = None):
    """Grade every matured open prediction. `bar_provider(prediction)` returns its
    15s bar series (agent supplies real MCP bars; tests supply synthetic). Returns
    a summary dict."""
    from . import ledger as ledgermod
    resolved, weight_changes = [], []
    for pred in ledgermod.open_predictions(con):
        bars = bar_provider(pred) or []
        res = grade(pred, bars, now_ts=now_ts)
        if not res.resolved:
            continue
        con.execute(
            "UPDATE predictions SET resolved=1, ts_resolved=?, outcome_class=?, first_touch_rule=?, "
            "settle_price=?, brier=?, brier_excluded=? WHERE prediction_id=?",
            (time.strftime("%Y-%m-%d %H:%M:%S"), res.outcome_class, res.first_touch_rule,
             res.settle_price, res.brier, int(res.brier_excluded), pred["prediction_id"]))
        con.commit()
        resolved.append((pred["prediction_id"], res.outcome_class, res.first_touch_rule, res.brier))
        if res.brier is not None and not res.brier_excluded:
            old_w, new_w = _update_weight(con, pred["generator_id"], res.brier, pred["prediction_id"])
            weight_changes.append((pred["generator_id"], old_w, new_w))
    return {"resolved": resolved, "weight_changes": weight_changes}
