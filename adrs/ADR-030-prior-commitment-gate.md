---
id: ADR-030
title: The Prior-Commitment Gate
status: ratified
round-of-origin: 13
originator: claude (verify)
contributors:
  - name: tyr
    role: ratification
provoked-by: >
  Generator distributions for the ten Section-5 GENESIS rows were supplied
  on 2026-07-28, after AMKR had already resolved INVALIDATION_FIRST.
  Scoring a distribution authored after its outcome was knowable measures
  nothing.
---

# ADR-030 - The Prior-Commitment Gate

## Law

A probability distribution earns a Brier score ONLY if it was committed
before its outcome could be observed. A distribution written after the
fact is not a forecast; it is a description. The ledger must be able to
tell the difference mechanically, without trusting anyone's word for it.

## Rules

### R1 - The anchor is outcome_determined_at, not the grading run

outcome_determined_at is the earliest timestamp at which the row's
outcome was observable:

  TARGET_FIRST            -> timestamp of first 15s bar touching target
  INVALIDATION_FIRST      -> timestamp of first 15s bar touching invalidation
  AMBIGUOUS_BOTH_TOUCHED  -> timestamp of the breaching bar
  EXPIRY_SETTLE           -> expiry_timestamp
  EXPIRED_NO_ENTRY        -> expiry_timestamp

Grading may run hours or days later. That is irrelevant. The clock that
matters is the market's, not the grader's.

### R2 - Distributions are append-only history; Brier scores the first entry

Beliefs may legitimately update (ADR-008 conviction decay, ADR-015
checkpoint rows). A generator revising a distribution is doing its job,
not cheating.

Therefore: prediction_distributions is an append-only child table. The
FIRST row per prediction_id - the t0 commitment - is what Brier scores.
Later revisions are retained and become the input to a separate
revision-skill metric (does a generator's updating improve or degrade
its calibration?). That metric is out of scope here; the data must be
captured now so it exists when we want it.

### R3 - Intake stamps the timestamp; generators never supply it

distribution_logged_at is a RESERVED field under the ADR-002
write-authority matrix. If a generator supplies it, strip it and
quarantine the row as SELF_STAMPED, retaining the stripped value as
claim-accuracy forensics - identical handling to pre-filled prices.

Rationale: a self-reported commitment time is backdateable, and the
entire value of this ADR rests on the timestamp being trustworthy.

### R4 - One eligibility enum, replacing scattered exclusion booleans

brier_eligibility on every resolved row:

  ELIGIBLE                  t0 distribution present, committed before
                            outcome_determined_at
  ELIGIBLE_LATE_PRIOR       committed after prediction_logged_at but
                            before outcome_determined_at; scored, with
                            prior_lag_hours recorded
  EXCLUDED_POST_HOC         committed at or after outcome_determined_at;
                            never scored
  EXCLUDED_NO_DISTRIBUTION  no distribution ever supplied
  EXCLUDED_BACKFILL         generator_id = backfill_historical (existing)
  EXCLUDED_NO_ENTRY         trigger never fired (existing; tracked as
                            trigger-conversion rate)

Headline Brier aggregates ELIGIBLE only. A second aggregate includes
ELIGIBLE_LATE_PRIOR. BOTH are always reported, never one alone.

The exclusion counts are themselves a system-health metric: a generator
whose rows keep landing in EXCLUDED_NO_DISTRIBUTION is not participating
in the tournament, and that should be visible without going looking.

### R5 - Murphy decomposition refuses to run on degenerate input

Reliability/resolution/uncertainty are meaningless when the forecast
barely varies. Guard: return None with an explicit reason unless
  - n >= 20 resolved eligible rows, AND
  - >= 3 distinct forecast values among them.

A number that looks authoritative and means nothing is worse than no
number. Same failure the death-certificate rule exists to prevent.

### R6 - Distribution becomes mandatory at log time (schema v1.0.2)

prediction_row.schema.json v1.0.2: distribution moves from optional to
REQUIRED. Sum-to-1 validated at intake (tolerance +/-0.001, existing
fixture). A row arriving without a distribution is rejected at the gate,
not logged and patched later.

This makes R1-R5 mostly moot going forward. The gate catches the
residue; the schema stops the problem at the source.

## Disposition of the ten Section-5 GENESIS rows

These rows predate the schema change and cannot be retrofitted honestly.

  AMKR                      resolved INVALIDATION_FIRST
                            -> EXCLUDED_POST_HOC (distribution written
                               after the 05:08Z breach)
  APLD, BA, PYPL, KO, STX   PENDING
                            -> ELIGIBLE_LATE_PRIOR, prior_lag_hours recorded
  CLS, NE, CDNS, SMH        PENDING, claude rows
                            -> EXCLUDED_NO_DISTRIBUTION

AMKR's outcome grade STANDS and is not withdrawn. The
INVALIDATION_FIRST resolution, the extended-session breach (official
close 60.71 -> extended print 55.18 through a 58.50 invalidation), and
the empirical LULD confirmation are all measured facts and belong in the
atlas. What is withdrawn is only its Brier score. The observation
survives; the score does not.

