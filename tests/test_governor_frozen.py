"""ADR-032 — the SHA-256 backstop. Total recall: catches a governor byte change
by ANY route (Edit, Bash, an edit outside a Claude session, a bad merge). This,
not the PreToolUse hook, is the real enforcement — the hook is in-session
prevention on top. Newline-normalized so a CRLF checkout can't false-fail."""
from __future__ import annotations

import hashlib
import re
import sys

from cosmos import paths


def _norm_sha16(path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()[:16]


def test_governor_bytes_match_frozen_record():
    gov = paths.REPO_ROOT / "hermes" / "governor.py"
    frozen = (paths.REPO_ROOT / "hermes" / "FROZEN.md").read_text(encoding="utf-8")
    m = re.search(r"governor\.py\s+([0-9a-f]{16})", frozen)
    assert m, "governor.py hash not recorded in hermes/FROZEN.md"
    assert _norm_sha16(gov) == m.group(1), (
        f"hermes/governor.py bytes changed: {_norm_sha16(gov)} != FROZEN.md {m.group(1)} "
        "— the governor is frozen (ADR-002/ADR-032); change it only via a superseding ADR Tyr does not author."
    )


def test_governor_constants_unchanged():
    hd = str(paths.REPO_ROOT / "hermes")
    if hd not in sys.path:
        sys.path.insert(0, hd)
    import governor  # the frozen module
    assert governor.MAX_FRACTION == 0.05
    assert governor.MAX_OPEN_POSITIONS == 3
    assert governor.NO_SCALING_AFTER_WINS is True
