# OPEN_QUESTIONS — the living register of known-unknowns

Per Section 7: every guessed threshold, unfit parameter, flagged ambiguity,
unverified capability, and un-run experiment. Reviewed in the weekly replay. A
closed question links the ADR or commit that resolved it. A register that
shrinks then regrows is a healthy organism; an empty one is blindness.

## Guessed thresholds / unfit parameters
- **OQ-ORACLE-1** — HY OAS band edges (3.0 / 4.5 / 7.0 %) in `cosmos/oracle.py` are guessed. Fit against historical BAMLH0A0HYM2 regimes. (ADR-004)
- **OQ-ORACLE-2** — HYG-proxy OAS calibration (`base_oas=3.5`, `sensitivity=8.0`) guessed; fit HYG-drawdown → OAS. (ADR-004)
- **OQ-TRIPWIRE-1** — Phase-0 null band σ = 20d close-to-close log-return σ · √(h/6.5); horizon units TBD. **ATR banned per the 1.6σ bug.** (Phase 5)
- **OQ-DECAY-1** — conviction decay λ per event type; P_base = ledger class rate (no data yet). (ADR-010)
- **OQ-COLLISION-1** — Proximity = horizon-overlap fraction; exact definition to fit. (ADR-009)
- **OQ-RUNLEDGER-1** — volume-shape tercile cuts (>50% first / >40% last); 50%-retrace-sustained-10min end rule. (ADR-023)
- **OQ-RECURRENCE-1** — recurrence window exactness (3-in-10). (ADR-018)
- **OQ-ALERTS-1** — 5/day alert-budget ranking weights (W × surprise × decay). (ADR-012)

## Ambiguities / spec gaps
- **OQ-CHECKPOINT-1** — is the checkpoint predicate enum complete, or are T+1w/T+2w/T+4w interim-checkpoint predicate types owed? (ADR-015 / ADR-022)
- **OQ-RECONCILE-P3** — the reconcile-upgrade spec (point 3) was truncated at `AMBIGUOUS_BOTH_TOUCHED=loss,`. Full ADR-007 list (move-start/lag capture, checkpoint match rules) still owed. Blocks Phase 3 only.
- **OQ-FIXTURES-1** — fixtures 1-14 are RECONSTRUCTED from failure fingerprints; ratify against Gemini's exact Round-12 enumeration. (ADR-016)
- **OQ-LEDGER-APPENDONLY** — v1.0.1 ledger: keep Hermes' in-place resolution UPDATE, or go fully event-sourced (separate resolution event)? (ADR-001 migration)
- **OQ-STX-ANCHOR** — STX row is ANCHOR_PENDING to the Jul 28 close (ADR-001 rule: last official close preceding release).

## ADR provenance / structure
- **OQ-ADR-FULLTEXT** — full text for ADR-001..018 (only compressed descriptors held).
- **OQ-ADR-NUMBERING** — 001-018 numbering reconstructed; confirm against Gemini's package.
- **OQ-ADR-COUNT** — handoff says "/adrs (19 files)"; 27 ADRs are numbered. Reconcile.
- **OQ-ADR-ROUND** — `round-of-origin` unknown for most ADRs (only ADR-002's round-3 provoker is known).

## Unverified capabilities (CLAIMED — nothing load-bears)
- **OQ-FRED-CAP** — FRED direct access not in the MEASURED set; needs API key / nonce proof. HYG proxy (over MEASURED Robinhood bars) is the load-bearing path.
- **OQ-GTASKS-CAP** — Drill-3 names a "Google Tasks queue" for human alerts; not measured. Load-bearing alert path is local `/data/alerts.jsonl` + Sheet mirror; Google-Tasks delivery pending a `capability_proofs` nonce.
- **OQ-OPTIONS** — options quotes FAILED (403, no entitlement). All implied-move features dead until entitlement changes.

## Boards
- **OQ-BOARDS-PRESS** — ADR-021 enumerates no shipping press for HORMUZ (Lloyd's List / TradeWinds proposed, pending).
- **OQ-BOARDS-URLS** — boards carry descriptive source names; Names Law wants one literal source URL per claim.

## Unverified third-party claims
- **OQ-SPARK-DECAY-ARC** — Spark's decay-arc statistics (412 equities / 64 trading days; forward-10d returns by ordinal appearance +4.5 / +1.1 / -3.2 / -11.8 %; win rates 54.4 / 44.4 / 37.5 / 23.7 %) are **unverified third-party stats** — Spark has no market-data feed. Verify-station audit 2026-07-28: **all 9 named exemplars EXIST and trade**; the 4-class taxonomy is corroborated in the tape (VTIX/LGVN dilution, BDSX sustained, QTTB/RXT serial-catalyst, DAIO noise — 6/9 clean). **Decay magnitudes NOT reproduced.** Ruling: numbers do not enter code; the classifier ships `expected_return=None`, populated ONLY from our own 90-day backfill atlas (ADR-027). Evidence: `data/verify/spark_ticker_audit_2026-07-28.json`; code: `cosmos/analytics/top_gainers_tracker.py`.
- **OQ-GAINER-OVERLAP** — the four gainer classes are NOT mutually exclusive: STAK was a violent 20-spike pump that also sat 79% off its 52w high (dilution+catalyst); CVGI/AIRS fit no clean box. Consider multi-label / confidence. Classifier currently emits a primary class + `overlap_flags`.
- **OQ-GAINER-DILUTION-SCOPE** — `TopGainersTracker._classify_recurrence_pattern` tags DILUTION CYCLE when `sec_filings` contains any S-3/S-1/ATM/6-K. Correct ONLY if `sec_filings` is scoped to recent / recurrence-window filings (per ADR-026 dilution radar); an all-time list over-flags almost every issuer (nearly all have an S-3 shelf). Caller must window-scope the filing list.
- **OQ-GAINER-LENS-RECONCILE** — two lenses now coexist in `cosmos/analytics/top_gainers_tracker.py`: the recurrence+filing classifier (returns display strings "DILUTION CYCLE" etc. + a `HYPOTHESIS_*` tag) and the price-behavior classifier (`GainerClass` enum, underscored). Reconcile the taxonomy naming and decide which is primary. `mean_interval` is currently unused in the recurrence classifier.

## Confirmed insights
- **LULD / extended session (Spark — verified, stands):** Limit-Up/Limit-Down halts apply during REGULAR hours only; AH/PM sessions genuinely lack that circuit breaker. Real structural insight. Directly relevant to extended-session first-touch grading (ADR-007) and the AMKR loss (Jul 27, traded through invalidation in the extended session) — an invalidation can be blown through by an after-hours gap with no halt to arrest it.

## Resolved
- **OQ-BACKOFF-1** — Drill-2 (Sheets) 30s→2m→8m vs Drill-3 (EDGAR) 30s→2m→10m are intentionally distinct. RESOLVED — both encoded as `SHEETS_PROFILE` / `SEC_EDGAR_PROFILE` in `cosmos/backoff.py`.
- **OQ-HANDOFF-CONST** — `COSMOS_SAVANT_HANDOFF.md` is the verbatim record; `CONSTITUTION.md` is the living charter ADRs amend. RESOLVED.
- **OQ-SCHEMA-1** — dependency-free JSON-Schema-subset validator shipped; swap to `jsonschema` lib only if full draft-2020-12 semantics are ever needed. RESOLVED (deferred by design).
