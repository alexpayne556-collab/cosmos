from __future__ import annotations

from cosmos import schema_validation as sv
from cosmos.quarantine import QuarantineReason
from cosmos import paths


def test_oracle_output_valid():
    row = {"regime": "CREDIT_CRISIS", "asset_class": "DEFENSIVE", "credit_strain": "ACUTE"}
    assert sv.is_valid(row, "oracle_output.schema.json")


def test_oracle_output_bad_enum():
    row = {"regime": "X", "asset_class": "MOON", "credit_strain": "ACUTE"}
    errs = sv.validate_against(row, "oracle_output.schema.json")
    assert any("asset_class" in e for e in errs)


def test_oracle_output_additional_property_rejected():
    row = {"regime": "X", "asset_class": "RISK_ON", "credit_strain": "LOW", "price": 1}
    errs = sv.validate_against(row, "oracle_output.schema.json")
    assert any("additional property 'price'" in e for e in errs)


def test_prediction_row_valid(valid_prediction):
    row = valid_prediction()
    assert sv.is_valid(row, "prediction_row.schema.json")


def test_prediction_row_missing_required():
    row = {"ticker": "FRO"}
    errs = sv.validate_against(row, "prediction_row.schema.json")
    assert any("missing required" in e for e in errs)


def test_validate_payload_routes_to_quarantine():
    bad = {"regime": "x", "asset_class": "NOPE", "credit_strain": "LOW"}
    ok, errs, qpath = sv.validate_payload(bad, "oracle_output.schema.json",
                                          source="unit")
    assert ok is False
    assert errs
    assert qpath is not None and qpath.exists()
    import json
    manifest = json.loads(qpath.read_text())
    assert manifest["reason"] == QuarantineReason.SCHEMA_INVALID.value
    # and the quarantine manifest itself is schema-valid
    assert sv.is_valid(manifest, "quarantine_manifest.schema.json")
