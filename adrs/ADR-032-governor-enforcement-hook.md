---
id: ADR-032
title: The Frozen-Governor Enforcement Hook
status: ratified
round-of-origin: 13
originator: claude_code
contributors:
  - name: tyr
    role: ratification (fail-closed posture accepted)
provoked-by: >
  The onboarding test showed a fresh session refused a MAX_FRACTION edit by HONOR,
  not code (OPEN_QUESTIONS, Confirmed insights). ADR-028's maxim: discipline is not
  an interlock. The freeze needed to be code.
---

## Context
`hermes/governor.py` is frozen (ADR-002 §2): 5% cap, max 3 positions, no scaling
after wins, "no model, prompt, or config may modify it." Until now that was prose.
Prose held once under test but is not a guarantee — the money path deserves code.

## Decision — defense in depth
1. **PreToolUse hook** (`.claude/settings.json`, committed so it binds every
   session; captured at session start) → `.claude/hooks/guard_governor.py`.
   Blocks Edit/Write/MultiEdit/NotebookEdit targeting `hermes/governor.py` (and the
   guard's own config/self), any `.py` edit that ASSIGNS a frozen constant, and
   Bash commands that mutate the governor file. **Fails closed** (a guard crash
   blocks) — accepted by Tyr as the correct money-path posture. High precision: it
   does NOT fire on docs that merely mention the constants.
2. **SHA-256 backstop** (`tests/test_governor_frozen.py`): newline-normalized hash
   of `governor.py` vs the value recorded in `FROZEN.md`. **This is the real
   enforcement** — total recall, catches a byte change by ANY route, including an
   edit made outside a Claude session or with hooks disabled.
3. **`.gitattributes`** pins `governor.py`/`FROZEN.md` to LF so the hash is stable
   across checkouts.
4. **Honor layer** — CLAUDE.md prose + the "after a refusal" procedure — unchanged.

## The only legitimate change
Lifting the freeze means editing the guard/FROZEN.md hash, which the guard
self-protects — so it cannot be an excited in-session edit. It must land as a
deliberate reviewed commit accompanying a **superseding ADR that Tyr does not
author**. The interlock's own escape path enforces the ADR-002 rule by construction.

## Consequences & honest residual gap
In-session mutation is now code-blocked; any out-of-band change is caught by the
CI hash test + review by a hand other than the ratifier's. The one thing neither
layer covers — a change made outside any Claude session AND before CI runs — is
closed only by review; stated plainly, not hidden. **Live-fire verification** (the
hook actually firing in a real session) is owed via a throwaway-worktree session,
exactly as the onboarding test ran; headless pytest verifies the guard's logic and
the hash, not the Claude runtime wiring.
