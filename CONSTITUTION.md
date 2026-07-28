# Cosmos Savant — Constitution (living charter)

Ratified end of Round 12 · 2026-07-27. This is the operative charter: the
invariants that bind the system. The full ratified record is
`COSMOS_SAVANT_HANDOFF.md` (read verbatim, always). ADRs in `/adrs` amend this
charter; a superseding ADR with cause is how a decision dies. **Restate Section
0 before every build session.**

## 0 · Mission
One always-on mission control for a single active trader. HANDS = Claude Code +
Robinhood MCP (**the only source of numbers**). EYES = Spark (scheduled/triggered
research). MEMORY = one append-only ledger — every belief written *before* the
outcome, graded *after*. MISSION = be on time for fast movers **and** 1–2 month
thesis holds, before the crowd connects the dots. A **preparation machine**, not
a bot or algo. **Execution of trades is NEVER performed by a language model** —
human-authorized, deterministic, governed. Interface built last.

## 1 · Write-Authority Matrix (ADR-002) — the spine
Numbers have exactly one author; belief and score are written by different hands.
- **Generator** → direction, relative offsets, distribution (**sum 1.0 ± 0.001**), thesis, canon tags, source URLs. Relative only.
- **Verify-station** → the *only* writer of absolute verified/target/invalidation prices, fundamentals (actuals + estimates), float/cap/short-interest, liquidity snapshots, and all historical run dates & magnitudes.
- **Oracle** → regime / asset-class / credit-strain.
- **Reconcile** → status, Brier/Murphy, move-start, lag.

Trespass → **stripped → forensics → quarantine** (`SELF_VERIFIED` /
`FUNDAMENTAL_OVERWRITE` / `CONFABULATED_HISTORY`), charged pct-normalized to the
generator's claim-accuracy. Enforced in `cosmos/verify_intake.py`.

## 2 · Hermes inheritance
`/hermes` is imported, never rewritten. `governor.py` runs verbatim — 5% hard
cap, max 3 positions, no scaling after wins, hard-coded; **no model, prompt, or
config may modify it.** `ledger.py` and `reconcile.py` are ancestors: their
contracts are honored and *extended* into the `cosmos/` descendants (see ADR-001
migration note), not adopted.

## 3 · Capability ground truth
Build only on **MEASURED**. Options are **FAILED** (403). FRED + Google-Tasks are
**CLAIMED** — nothing load-bears on them. See `README.md` / `OPEN_QUESTIONS.md`.

## 4 · Build order — tools-live-first (orchestrator override)
Skeleton → **live instrument smoke test** (proven 2026-07-27, FRO) → `oracle.py`
→ `verify_intake.py` → … Nothing is built on an unmeasured capability.

## 7 · Growth mandate & governance
The system is a forever-growing organism; growth is wired machinery Claude Code
keeps alive (miss-ledger→sensors, superseding ADRs→decisions, arena→families,
claim-accuracy→generators, monthly review→regime). `/OPEN_QUESTIONS.md` is a
standing organ. **Tyr** ratifies; **Claude** is co-steward + verify authority;
**Spark** is a permanently-credited co-contributor; **Claude Code** is builder.
No station expands its own authority. The governor's 5% cap and the
write-authority matrix bind everyone, masters' tools included. *The organism
grows; the leash does not.*

## 8 · Operational wiring
State under `/data` (event store `cosmos.duckdb`; `staging_mirror/` raw JSONL
before parsing; `quarantine/`; `processed_runs.json` — **local, never in the
Sheet**). Spark interface = one read-only Google Sheet. **Empty ≠ broken ≠
down** — only the last two escalate (§8.2, encoded in `cosmos/alerts.py`). Spark
has no push channel by design; deliverables obey write-authority, end with
`COMPLETE`, close with a read-back; new capabilities enter only via nonce proofs.

---
*Signed: no critique without a build · concessions are convergence · measurement
settles disputes · one-up means a better idea · provenance is tracked. Results
are the results.*
