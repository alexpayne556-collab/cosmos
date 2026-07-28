from __future__ import annotations

import pytest

from cosmos import oracle
from cosmos import schema_validation as sv


@pytest.mark.parametrize("oas,expected", [
    (2.5, oracle.CreditBand.LOW),
    (3.0, oracle.CreditBand.NORMAL),
    (4.49, oracle.CreditBand.NORMAL),
    (4.5, oracle.CreditBand.ELEVATED),
    (6.99, oracle.CreditBand.ELEVATED),
    (7.0, oracle.CreditBand.ACUTE),
    (12.0, oracle.CreditBand.ACUTE),
])
def test_credit_bands(oas, expected):
    assert oracle.credit_band(oas) == expected


def test_curve_state():
    assert oracle.curve_state(0.0) == oracle.Curve.POSITIVE
    assert oracle.curve_state(-0.01) == oracle.Curve.INVERTED


def test_classify_expansion():
    s = oracle.classify(2.0, 1.2)
    assert (s.regime, s.asset_class, s.credit_strain) == ("EXPANSION_RISK_SEEKING", "RISK_ON", "LOW")


def test_classify_credit_crisis():
    s = oracle.classify(8.0, -0.5)
    assert (s.regime, s.asset_class, s.credit_strain) == ("CREDIT_CRISIS", "DEFENSIVE", "ACUTE")


def test_stamp_to_row_only_three_fields_and_schema_valid():
    row = oracle.classify(5.0, 0.4).to_row()
    assert set(row) == {"regime", "asset_class", "credit_strain"}
    assert sv.is_valid(row, "oracle_output.schema.json")


def test_hyg_proxy_widens_when_below_ma():
    tight = oracle.hyg_proxy_oas(hyg_last=80.0, hyg_ma200=80.0)   # at MA
    stressed = oracle.hyg_proxy_oas(hyg_last=68.0, hyg_ma200=80.0)  # 15% below
    assert stressed > tight
    s = oracle.classify_from_hyg(68.0, 80.0, -0.2)
    assert s.source == "HYG_PROXY"


class _FakeResp:
    def __init__(self, data): self._data = data
    def read(self): return self._data
    def __enter__(self): return self
    def __exit__(self, *a): return False


def test_fetch_fred_with_injected_opener():
    def opener(url, timeout=20):
        assert "BAMLH0A0HYM2" in url
        return _FakeResp(b'{"observations":[{"value":"4.25"}]}')
    val = oracle.fetch_fred_latest("BAMLH0A0HYM2", api_key="TESTKEY", opener=opener)
    assert val == pytest.approx(4.25)


def test_fetch_fred_without_key_raises(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        oracle.fetch_fred_latest("T10Y2Y")