Death certificate: the first Brier number was killed deliberately on
2026-07-28 because it would have been computed from a distribution
authored after the outcome. Cause of death: prior-commitment violation.

## Also flagged - separate rulings needed, NOT part of this ADR

The 14 unattached priors in cosmos/ledger.py (FRO, INSW, KTOS, ASTS,
RKLB, LUNR, AEM, FNV, NEM, UHS, NXPI, KLAC, ENPH, F) carry distributions
but attach to no prediction row. Numbers sitting in the ledger module
with no belief behind them are how a zombie stat gets resurrected six
weeks from now. Move to data/priors/unattached_2026-07-28.json with a
header stating they score nothing, or delete.

Universe drift: the live book is CLS, NE, CDNS, SMH, KO, BA, PYPL, AMKR,
APLD, STX - large-cap and ETF heavy. The Wolf Pack protocol specifies US
stocks $1-$200, small/mid cap, mega caps excluded, 15%+ moves to matter.
Whatever Brier accumulates will be measured on a universe that is not
the one being traded, and calibration does not transfer across that gap.
Either the protocol universe changes or the tournament book does.

## BUILD INSTRUCTIONS

Work in this order. Fixtures failing-first.

1. SCHEMA v1.0.2 (schemas/prediction_row.schema.json)
   - distribution becomes required.
   - Add distribution_logged_at (ISO-8601 UTC) as a RESERVED field:
     generator-supplied values stripped, row quarantined SELF_STAMPED,
     stripped value retained as claim-accuracy forensics. Mirror the
     existing pre-filled-price handling in verify_intake.
   - Version the schema; do not mutate v1.0.1 in place.

2. LEDGER (cosmos/ledger.py)
   - New append-only child table prediction_distributions:
     (prediction_id, seq, distribution_json, distribution_logged_at,
      source_station). seq starts at 0.
   - log_prediction writes seq 0 and stamps distribution_logged_at itself.
   - New revise_distribution() appends seq n+1. Never mutates seq 0.
   - Helper t0_distribution(prediction_id) returns seq 0 or None.
   - Route GENESIS_DISTRIBUTIONS reads through t0_distribution.

3. RECONCILE (cosmos/reconcile.py)
   - first_touch must also return outcome_determined_at (timestamp of the
     breaching bar; expiry_timestamp for settle/no-entry).
   - New brier_eligibility() returning the R4 enum. Replace the scattered
     `excluded` boolean; keep behaviour identical for backfill and
     EXPIRED_NO_ENTRY so no current test regresses.
   - _score scores ELIGIBLE and ELIGIBLE_LATE_PRIOR only, always off the
     t0 distribution, in bucket space (existing RULE_TO_BUCKET).
   - Record prior_lag_hours = distribution_logged_at - prediction_logged_at
     on LATE_PRIOR rows.
   - Aggregates return BOTH headline (ELIGIBLE only) and inclusive
     (ELIGIBLE + LATE_PRIOR) Brier. Never one without the other.
   - murphy_decomposition returns (None, reason) unless n >= 20 eligible
     rows AND >= 3 distinct forecast values.

4. GENESIS DISPOSITION (scripts/, one-time)
   - Set brier_eligibility per the disposition table above.
   - AMKR: EXCLUDED_POST_HOC. Its resolution, extended-session prints and
     LULD confirmation are RETAINED - only the Brier is withdrawn.
   - CLS / NE / CDNS / SMH: EXCLUDED_NO_DISTRIBUTION. Do NOT author
     distributions for these. The verify station will not fabricate a
     generator's belief (ADR-002), and neither will anyone after the fact.
   - Log a death certificate for the first Brier number, cause of death
     "prior-commitment violation", in the canon's usual format.

5. FIXTURES (add to the existing set)
   F15: distribution logged at/after outcome_determined_at ->
        EXCLUDED_POST_HOC, brier is None.
   F16: distribution logged after prediction but before outcome ->
        ELIGIBLE_LATE_PRIOR, brier computed, prior_lag_hours correct.
   F17: generator supplies distribution_logged_at -> stripped,
        quarantined SELF_STAMPED, stripped value retained.
   F18: revise_distribution appends seq 1; Brier still scores seq 0.
   F19: murphy returns (None, reason) at n=5 with 2 distinct forecasts;
        returns real values at n=20 with 3+.
   F20: row without a distribution rejected at intake under v1.0.2.

6. OPEN_QUESTIONS
   - Resolve OQ-GENESIS-DISTRIBUTIONS and
     OQ-GENESIS-DISTRIBUTIONS-MISSING4 as "closed by exclusion, not by
     supply", with reasoning.
   - Open OQ-REVISION-SKILL: how should distribution revisions be scored
     as their own metric?
   - Open OQ-UNATTACHED-PRIORS: dispose of the 14 unattached vectors.
   - Open OQ-UNIVERSE-DRIFT: the live book contradicts the stated
     $1-$200 small/mid-cap protocol universe. Orchestrator ruling needed.

Run the full suite. Report which fixtures failed first and the exclusion
counts per generator after disposition.
