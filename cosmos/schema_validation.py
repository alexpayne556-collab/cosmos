"""
Self-contained JSON-Schema (draft 2020-12 subset) validator + loader.

Supported keywords: type, const, enum, minimum, maximum, exclusiveMinimum,
exclusiveMaximum, minLength, maxLength, pattern, minItems, items, required,
properties, additionalProperties. This is deliberately dependency-free so the
grading and intake pipelines never fail to import; the schemas we author stay
within this subset. `validate_payload` pairs validation with quarantine
routing for the intake path.

(OPEN_QUESTIONS: swap to the `jsonschema` library if we ever need full
draft-2020-12 semantics — tracked as OQ-SCHEMA-1.)
"""
from __future__ import annotations

import functools
import json
import re
from typing import List, Optional

from . import paths
from .quarantine import QuarantineReason, quarantine


class SchemaLoadError(Exception):
    pass


@functools.lru_cache(maxsize=None)
def load_schema(name: str) -> dict:
    p = paths.SCHEMAS_DIR / name
    if not p.exists():
        raise SchemaLoadError(f"schema not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _type_ok(value, t: str) -> bool:
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if t == "boolean":
        return isinstance(value, bool)
    mapping = {"object": dict, "array": list, "string": str, "null": type(None)}
    py = mapping.get(t)
    return isinstance(value, py) if py is not None else True


def validate(instance, schema: dict, *, path: str = "$") -> List[str]:
    """Return a list of human-readable validation errors ([] == valid)."""
    errs: List[str] = []

    t = schema.get("type")
    if t is not None:
        types = t if isinstance(t, list) else [t]
        if not any(_type_ok(instance, tt) for tt in types):
            errs.append(f"{path}: expected type {t}, got {type(instance).__name__}")
            return errs  # downstream keyword checks are moot on a type mismatch

    if "const" in schema and instance != schema["const"]:
        errs.append(f"{path}: expected const {schema['const']!r}, got {instance!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errs.append(f"{path}: {instance!r} not in enum {schema['enum']}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errs.append(f"{path}: {instance} < minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errs.append(f"{path}: {instance} > maximum {schema['maximum']}")
        if "exclusiveMinimum" in schema and instance <= schema["exclusiveMinimum"]:
            errs.append(f"{path}: {instance} <= exclusiveMinimum {schema['exclusiveMinimum']}")
        if "exclusiveMaximum" in schema and instance >= schema["exclusiveMaximum"]:
            errs.append(f"{path}: {instance} >= exclusiveMaximum {schema['exclusiveMaximum']}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errs.append(f"{path}: length {len(instance)} < minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errs.append(f"{path}: length {len(instance)} > maxLength {schema['maxLength']}")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            errs.append(f"{path}: does not match pattern {schema['pattern']!r}")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errs.append(f"{path}: {len(instance)} items < minItems {schema['minItems']}")
        if "items" in schema:
            for i, item in enumerate(instance):
                errs.extend(validate(item, schema["items"], path=f"{path}[{i}]"))

    if isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                errs.append(f"{path}: missing required property '{req}'")
        props = schema.get("properties", {})
        for key, subschema in props.items():
            if key in instance:
                errs.extend(validate(instance[key], subschema, path=f"{path}.{key}"))
        if schema.get("additionalProperties") is False:
            for key in sorted(set(instance) - set(props)):
                errs.append(f"{path}: additional property '{key}' not allowed")

    return errs


def validate_against(instance, schema_name: str) -> List[str]:
    return validate(instance, load_schema(schema_name))


def is_valid(instance, schema_name: str) -> bool:
    return not validate_against(instance, schema_name)


def validate_payload(instance, schema_name: str, *,
                     source: Optional[str] = None,
                     reason: QuarantineReason = QuarantineReason.SCHEMA_INVALID):
    """Validate; on failure route the payload to quarantine and return
    (False, errors, quarantine_path). On success return (True, [], None)."""
    errs = validate_against(instance, schema_name)
    if errs:
        qp = quarantine(instance, reason=reason, errors=errs,
                        source=source or f"schema:{schema_name}")
        return False, errs, qp
    return True, [], None
