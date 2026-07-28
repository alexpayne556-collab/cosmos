"""
Oracle — regime classifier (ADR-004, originator: gemini_spark).

A deterministic 4x2 matrix:
    rows (4) = high-yield credit-strain band from FRED BAMLH0A0HYM2 (HY OAS)
    cols (2) = curve state from FRED T10Y2Y (10y-2y spread) sign

Write-authority (Section 1): the oracle writes ONLY regime / asset_class /
credit_strain. It never touches prices, fundamentals, or grades.

Data sourcing:
    - Primary: FRED (BAMLH0A0HYM2, T10Y2Y). FRED access is CLAIMED (Section 3
      does not list it MEASURED) -> requires FRED_API_KEY; absent that we fall
      back to the HYG proxy, which rides the MEASURED Robinhood daily historicals.
    - The classification logic is pure and fully unit-tested offline.

Thresholds below are GUESSED and load nothing until fit -> OQ-ORACLE-1.
"""
from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, Optional, Tuple


class CreditBand(str, Enum):
    LOW = "LOW"          # spreads compressed
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    ACUTE = "ACUTE"      # crisis-wide


class Curve(str, Enum):
    POSITIVE = "POSITIVE"   # 10y-2y >= 0 (normal)
    INVERTED = "INVERTED"   # 10y-2y < 0


class AssetClass(str, Enum):
    RISK_ON = "RISK_ON"
    NEUTRAL = "NEUTRAL"
    RISK_OFF = "RISK_OFF"
    DEFENSIVE = "DEFENSIVE"


# HY OAS band edges in PERCENT (guessed -> OQ-ORACLE-1)
_OAS_EDGES: Tuple[Tuple[float, CreditBand], ...] = (
    (3.0, CreditBand.LOW),
    (4.5, CreditBand.NORMAL),
    (7.0, CreditBand.ELEVATED),
)

# 4x2 regime matrix: (band, curve) -> (regime_label, asset_class)
REGIME_MATRIX: Dict[Tuple[CreditBand, Curve], Tuple[str, AssetClass]] = {
    (CreditBand.LOW,      Curve.POSITIVE): ("EXPANSION_RISK_SEEKING", AssetClass.RISK_ON),
    (CreditBand.LOW,      Curve.INVERTED): ("LATE_CYCLE_MELTUP",      AssetClass.RISK_ON),
    (CreditBand.NORMAL,   Curve.POSITIVE): ("STABLE_NEUTRAL",         AssetClass.NEUTRAL),
    (CreditBand.NORMAL,   Curve.INVERTED): ("SLOWDOWN_WATCH",         AssetClass.NEUTRAL),
    (CreditBand.ELEVATED, Curve.POSITIVE): ("REPRICING_CAUTION",      AssetClass.RISK_OFF),
    (CreditBand.ELEVATED, Curve.INVERTED): ("CONTRACTION_RISK_OFF",   AssetClass.RISK_OFF),
    (CreditBand.ACUTE,    Curve.POSITIVE): ("STRESS_UNWIND",          AssetClass.DEFENSIVE),
    (CreditBand.ACUTE,    Curve.INVERTED): ("CREDIT_CRISIS",          AssetClass.DEFENSIVE),
}


def credit_band(oas_pct: float) -> CreditBand:
    for edge, band in _OAS_EDGES:
        if oas_pct < edge:
            return band
    return CreditBand.ACUTE


def curve_state(t10y2y_pct: float) -> Curve:
    return Curve.POSITIVE if t10y2y_pct >= 0.0 else Curve.INVERTED


@dataclass(frozen=True)
class OracleStamp:
    regime: str
    asset_class: str
    credit_strain: str
    source: str
    inputs: dict

    def to_row(self) -> dict:
        """Only the three write-authority fields land in the ledger row."""
        return {
            "regime": self.regime,
            "asset_class": self.asset_class,
            "credit_strain": self.credit_strain,
        }


def classify(oas_pct: float, t10y2y_pct: float, *, source: str = "FRED") -> OracleStamp:
    band = credit_band(oas_pct)
    curve = curve_state(t10y2y_pct)
    regime, asset_class = REGIME_MATRIX[(band, curve)]
    return OracleStamp(
        regime=regime,
        asset_class=asset_class.value,
        credit_strain=band.value,
        source=source,
        inputs={"oas_pct": oas_pct, "t10y2y_pct": t10y2y_pct},
    )


# ---------------------------------------------------------------- HYG proxy --
def hyg_proxy_oas(hyg_last: float, hyg_ma200: float, *,
                  base_oas: float = 3.5, sensitivity: float = 8.0) -> float:
    """Estimate HY OAS from HYG behaviour when FRED is unavailable. HYG trading
    below its 200d MA implies widening spreads; the drawdown fraction scales the
    OAS proxy. (Calibration guessed -> OQ-ORACLE-2.)"""
    if hyg_ma200 <= 0:
        raise ValueError("hyg_ma200 must be positive")
    drawdown = max(0.0, (hyg_ma200 - hyg_last) / hyg_ma200)
    return base_oas + sensitivity * drawdown


def classify_from_hyg(hyg_last: float, hyg_ma200: float, t10y2y_pct: float) -> OracleStamp:
    return classify(hyg_proxy_oas(hyg_last, hyg_ma200), t10y2y_pct, source="HYG_PROXY")


# ------------------------------------------------------------------- FRED ----
FRED_SERIES = {"oas": "BAMLH0A0HYM2", "curve": "T10Y2Y"}


def fetch_fred_latest(series_id: str, *,
                      api_key: Optional[str] = None,
                      opener: Callable = urllib.request.urlopen) -> float:
    """Fetch the latest observation for a FRED series. Raises RuntimeError if no
    API key (caller falls back to the HYG proxy). `opener` is injectable for tests."""
    api_key = api_key or os.environ.get("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("FRED_API_KEY not set; oracle must use the HYG proxy fallback")
    url = (
        "https://api.stlouisfed.org/fred/series/observations"
        f"?series_id={series_id}&api_key={api_key}"
        "&file_type=json&sort_order=desc&limit=1"
    )
    with opener(url, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return float(payload["observations"][0]["value"])
