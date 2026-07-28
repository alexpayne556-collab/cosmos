"""
Top-gainers taxonomy classifier (ADR-018 recurrence / ADR-024 precursor /
ADR-026 dilution radar / ADR-027 backfill atlas).

Two complementary lenses over the same taxonomy hypothesis:
  1. Recurrence + filing lens: `TopGainersTracker._classify_recurrence_pattern`
     (ordinal appearance count, float, SEC form types). Orchestrator-specified.
  2. Price-behavior lens: `classify_gainer(GainerFeatures)` (window return,
     drawdown, spike-day counts) — corroborated by the 2026-07-28 verify-station
     audit of Spark's 9 exemplars.

RULING (OQ-SPARK-DECAY-ARC): Spark's decay magnitudes are UNVERIFIED third-party
statistics. **They do not enter this file.** Every emitted record carries
`expected_return = None`, populated only from OUR OWN 90-day backfill atlas
(ADR-027). No hardcoded expected return exists anywhere in this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


# --------------------------------------------------------------------------- #
#  Lens 1 — recurrence + SEC-filing classifier (orchestrator-specified)       #
# --------------------------------------------------------------------------- #
class TopGainersTracker:
    """Harvests daily top gainers, tracks recurrence (ADR-018/023), and classifies
    each recurring name into the qualitative taxonomy HYPOTHESIS."""

    DILUTIVE_FORMS = ("S-3", "S-1", "ATM", "6-K")
    EARNINGS_FORMS = ("8-K", "10-Q", "10-K")

    def _classify_recurrence_pattern(
        self,
        ticker: str,
        ordinal_count: int,
        mean_interval: float,
        float_m: Optional[float],
        sec_filings: List[str],
    ) -> Tuple[str, str]:
        """
        Classifies recurrence into qualitative taxonomy hypothesis classes:
        - SERIAL CATALYST
        - SUSTAINED REGIME
        - DILUTION CYCLE
        - STRUCTURAL NOISE

        NOTE (OQ-GAINER-DILUTION-SCOPE): `sec_filings` MUST be scoped to recent /
        recurrence-window filings, not all-time — nearly every issuer has an S-3
        shelf on file, so an unscoped list would over-flag DILUTION CYCLE.
        `mean_interval` is accepted for signature stability / future interval rules.
        """
        has_s3_s1 = any(f in self.DILUTIVE_FORMS for f in sec_filings)
        has_8k_earnings = any(f in self.EARNINGS_FORMS for f in sec_filings)

        # 1. Toxic Dilution Check
        if has_s3_s1 or (ordinal_count >= 4 and float_m and float_m < 10.0 and not has_8k_earnings):
            return "DILUTION CYCLE", "HYPOTHESIS_DILUTION_RISK"

        # 2. Structural Noise (Ultra low float)
        if float_m and float_m < 5.0 and ordinal_count >= 3 and not has_8k_earnings:
            return "STRUCTURAL", "HYPOTHESIS_HIGH_BETA_NOISE"

        # 3. Serial Catalyst
        if has_8k_earnings and ordinal_count <= 3:
            return "SERIAL CATALYST", "HYPOTHESIS_SERIAL_CATALYST"

        # 4. Sustained Regime
        if ordinal_count <= 2:
            return "SUSTAINED REGIME", "HYPOTHESIS_SUSTAINED_REGIME"

        return "UNKNOWN", "MONITOR"

    def build_record(
        self,
        ticker: str,
        ordinal_count: int,
        mean_interval: float,
        float_m: Optional[float],
        sec_filings: List[str],
    ) -> dict:
        """Emit a tracker record. `expected_return` is always None until the
        atlas populates it (see `expected_return_from_atlas`)."""
        taxonomy, hypothesis = self._classify_recurrence_pattern(
            ticker, ordinal_count, mean_interval, float_m, sec_filings
        )
        return {
            "ticker": ticker,
            "ordinal_count": ordinal_count,
            "mean_interval": mean_interval,
            "float_m": float_m,
            "taxonomy": taxonomy,
            "hypothesis": hypothesis,
            "expected_return": None,  # OQ-SPARK-DECAY-ARC: Uncalibrated pending live venue backfill
        }


# --------------------------------------------------------------------------- #
#  Lens 2 — price-behavior classifier (verify-station audit lens)             #
# --------------------------------------------------------------------------- #
class GainerClass(str, Enum):
    SERIAL_CATALYST = "SERIAL_CATALYST"
    DILUTION_CYCLE = "DILUTION_CYCLE"
    SUSTAINED_REGIME = "SUSTAINED_REGIME"
    STRUCTURAL_NOISE = "STRUCTURAL_NOISE"
    UNCLASSIFIED = "UNCLASSIFIED"


@dataclass(frozen=True)
class ClassProfile:
    gainer_class: GainerClass
    expected_return: Optional[float] = None   # ALWAYS None until fit from our atlas
    sample_n: int = 0
    source: str = "unpopulated"


PROFILES = {c: ClassProfile(c) for c in GainerClass}


@dataclass(frozen=True)
class GainerFeatures:
    off_52w_high_frac: float
    window_return_pct: float
    max_drawdown_pct: float
    up_spike_days: int
    down_spike_days: int
    avg_daily_volume: float
    range_position: float
    noncompliant: bool = False


@dataclass(frozen=True)
class ClassificationResult:
    gainer_class: GainerClass
    expected_return: Optional[float]
    rationale: str
    overlap_flags: tuple = ()


def classify_gainer(f: GainerFeatures) -> ClassificationResult:
    """Primary-class assignment from measured price behavior. expected_return is
    ALWAYS None here (OQ-SPARK-DECAY-ARC)."""
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
    """The ONLY legitimate source of an expected-return number: OUR OWN realized
    samples (ADR-027 backfill / ADR-024 precursor atlas). None with no samples."""
    if not samples:
        return None
    return sum(samples) / len(samples)
