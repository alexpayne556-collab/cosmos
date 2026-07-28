"""
Top-gainers taxonomy classifier (ADR-018 recurrence / ADR-024 precursor /
ADR-027 backfill atlas).

Spark's four-class taxonomy — SERIAL_CATALYST / DILUTION_CYCLE /
SUSTAINED_REGIME / STRUCTURAL_NOISE — is a good HYPOTHESIS, corroborated by the
2026-07-28 verify-station audit (6/9 exemplars clean; STAK shows the classes
overlap). It enters as a classifier over MEASURED features.

RULING (OQ-SPARK-DECAY-ARC): Spark's decay magnitudes (+4.5 / +1.1 / -3.2 /
-11.8 %) and win rates are UNVERIFIED third-party statistics with no market-data
provenance. **They do not enter this file.** Every class carries
`expected_return = None` until populated from OUR OWN 90-day backfill atlas
(ADR-027). No hardcoded expected return exists anywhere in this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class GainerClass(str, Enum):
    SERIAL_CATALYST = "SERIAL_CATALYST"     # repeated distinct spikes (event-driven)
    DILUTION_CYCLE = "DILUTION_CYCLE"       # collapse / going-concern / noncompliant
    SUSTAINED_REGIME = "SUSTAINED_REGIME"   # durable trend toward the 52w high
    STRUCTURAL_NOISE = "STRUCTURAL_NOISE"   # thin, rangebound micro-cap chop
    UNCLASSIFIED = "UNCLASSIFIED"


@dataclass(frozen=True)
class ClassProfile:
    gainer_class: GainerClass
    expected_return: Optional[float] = None   # ALWAYS None until fit from our atlas
    sample_n: int = 0
    source: str = "unpopulated"               # -> 'atlas' once ADR-027 backfill runs


# Every profile starts with expected_return=None. This is the enforcement point
# for the ruling: no third-party decay number is baked in.
PROFILES = {c: ClassProfile(c) for c in GainerClass}


@dataclass(frozen=True)
class GainerFeatures:
    """All MEASURED (verify-station lane) — derived from bars + fundamentals."""
    off_52w_high_frac: float      # 1 - last/hi52   (0 = at high, 1 = far below)
    window_return_pct: float
    max_drawdown_pct: float       # <= 0
    up_spike_days: int            # count of >= +15% single-day closes
    down_spike_days: int          # count of <= -15% single-day closes
    avg_daily_volume: float
    range_position: float         # (last - lo52) / (hi52 - lo52), 0..1
    noncompliant: bool = False


@dataclass(frozen=True)
class ClassificationResult:
    gainer_class: GainerClass
    expected_return: Optional[float]   # None by ruling until atlas-populated
    rationale: str
    overlap_flags: tuple = ()          # other classes whose signals also fired


def classify_gainer(f: GainerFeatures) -> ClassificationResult:
    """Assign a PRIMARY class from measured features. Priority: distress first,
    then event-spikiness, then durable trend, then noise. Overlapping signals are
    recorded (the taxonomy is not a clean partition — see STAK in the audit).
    expected_return is ALWAYS None here (OQ-SPARK-DECAY-ARC)."""
    spikes = f.up_spike_days + f.down_spike_days
    overlap: List[GainerClass] = []
    if spikes >= 3:
        overlap.append(GainerClass.SERIAL_CATALYST)
    if f.off_52w_high_frac >= 0.75 or f.noncompliant:
        overlap.append(GainerClass.DILUTION_CYCLE)
    if f.window_return_pct >= 40 and f.range_position >= 0.6 and spikes <= 2:
        overlap.append(GainerClass.SUSTAINED_REGIME)
    if f.avg_daily_volume < 100_000 and abs(f.window_return_pct) < 30:
        overlap.append(GainerClass.STRUCTURAL_NOISE)

    if f.noncompliant or f.off_52w_high_frac >= 0.75:
        primary = GainerClass.DILUTION_CYCLE
        why = f"{f.off_52w_high_frac*100:.0f}% off 52w high" + (", NONCOMPLIANT" if f.noncompliant else "")
    elif spikes >= 3:
        primary = GainerClass.SERIAL_CATALYST
        why = f"{f.up_spike_days} up / {f.down_spike_days} down single-day spikes"
    elif f.window_return_pct >= 40 and f.range_position >= 0.6 and spikes <= 2:
        primary = GainerClass.SUSTAINED_REGIME
        why = f"+{f.window_return_pct:.0f}% window, {f.range_position*100:.0f}% up 52w range, few spikes"
    elif f.avg_daily_volume < 100_000 and abs(f.window_return_pct) < 30:
        primary = GainerClass.STRUCTURAL_NOISE
        why = f"thin ({f.avg_daily_volume/1000:.0f}k/d), flat window"
    else:
        primary = GainerClass.UNCLASSIFIED
        why = f"window {f.window_return_pct:+.0f}%, {spikes} spikes, {f.range_position*100:.0f}% up range"

    return ClassificationResult(
        gainer_class=primary,
        expected_return=PROFILES[primary].expected_return,   # None, by ruling
        rationale=why,
        overlap_flags=tuple(c for c in overlap if c != primary),
    )


def expected_return_from_atlas(samples: List[float]) -> Optional[float]:
    """Populate a class's expected forward return from OUR OWN realized samples
    (ADR-027 backfill / ADR-024 precursor atlas). Returns None with no samples —
    the only legitimate source of an expected-return number in this system."""
    if not samples:
        return None
    return sum(samples) / len(samples)
