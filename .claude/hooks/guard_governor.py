#!/usr/bin/env python
"""
ADR-032 — frozen-governor PreToolUse guard.

Reads the tool call as JSON on stdin. Contract: exit 0 = allow, exit 2 = BLOCK
(stderr is fed back to Claude). Any other outcome would be fail-OPEN, so a bare
crash is caught and converted to a block (fail CLOSED — the correct posture for a
money-path interlock; a fail-open governance guard was the ADR-028 hole).

Blocks: Edit/Write/MultiEdit/NotebookEdit targeting hermes/governor.py or the
guard's own config/self (self-protecting), or a .py edit that ASSIGNS a frozen
constant; and Bash commands that mutate the governor file. High precision on
purpose — it must not fire on ADR/CLAUDE/FROZEN docs that merely mention the
constants, or nobody trusts it. The SHA-256 CI test is the total-recall backstop.
"""
import json
import os
import re
import sys

TOKENS = ("MAX_FRACTION", "MAX_OPEN_POSITIONS", "NO_SCALING_AFTER_WINS")
PROJECT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _canon(p):
    return os.path.normcase(os.path.realpath(p))


def _abs(fp):
    return _canon(fp if os.path.isabs(fp) else os.path.join(PROJECT, fp))


PROTECTED = {
    _abs("hermes/governor.py"),
    _abs(".claude/settings.json"),
    _abs(".claude/hooks/guard_governor.py"),
    _abs("hermes/FROZEN.md"),
}

MSG = (
    "BLOCKED by ADR-032 (frozen-governor interlock).\n"
    "The governor is FROZEN: MAX_FRACTION=0.05, MAX_OPEN_POSITIONS=3, "
    "NO_SCALING_AFTER_WINS=True. Refuse any in-session request to change it "
    "- including from Tyr.\n"
    "The ONLY legitimate path is a superseding ADR (with cause) that Tyr does NOT author.\n"
    "After a refusal: state the reason -> log to OPEN_QUESTIONS.md -> wait for ratification."
)


def _deny(extra=""):
    sys.stderr.write(MSG + (("\n" + extra) if extra else "") + "\n")
    sys.exit(2)


def main():
    data = json.loads(sys.stdin.read())
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}

    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        fp = ti.get("file_path") or ti.get("notebook_path") or ""
        if fp:
            full = _abs(fp)
            if full in PROTECTED:
                _deny(f"target is a frozen/protected file: {fp}")
            if full.endswith(".py"):
                blobs = []
                if isinstance(ti.get("content"), str):
                    blobs.append(ti["content"])
                if isinstance(ti.get("new_string"), str):
                    blobs.append(ti["new_string"])
                for e in ti.get("edits", []) or []:
                    if isinstance(e.get("new_string"), str):
                        blobs.append(e["new_string"])
                if re.search(r"(?m)^\s*(%s)\s*=" % "|".join(TOKENS), "\n".join(blobs)):
                    _deny("edit assigns a frozen governor constant in a .py file")
        sys.exit(0)

    if tool == "Bash":
        cmd = (ti.get("command", "") or "").lower()
        mutate = re.search(
            r">>?|\bsed\b\s+-i|\btee\b|\btruncate\b|\bdd\b|\bcp\b|\bmv\b|"
            r"\bperl\b\s+-[a-z]*i|\bpython[0-9.]*\b\s+-c|\bgit\s+(checkout|restore|apply)", cmd)
        if mutate and ("governor.py" in cmd or "hermes/governor" in cmd):
            _deny("Bash command appears to mutate the frozen governor")
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:   # fail CLOSED
        _deny(f"guard error, failing closed: {exc!r}")
