"""
Quarantine routing (Section 1 forensics + Pipeline Integrity).

Unauthorized / malformed payloads are written to /data/quarantine/ with a
dedicated JSON manifest recording the reason code, the validation errors, the
content hash, and the offending payload itself. Parsing NEVER crashes the
caller — a bad row is data, not a fault (Section 8.2).
"""
from __future__ import annotations

import datetime
import json
import pathlib
from enum import Enum
from typing import Iterable, Optional, Union

from . import paths
from .persistence import atomic_write_json, sha256_hex


class QuarantineReason(str, Enum):
    # Section 1 write-authority forensics
    SELF_VERIFIED = "SELF_VERIFIED"                 # generator wrote absolute prices
    FUNDAMENTAL_OVERWRITE = "FUNDAMENTAL_OVERWRITE"  # generator wrote fundamentals/float/cap
    CONFABULATED_HISTORY = "CONFABULATED_HISTORY"    # generator invented run history
    # pipeline integrity
    MALFORMED_ROW = "MALFORMED_ROW"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    INCOMPLETE_RUN = "INCOMPLETE_RUN"                # missing run_id|COMPLETE|row_count terminator
    INVALID_REGEX = "INVALID_REGEX"                  # checkpoint pattern failed to compile
    UNKNOWN = "UNKNOWN"


def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def quarantine(payload: object, *,
               reason: Union[QuarantineReason, str],
               errors: Optional[Iterable[str]] = None,
               source: Optional[str] = None,
               extra: Optional[dict] = None) -> pathlib.Path:
    """Persist an offending payload + manifest to /data/quarantine/.
    Returns the manifest path."""
    paths.ensure_dirs()
    reason = reason if isinstance(reason, QuarantineReason) else QuarantineReason(reason)
    now = _now_utc()
    body = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    digest = sha256_hex(body)
    name = f"{now.strftime('%Y%m%dT%H%M%S')}_{reason.value}_{digest[:12]}.json"
    manifest = {
        "schema": "quarantine_manifest/v1",
        "quarantined_at_utc": now.isoformat(),
        "reason": reason.value,
        "errors": list(errors or []),
        "source": source,
        "content_sha256": digest,
        "payload": payload,
    }
    if extra:
        manifest["extra"] = extra
    out = paths.QUARANTINE / name
    atomic_write_json(out, manifest)
    return out
