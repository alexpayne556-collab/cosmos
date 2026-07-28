---
id: ADR-013
title: Git provenance + provenance-as-weight
status: ratified
round-of-origin: PENDING
originator: per-handoff
contributors: []
---

## Context
Credit must be permanent and *useful*, not decorative (Section 6).

## Decision
Every commit carries `Co-Authored-By:` trailers for contributing AIs. Every ADR
frontmatter carries `originator / contributors / round-of-origin` (+ `provoked-by`
where a failure exposed the flaw — that is also authorship). **Idea-source hit
rate is a scored weight**: whose ideas actually earned Brier over time feeds the
weight matrix. Credit is structural — git + frontmatter, never recalled memory.

## Consequences
Provenance is both permanent record and a live input to trust. See `adrs/README.md`
for the provenance map.
