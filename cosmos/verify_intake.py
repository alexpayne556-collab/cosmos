"""
Verify-intake — the write-authority gate (ADR-002, originator: claude,
provoked-by: gemini's round-3 failure).

Enforces the Section 1 matrix on every inbound prediction:
  1. Structural gate: required generator fields present; direction / price_mode
     valid; distribution sums to 1.0 +/- 0.001.
  2. Duplicate prediction_id rejection (design-inherited from Hermes ledger.py,
     implemented new here — the ancestor had no such mechanism; see the ledger
     migration ADR).
  3. Field-ownership enforcement: any field a station may not write is STRIPPED,
     forensically logged, quarantined with the correct reason, and charged
     (pct-normalized) to the generator's claim-accuracy metric.

Anchoring (ADR-001): `anchor_relative` converts RELATIVE_PCT offsets against the
last official close preceding release into absolute target/invalidation prices.
This is the VERIFY station's lane — generators never write absolutes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from . import alerts
from .quarantine import QuarantineReason, quarantine


class Station(str, Enum):
    GENERATOR = "GENERATOR"
    VERIFY = "VERIFY"
    ORACLE = "ORACLE"
    RECONCILE = "RECONCILE"


# Field -> owning station (Section 1 write-authority matrix).
FIELD_OWNER: Dict[str, Station] = {
    # generator lane
    "ticker": Station.GENERATOR,
    "direction": Station.GENERATOR,
    "offset_target_pct": Station.GENERATOR,
    "offset_invalidation_pct": Station.GENERATOR,
    "distribution": Station.GENERATOR,
    "thesis": Station.GENERATOR,
    "canon_tags": Station.GENERATOR,
    "source_urls": Station.GENERATOR,
    "strategy_family": Station.GENERATOR,
    "price_mode": Station.GENERATOR,
    "horizon_days": Station.GENERATOR,
    "generator_id": Station.GENERATOR,
    "prediction_id": Station.GENERATOR,
    # verify-station lane
    "verified_price": Station.VERIFY,
    "target_price": Station.VERIFY,
    "invalidation_price": Station.VERIFY,
    "anchor_close": Station.VERIFY,
    "liquidity_snapshot": Station.VERIFY,
    "float": Station.VERIFY,
    "market_cap": Station.VERIFY,
    "short_interest": Station.VERIFY,
    "shares_outstanding": Station.VERIFY,
    "fundamentals": Station.VERIFY,
    "eps_actual": Station.VERIFY,
    "eps_estimate": Station.VERIFY,
    "run_date": Station.VERIFY,
    "run_magnitude_pct": Station.VERIFY,
    "run_history": Station.VERIFY,
    "distribution_logged_at": Station.VERIFY,   # ADR-030 R3: intake stamps it; generators never do
    # oracle lane
    "regime": Station.ORACLE,
    "asset_class": Station.ORACLE,
    "credit_strain": Station.ORACLE,
    # reconcile lane
    "status": Station.RECONCILE,
    "brier": Station.RECONCILE,
    "murphy": Station.RECONCILE,
    "move_start": Station.RECONCILE,
    "lag": Station.RECONCILE,
}

_PRICE_FIELDS = {"verified_price", "target_price", "invalidation_price",
                 "anchor_close", "liquidity_snapshot"}
_FUNDAMENTAL_FIELDS = {"float", "market_cap", "short_interest", "shares_outstanding",
                       "fundamentals", "eps_actual", "eps_estimate"}
_HISTORY_FIELDS = {"run_date", "run_magnitude_pct", "run_history"}

REQUIRED_GENERATOR_FIELDS = (
    "ticker", "direction", "offset_target_pct", "offset_invalidation_pct",
    "distribution", "thesis", "canon_tags", "source_urls", "price_mode",
)
VALID_DIRECTIONS = ("up", "down", "no_move")
VALID_PRICE_MODES = ("ABSOLUTE", "RELATIVE_PCT")
DISTRIBUTION_TOLERANCE = 0.001


def _reason_for(fieldname: str) -> QuarantineReason:
    if fieldname == "distribution_logged_at":
        return QuarantineReason.SELF_STAMPED       # ADR-030 R3: a self-reported commit time is backdateable
    if fieldname in _FUNDAMENTAL_FIELDS:
        return QuarantineReason.FUNDAMENTAL_OVERWRITE
    if fieldname in _HISTORY_FIELDS:
        return QuarantineReason.CONFABULATED_HISTORY
    # prices + any other unauthorized generator write
    return QuarantineReason.SELF_VERIFIED


@dataclass
class IntakeResult:
    accepted: bool
    record: dict
    violations: List[dict] = field(default_factory=list)   # {field, value, reason}
    errors: List[str] = field(default_factory=list)
    quarantine_paths: List[str] = field(default_factory=list)
    claim_accuracy_charge: float = 0.0                     # pct-normalized gap


def _structural_errors(payload: dict) -> List[str]:
    errs: List[str] = []
    for f in REQUIRED_GENERATOR_FIELDS:
        if f not in payload:
            errs.append(f"missing required generator field '{f}'")
    if "direction" in payload and payload["direction"] not in VALID_DIRECTIONS:
        errs.append(f"direction {payload['direction']!r} not in {VALID_DIRECTIONS}")
    if "price_mode" in payload and payload["price_mode"] not in VALID_PRICE_MODES:
        errs.append(f"price_mode {payload['price_mode']!r} not in {VALID_PRICE_MODES}")
    dist = payload.get("distribution")
    if isinstance(dist, dict) and dist:
        total = sum(dist.values())
        if abs(total - 1.0) > DISTRIBUTION_TOLERANCE:
            errs.append(f"distribution sums to {total:.4f}; must be 1.0 +/- {DISTRIBUTION_TOLERANCE}")
    elif "distribution" in payload:
        errs.append("distribution must be a non-empty mapping")
    return errs


def intake(payload: dict, *,
           actor: Station = Station.GENERATOR,
           seen_ids: Optional[Set[str]] = None) -> IntakeResult:
    """Run a prediction payload through the write-authority gate."""
    seen_ids = seen_ids if seen_ids is not None else set()
    violations: List[dict] = []
    quarantine_paths: List[str] = []

    errors = _structural_errors(payload)

    pid = payload.get("prediction_id")
    if pid is not None and pid in seen_ids:
        err = f"duplicate prediction_id {pid!r}"
        qp = quarantine(payload, reason=QuarantineReason.MALFORMED_ROW,
                        errors=[err], source="verify_intake.duplicate")
        errors.append(err)
        return IntakeResult(False, {}, violations, errors, [str(qp)], 0.0)

    clean: dict = {}
    trespass = 0
    owned = 0
    for key, value in payload.items():
        owner = FIELD_OWNER.get(key)
        if owner is not None:
            owned += 1
        if owner is None or owner == actor:
            clean[key] = value
            continue
        # trespass: actor wrote a field it does not own -> strip + forensics
        reason = _reason_for(key)
        violations.append({"field": key, "value": value, "reason": reason.value})
        qp = quarantine(
            {"field": key, "value": value, "prediction_id": pid},
            reason=reason,
            errors=[f"{actor.value} may not write '{key}' (owned by {owner.value})"],
            source="verify_intake.write_authority",
        )
        quarantine_paths.append(str(qp))
        trespass += 1

    if violations:
        alerts.emit_alert(
            "WRITE_AUTHORITY_VIOLATION",
            f"{actor.value} trespassed {len(violations)} field(s)",
            severity="WARN",
            fields=[v["field"] for v in violations],
        )

    charge = round(trespass / owned, 4) if owned else 0.0

    if pid is not None:
        seen_ids.add(pid)

    return IntakeResult(
        accepted=not errors,
        record=clean,
        violations=violations,
        errors=errors,
        quarantine_paths=quarantine_paths,
        claim_accuracy_charge=charge,
    )


def anchor_relative(anchor_close: float,
                    offset_target_pct: float,
                    offset_invalidation_pct: float,
                    *, ndigits: int = 4) -> Tuple[float, float]:
    """ADR-001: RELATIVE_PCT anchors strictly to the last official close
    preceding release_timestamp_utc. Returns absolute (target, invalidation).
    VERIFY-station lane only."""
    if anchor_close <= 0:
        raise ValueError("anchor_close must be positive")
    target = round(anchor_close * (1.0 + offset_target_pct / 100.0), ndigits)
    invalidation = round(anchor_close * (1.0 + offset_invalidation_pct / 100.0), ndigits)
    return target, invalidation
