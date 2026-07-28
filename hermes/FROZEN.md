# /hermes — Ancestry Vault (FROZEN)

Hermes Phase 1, proven working 2026-07-04 (60 real resolved predictions).
This directory is the oldest surviving organ of the project (Section 2). It is
imported, **never rewritten**.

## Disposition (per the orchestrator's ratified correction)

| File | Disposition | Runs live? |
|------|-------------|------------|
| `governor.py` | **IMPORT VERBATIM · UNTOUCHABLE.** `MAX_FRACTION=0.05`, `MAX_OPEN_POSITIONS=3`, `NO_SCALING_AFTER_WINS`. "The organ that decides HOW MUCH must never be reachable by the organ excited about HOW GOOD." Confidence is not an input. **Never modify.** | **YES** |
| `ledger.py` | **ANCESTOR, NOT ADOPTED.** Read-only forebear. The live event store is the v1.0.1 descendant, which *inherits* append-only discipline + the duplicate-rejection contract and *extends* the schema. See ADR-001 migration note. | no |
| `reconcile.py` | **ANCESTOR, NOT ADOPTED.** Grading predates ADR-007. The live grader upgrades to first-touch on 15s bars (incl. extended session), multi-class Brier, Murphy. | no |
| `seed_demo.py`, `hermes.db` | Demo / proof artifacts. Never fed to production. | no |
| `HERMES_MASTER_SPEC.md`, `HERMES_CANON_v1.2_EVIDENCE_AUDITED.md`, `README.md` | Original records, preserved. | n/a |

## Frozen-core integrity (SHA-256, first 16 hex)

```
governor.py   8b466f75e8c93295
ledger.py     98e90cdcf27b1a70
reconcile.py  09f0d892560c02cb
```

Any change to `governor.py` or `ledger.py` bytes is a governance violation, not
a refactor. `reconcile.py` is the single Hermes file explicitly slated for an
ADR-007-governed upgrade — and even that happens in a *descendant* module
(`cosmos/`), leaving this ancestor byte-identical.

## Verify-station note (design-inherited / code-new)

Section 2 attributes a "duplicate `prediction_id` rejected" contract to the
ledger. The Phase-1 code does **not** implement it (autoincrement `id`, no
`prediction_id`, plain `INSERT`). The contract is therefore *design-inherited,
code-new*: it is implemented fresh in `cosmos/verify_intake.py`. Nothing was
"ported" — see ADR-001. (OQ-LEDGER-APPENDONLY: keep in-place resolution, or go
fully event-sourced?)
