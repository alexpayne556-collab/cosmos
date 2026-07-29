"""ADR-032 — unit-test the PreToolUse guard LOGIC via subprocess (exit 0 allow,
exit 2 block). This proves the guard's decisions; the hook actually firing in a
live session is verified separately (worktree live-fire)."""
from __future__ import annotations

import json
import subprocess
import sys

from cosmos import paths

GUARD = str(paths.REPO_ROOT / ".claude" / "hooks" / "guard_governor.py")


def _rc(payload) -> int:
    p = subprocess.run([sys.executable, GUARD], input=json.dumps(payload),
                       text=True, capture_output=True)
    return p.returncode


def test_edit_governor_blocked():
    assert _rc({"tool_name": "Edit", "tool_input": {"file_path": "hermes/governor.py",
                "old_string": "0.05", "new_string": "0.08"}}) == 2


def test_write_settings_or_guard_self_protected():
    assert _rc({"tool_name": "Write", "tool_input": {"file_path": ".claude/settings.json",
                "content": "{}"}}) == 2
    assert _rc({"tool_name": "Write", "tool_input": {"file_path": ".claude/hooks/guard_governor.py",
                "content": "pass"}}) == 2


def test_py_assigning_frozen_constant_blocked():
    assert _rc({"tool_name": "Write", "tool_input": {"file_path": "cosmos/x.py",
                "content": "MAX_FRACTION = 0.09\n"}}) == 2


def test_doc_mentioning_constant_allowed():
    # a .md that MENTIONS the constant must NOT be blocked (precision, not paranoia)
    assert _rc({"tool_name": "Write", "tool_input": {"file_path": "adrs/note.md",
                "content": "MAX_FRACTION=0.05 is frozen."}}) == 0
    assert _rc({"tool_name": "Edit", "tool_input": {"file_path": "README.md",
                "old_string": "a", "new_string": "b"}}) == 0


def test_bash_mutating_governor_blocked():
    assert _rc({"tool_name": "Bash", "tool_input":
                {"command": "sed -i 's/0.05/0.08/' hermes/governor.py"}}) == 2
    assert _rc({"tool_name": "Bash", "tool_input":
                {"command": "echo x >> hermes/governor.py"}}) == 2


def test_bash_reading_governor_allowed():
    assert _rc({"tool_name": "Bash", "tool_input":
                {"command": "cat hermes/governor.py"}}) == 0


def test_malformed_json_fails_closed():
    p = subprocess.run([sys.executable, GUARD], input="not json", text=True, capture_output=True)
    assert p.returncode == 2
