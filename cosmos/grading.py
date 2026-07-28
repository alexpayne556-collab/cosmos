"""
Structural gate for outcome grading (ADR: structural gate + AMBIGUOUS_BOTH_TOUCHED).

This module holds the single-bar structural rule that is deterministic today.
The full first-touch grader over a 15-second bar SERIES (extended session,
multi-class Brier, Murphy decomposition) is the ADR-007 reconcile upgrade =
Phase 3 (pending the orchestrator's truncated spec point 3).

Rule: if a single bar breaches BOTH the target and the invalidation, the
outcome is ambiguous and is graded a LOSS — the system never awards itself the
optimistic side of an ambiguous bar. (Fixture 14 regression guard.)
"""
from __future__ import annotations

from enum import Enum


class Grade(str, Enum):
    HIT = "HIT"
    MISS = "MISS"
    LOSS = "LOSS"
    AMBIGUOUS_BOTH_TOUCHED = "AMBIGUOUS_BOTH_TOUCHED"   # == loss
    PENDING = "PENDING"


def structural_gate(direction: str,
                    bar_high: float,
                    bar_low: float,
                    target_price: float,
                    invalidation_price: float) -> Grade:
    """Grade a single bar against a target and an invalidation."""
    if direction == "up":
        hit = bar_high >= target_price
        invalidated = bar_low <= invalidation_price
    elif direction == "down":
        hit = bar_low <= target_price
        invalidated = bar_high >= invalidation_price
    else:
        return Grade.PENDING

    if hit and invalidated:
        return Grade.AMBIGUOUS_BOTH_TOUCHED
    if hit:
        return Grade.HIT
    if invalidated:
        return Grade.LOSS
    return Grade.PENDING


def is_loss(grade: Grade) -> bool:
    """AMBIGUOUS_BOTH_TOUCHED counts as a loss."""
    return grade in (Grade.LOSS, Grade.AMBIGUOUS_BOTH_TOUCHED)
