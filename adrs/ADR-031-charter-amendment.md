---
id: ADR-031
title: Charter amendment — §-1 Why-preamble + BUILT / BUILT-DIFFERENTLY / TARGET status markers
status: ratified
round-of-origin: 13
originator: claude_code
contributors:
  - name: tyr
    role: author of the §-1 "Why this exists" text; ratifier
  - name: claude (verify)
    role: review — caught the three-lane provenance error and the "unamendable" governor overreach
provoked-by: >
  Sessions started unoriented because only CLAUDE.md auto-loads, and the charter described target
  architecture in present tense (cosmos.duckdb, EYES=Spark, the Sheet interface) as if built —
  so restating it nightly would recite untruths.
---

## Context
CLAUDE.md (Step 1) instructs every session to read and restate the charter at start. The charter
must therefore be true before that instruction ships. Two problems: (1) the mission's *why* — the
reason the discipline is disproportionate to the codebase — lived only in chat, in no
read-at-start doc; (2) parts of the charter stated designed-but-unbuilt architecture in the
present tense.

## Decision
1. **Prepend `## -1 · Why this exists`** to `CONSTITUTION.md` — Tyr's statement of intent,
   verbatim, as the first thing read. CLAUDE.md's read-order and "restate before building" point
   at it.
2. **Standing status-marker convention**, applied across the whole charter, not only where flagged:
   - `BUILT` — accurate; the default, unmarked.
   - `[BUILT-DIFFERENTLY: …]` — the charter was factually wrong; corrected in place. First use:
     event store `cosmos.duckdb` → `cosmos.sqlite` (ratified "measured beats elegant", 2026-07-28).
   - `[TARGET: …]` — designed, not yet wired; explicitly marked. First uses: `EYES = Spark`
     (no push channel; manual paste), the Google-Sheet interface (`sync_staging` unbuilt), the Wall/UI.
   `grep '\[TARGET' CONSTITUTION.md` yields an instant list of what is still promise. Present-tense
   rewording would erase the design and lose the record of intent — keep both, permanently.
3. **Charter amendments land as ADRs** (the charter's own mechanism), preserving the ratification
   trail. This ADR is the precedent.

## Consequences
Every session reads the "why" and can tell built from promise at a glance; restating §0 no longer
recites untruths. `cosmos.sqlite` is now the charter-correct store. CLAUDE.md carries the
builder-facing distillation (four write-authority lanes, per-field; the frozen-governor path; the
refusal path).

## ADR numbering reservations (prevent forks)
- **031** — this amendment (ratified).
- **032** — builder discipline / hooks (CLAUDE.md Steps 2–4). RESERVED.
- **033** — skill-relative weighting (queued weight-math fix). RESERVED.
