# Architecture Decision Records

One file per decision. Frontmatter carries provenance (Section 6): `originator`,
`contributors` (role-tagged), `round-of-origin`, and `provoked-by` where a
failure exposed the flaw ("being the failure that exposed a flaw is also
authorship"). Credit is structural — it lives here and in git `Co-Authored-By`
trailers, never in recalled memory.

## Index

| ADR | Title | Originator | Status |
|-----|-------|-----------|--------|
| 001 | Prediction schema v1.0.1 + anchoring | claude (verify) | ratified |
| 002 | Write-Authority Matrix (+ Extensions 1-3) | claude · provoked-by gemini R3 | ratified |
| 003 | Sheets staging protocol (run_id + COMPLETE) | gemini | ratified |
| 004 | Oracle 4x2 regime (FRED + HYG proxy) | gemini | ratified |
| 005 | Capability ledger + nonce proofs | gemini | ratified |
| 006 | Frozen function signatures | per handoff | ratified |
| 007 | Reconcile upgrade (first-touch 15s) | per handoff | partial (Phase 3) |
| 008 | Calibration: multi-class Brier + Murphy | gemini · calibration claude | ratified |
| 009 | Collision severity + proximity | gemini · proximity claude | ratified |
| 010 | Conviction decay (P_base, lambda) | per handoff | ratified |
| 011 | Move-start detector (SPIKE + DRIFT) | gemini | ratified |
| 012 | 5/day alert budget | per handoff | ratified |
| 013 | Git provenance + provenance-as-weight | per handoff | ratified |
| 014 | LEAD TIME headline KPI | per handoff | ratified |
| 015 | Checkpoint predicate enum + match rules | gemini | ratified |
| 016 | Fixtures 1-14 regression guards | gemini (1-4) | ratified |
| 017 | Names Law v2 (boards) | gemini | ratified |
| 018 | Recurrence rule 3-in-10 | per handoff | ratified |
| 019 | Unified Four-Loop Blueprint | claude (Annex A) | ratified |
| 020 | Perpetual Calendar | claude (Annex A) | ratified |
| 021 | World Board + Domain Boards | claude (Annex A) | ratified |
| 022 | Two-Book Structure + Strategy Arena | claude (Annex A) | ratified |
| 023 | Run Ledger v1.0.1 | gemini · end-rules claude | ratified |
| 024 | Precursor Library | claude (Annex A) | ratified |
| 025 | Miss Ledger + Friday Replay | claude (Annex A) | ratified |
| 026 | Reader Corps (EDGAR/Drill 3) | gemini (chatter) | ratified |
| 027 | Backfill Program | claude (Annex A) | ratified |
| 028 | The Order Interlock | claude_code · ruling tyr | ratified |
| 029 | The Shadow Book (paper under the leash) | tyr | ratified |
| 030 | The Prior-Commitment Gate | claude (verify) · ratified tyr | ratified |
| 031 | Charter amendment: §-1 Why + status markers | claude_code · ratified tyr | ratified |
| 032 | The Frozen-Governor Enforcement Hook | claude_code · ratified tyr | ratified |
| 033 | Skill-relative weighting (weight-math) | per queued spec | reserved |

## Numbering caveat (honest)

Explicitly anchored in the constitution text: **002** (write-authority), **004**
(FRED), **007** (reconcile), **015** (checkpoint), **017** (Names Law), **018**
(recurrence), and **019–027** (Annex A, full text). The remaining 001–018 titles
are reconstructed from the Section-1 compressed descriptors + the provenance map;
full ADR text and exact `round-of-origin` await Gemini's Round-12 package.
→ `OPEN_QUESTIONS.md` OQ-ADR-FULLTEXT, OQ-ADR-NUMBERING. The handoff's "19 files"
vs the 27 numbered ADRs is likewise logged (OQ-ADR-COUNT).
