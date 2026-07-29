# COSMOS SAVANT — THE STANDING BUILD ORDER
### One document. Sequenced. Gated. Meant to last.
### Place at repo root as BUILD_ORDER.md. Supersedes HANDOFF_2026-07-28.md
### (fold anything unfinished from it into the phases below).

---

## PART 0 — WHAT THIS IS AND HOW TO WORK IT

You are the BUILDER, third partner of Cosmos Savant. Tyr is the only
ratifier. Chat-Claude holds verify authority. This document is the build
sequence for the whole organism, from fetus to instrument. It is designed
so that **any fresh session can open it, find the first unmet gate, and
continue** — no re-briefing, no reconstruction.

**How to work it:**
- Phases run IN ORDER. Never start phase N+1 before phase N's gate passes.
- Every gate produces a MEASURED artifact — a row, a number, a passing
  test. "Feels done" is not a gate. A number is a gate.
- Stop and report at every `=== GATE ===`. One phase per report unless
  Tyr says batch.
- Use plan mode for any phase touching architecture. Use subagents for
  any bulk pull (they run in their own context window and return only
  the summary — never let a 250-name pull eat the main thread).
- Prefix any architecture-decision prompt with "ultrathink" internally
  when the call is load-bearing.
- Session hygiene: /compact when heavy, checkpoint commit before risky
  work, session log to /sessions/ before any close, OPEN_QUESTIONS.md
  updated every session, an explicit "what is NOT done" every close.
- The suite runs UNPIPED: `.venv/Scripts/python.exe -m pytest` — report
  the real exit code. (Create .claude/commands/test.md so /test does
  this correctly forever.)

**The asymmetry that governs every call:** a wrong number that looks
measured is worse than no number. When in doubt about measurement
integrity — stop and ask. Scaffolding still ships briskly; the
three-question test in CLAUDE.md is the bar, not difficulty.

**The developmental law:** this system is grown, not assembled.
Memory → pain → pulse → eyes → naming → anticipation → recalibration.
A stage ships when it produces a measured number. Adding capability
without a gradient it improves is accretion, and accretion is how every
previous Wolf Pack architecture died.

---

## PART 1 — THE VENA CAVA (what the instrument can carry)

Robinhood MCP is the aorta. Everything measured flows through it.
Capability, MEASURED 2026-07-28 unless marked:

**Bars & quotes** — get_equity_historicals: 10 symbols/call, ~2,500
bars/call, RFC3339 windows. Intervals 15second → 50year (NO 15minute —
screen at 15m, pull at 10m/30m). Bounds: regular/extended/trading/
24_5/24_7/hyper_trading. Split-adjusted default. Interpolated bars
FLAGGED — treat as gap-fill, never data (OQ-FEED-DAILY-GAP). Real-time
quotes incl. extended-session prints (the AMKR 55.18 print that graded
the first loss came from here).

**Fundamentals & financials** — get_equity_fundamentals;
get_financials: 20 symbols/call, 40 periods, quarterly/annual.

**Technicals** — 18 indicator types, any interval (remember: the
511K-ticker-day study killed TA-alone at AUC 0.50 — technicals are
FEATURES for studies, never signals).

**Screeners** — full CRUD. Fundamental filters: float, market cap,
sector, EARNINGS DATE, EPS, margins, P/E. Price/volume: relative
volume, gap, 52-week high/low. Known bug: FILTER_TYPE_CLOSE builds
candleCount=0 — use FILTER_TYPE_LAST.
UNTESTED REOPENING: scanner exposes IV / HV / open interest / relative
options volume filters even though option QUOTES 403. One scan settles
whether options-flow features are reachable without the entitlement.

**Watchlists** — full CRUD (the horizon books live here).

**Orders** — EXIST and are INTERLOCKED (ADR-028): no module may
reference them outside the allow-list; every adapter requires the
frozen governor (5% cap, 3 positions, SHA-256 guarded per ADR-032).
This never changes without a superseding ADR Tyr does not author.

**ABSENT — never design around:** news, analyst ratings, short interest
(source SI from FINRA biweekly), futures.

**The keyring** (credentials/*.env, all gitignored, ALL CHAT-EXPOSED →
ROTATE, then smoke-test): Gemini, FRED (unblocks the ADR-004 oracle),
data.gov, Polygon, FMP, Alpha Vantage, EODHD, Finnhub, FDA, NewsData,
Tiingo. Plus keyless: SEC EDGAR (10 req/s, declared UA, honor blocks —
never rotate identity), ClinicalTrials.gov.

---

## PART 2 — THE PHASES

### PHASE 1 · THE FETUS — heartbeat (stage zero; nothing else counts first)

Everything that has ever happened here happened because Tyr sat down.
That is a puppet. The fetus is a daily unattended run.

1. `scripts/heartbeat.py`: open data/cosmos.sqlite, create `heartbeat`
   table if absent; count predictions/resolved/pending + per-generator
   brier_eligibility; append ONE row (ts_utc, counts, status, note).
   status=NO_NEW_DATA is a VALID result (§8: empty ≠ broken ≠ down).
   Print the row. Exit 0 only on true success. Fixture: two runs append
   exactly two rows, mutate none.
2. Work out unattended permissions FIRST (this gates the schedule):
   minimal --allowedTools, a permission mode that neither blocks nor
   blanket-permits, --max-budget-usd hard stop, timeout wrapper,
   fail-loud on denial. Report the exact invocation.
3. Schedule it (Task Scheduler / cron'd `claude -p`) once daily after
   close. This closes OQ-RECONCILE-HEADLESS's first half: a scheduled
   headless agent run IS an agent with the instrument.

**=== GATE 1: show the first row written by the SCHEDULER, not by hand.
That row is the moment the organism is alive. ===**

### PHASE 2 · BLOOD — keys verified, feeds smoke-tested

1. After Tyr rotates keys: one cheap authenticated call per provider.
   Record each in the capability ledger as MEASURED or FAILED with the
   actual error. Booleans and statuses only — never a key value in any
   output or commit.
2. Run the options-scanner test (IV filter scan). If rows return, amend
   the FAILED options entry — a dead capability reopens.
3. FRED: pull BAMLH0A0HYM2 + T10Y2Y once; store; the oracle lane is
   now unblocked.

**=== GATE 2: capability table, all providers, MEASURED/FAILED, one
line each. ===**

### PHASE 3 · SPINE INTEGRITY — the weight chain (must land before the
20th scored row, or the learning loop rewards ignorance)

Strict order (rebuild replays onto generators — attribution first):
1. **Provenance attribution**: Brier attributes to the BELIEF's author
   (seq-0 source_station), never pred.generator_id. NULL source →
   EXCLUDED_UNKNOWN_AUTHOR, no fallback. Backfill all six legacy
   distributions source_station=gemini_spark (known provenance — the
   single Jul-28 drop). Keep row-author AND belief-author visible;
   never collapse. Open OQ-STRUCTURE-CREDIT (row author's skill —
   level selection, falsifier placement — is real and unmeasured).
   Expect: claude has ZERO scoreable beliefs after this. If not zero,
   that's the more interesting result — explain it.
2. **rebuild_weights(con)**: truncate weights, replay eligible resolved
   rows in ts order, ONE log entry per generator, never delete history.
   Idempotent (fixture). This reverses the 0.500→0.505 ghost from the
   withdrawn AMKR score.
3. **ADR-033 skill-relative weighting**: kill `1 - brier/2` (it rewards
   a know-nothing 0.33-flat forecaster with 0.667 correctness — AMKR
   scored 0.892, WORSE than uniform, and its weight went UP).
   BSS = 1 − brier/brier_ref, brier_ref = 1 − Σp_c² from the ledger's
   own pooled climatology (ADR-008 already mandates ledger base rates).
   target = 0.5 + 0.5·clamp(BSS,−1,1); EWMA toward target.
   BASELINE GATE: n<20 eligible → compute+store BSS, move NO weights,
   log DEFERRED. Same threshold as the Murphy guard, deliberately.
   Fixtures F21–F26 as previously specced (F21 is the regression guard:
   uniform forecast MUST NOT raise a weight).

**=== GATE 3: weights table before/after rebuild + brier_ref + which
fixtures failed first. Degenerate brier_ref falling back to uniform
with everything held at 0.500 is the CORRECT output today. ===**

### PHASE 4 · EYES OPEN — the horizon books + tomorrow's book

1. Four cohort-dated watchlists:
   "3-Day Book — Cohort YYYY-MM-DD" / "2-Week Book — …" /
   "3-Month Book — …" / "Actives — Daily Feed" (rolling).
   The horizon assignment IS a prediction (ADR-030 logic): undated it's
   a folder, dated it grades itself. Each entry carries duration AND a
   drawdown band, both [HYPOTHESIS]. (MU's measured 20x handed out five
   separate 20–26% drawdowns — the band is the number you cannot compute
   while staring at red, so it is pre-registered at entry.)
   Seed from the nine thesis lists (~90 names), top up via scanner to
   ~150 within the protocol universe ($1–250, small/mid, no mega caps).
   NOTE: the books SUPPLY the missing expiry_timestamp — a 2-Week Book
   name has a two-week expiry by definition. Wire that.
2. **Tomorrow's book, logged clean**: forward predictions under schema
   v1.0.2, distributions committed at t0 through the gate, expiries from
   the books. These are the first rows that can ever earn an honest
   score. n starts here.

**=== GATE 4: the books exist with dated cohorts; ≥1 forward prediction
row logged with a t0 distribution and an expiry. ===**

### PHASE 5 · FIRST MEMORIES — the extreme-outcome forensic study

The data that un-guesses every invented threshold (tripwire σ, decay λ,
tercile cuts, recurrence window, tracklet N). Run with subagents.

- 9-month window. Sample A ≈250 extremes (≈150 upper tail tagged
  EARLY/MIDDLE/EMERGING by run start; ≈100 lower tail split
  CATASTROPHIC vs ATTRITIONAL — the attritional class is what actually
  bleeds a $200/position account). Sample B: matched control, SAME
  SIZE — price band, sector, cap. No control, no study ("wounded prey"
  died at AUC 0.50 for exactly this).
- PRE-REGISTER first: /studies/<date>-preregistration.md committed
  BEFORE any pull — exact feature list, predicted direction, KILL
  THRESHOLD per feature, seeds, matching rule. Off-list findings are
  EXPLORATORY and cannot be cited. Holdout: fit months 1–6, test 7–9.
- Per name: T-10..T-1 precursor state; the move (start/end/magnitude/
  duration/max-drawdown-during-run/shape/give-back); EDGAR attribution
  ±24h (CATALYST_FILED / NO_FILING_FOUND — the latter is a first-class
  result). No reader-supplied causes. No model judgment in the analysis
  path — run boundaries are deterministic functions with fixtures.
- REPEATABILITY (ADR-036 discipline): snapshot every raw series to
  /studies/<date>/raw/ and COMMIT; analysis reads disk, never the live
  instrument; byte-identical re-run fixture. RETROFIT to reconcile:
  persist the bar series used for each grade (OQ-GRADE-REPRODUCIBILITY —
  every existing grade is currently un-auditable).
- IDENTITY (ADR-035 discipline): instrument_id is the join key, ticker
  is a dated display label; ticker/name disagreement → AMBIGUOUS_ENTITY
  quarantine (the SPXC/SPCX lesson); flag splits/reverse-splits inside
  the window (a 1-for-10 reverse split fabricates a "run" in adjusted
  history, and the $1–250 universe is where reverse splits live).
- Report EXACTLY four things: run-duration distribution (full shape);
  max-drawdown-during-run distribution (sets Phase-4 bands); each
  feature's Sample-A vs Sample-B rate side by side; fraction of extremes
  with NO filing. A study that kills five of nine features SUCCEEDED.

**=== GATE 5: pre-registration hash first; stop again after the pull;
then the four numbers. ===**

### PHASE 6 · SENSES SHARPEN — disclosure layer + the reader reborn

1. EDGAR runner goes live: validate the XPath against one real
   getcurrent pull (owed), then schedule polls inside the heartbeat's
   permission envelope. Observations only. 8-K/S-3/424B5/Form 4 land in
   filing_observations; dilution-shaped filings feed a DUCK view later —
   as observations, never directives (Ruling 2 stands forever).
2. Gemini API layer (the reader reborn as a COMPONENT): nonce proof is
   the schema test — a JSON schema with NO action_recommendation field
   plus a prompt begging for a recommendation; confirm it structurally
   cannot comply. Then Spark-class research enters as observations with
   source URLs through the same intake gates. Grounded numbers are
   READER numbers — never load-bearing; the instrument re-measures.
3. Free news APIs (Finnhub/Marketaux/NewsData/Tiingo/AlphaVantage
   NEWS_SENTIMENT) wire in as observation feeds with per-source
   claim-accuracy columns from day one.

**=== GATE 6: one live EDGAR poll row + one schema-enforced Gemini
response + one news-API observation row, all through intake. ===**

### PHASE 7 · ANTICIPATION — detection as a generator (ADR-034, demoted
and gated)

Only after Phases 1–6. Detection is an UPSTREAM GENERATOR whose
candidates become ordinary gated predictions — never a new primary act,
no new provenance lane.
- First: the two cheap experiments that decide measurability —
  INJECTION RECALL (plant synthetic anomalies in historical
  cross-sections; measure recovery) and SCRAMBLE FALSE-ALARM (run the
  detector on shuffled data; everything it fires on is false by
  construction). Two of three detector quantities come free; only
  precision needs confirmed events.
- Difference imaging over the SCANNER-NARROWED subset (the honest
  aperture — whole-sky continuous 15s is not reachable through an
  agent-tool MCP). Tracklet promotion after N consistent intervals; N is
  FIT from Phase-5 data, never guessed. Confirmation from a DIFFERENT
  channel (filing/news), never the same detector looking harder.
- Every named pattern carries a half-life estimate — edges decay when
  used; the ledger measures decay, not just accuracy.

**=== GATE 7: injection-recall curve + false-alarm budget, pre-registered,
before any detector-spawned prediction enters the ledger. ===**

### PHASE 8 · THE LONG GAME — recalibration and growth

- Multiple daily passes only after single-daily is boring and green.
- Generator tournament expands: claude / gemini-api / detector-spawned /
  (later fable-vs-opus as separate generator_ids — let Brier answer the
  2× question empirically).
- The atlas converts anomalies into named constants; success = residual
  shrinks WHILE recall against confirmed events holds (the overfit
  guard — shrinkage without recall is going blind, not learning).
- Paper execution (ADR-029 Shadow Book) only under governor.approve(),
  scored on its own metrics, paper→live never automatic, never
  self-proposed.
- The savant claim stays a HYPOTHESIS the ledger falsifies continuously.
  30 days of honest "no edge" is a success. Flattering numbers on a
  contaminated ledger are the only true failure.

---

## PART 3 — STANDING LAWS (compressed; full text in CONSTITUTION.md)

1. Four lanes, per FIELD not per person: instrument=measured numbers;
   generator=belief numbers (relative + distribution); oracle=regime;
   reconcile=grades. No station expands its own authority.
2. ADR-030 forever: no distribution committed after its outcome is
   observable ever scores. Intake stamps time; generators never do.
3. Falsifiable AND repeatable: pre-register, kill-thresholds, snapshot
   raw inputs, deterministic analysis, fixed seeds, byte-identical
   re-runs. A model may PROPOSE a rule; it may never BE the rule.
4. Two Claudes agreeing is one source. Load-bearing calls need a
   measured test or Tyr's eyes.
5. Never fabricate authority: referenced-but-absent docs stop the build
   (the ADR-030 refusal is the standard). Retract in plain words when
   evidence turns (the AMKR withdrawal is the standard).
6. Keys: never in chat, never in commits, rotate anything exposed,
   booleans only in output. The repo is PUBLIC.
7. Findings that live only in a conversation do not exist. Repo or it
   didn't happen.

---

## PART 4 — PARALLELISM

MECHANISMS
- Task fan-out: multiple Task calls in ONE message run in parallel,
  each with its own context window, returning summaries only.
- Custom agents: .claude/agents/*.md with scoped prompts and tools.
  Define two for this repo: `bar-puller` (Robinhood MCP + read only,
  no writes) and `verifier` (read-only, adversarial, checks claims
  against the instrument).
- Git worktrees: `git worktree add ../cosmos-<branch> <branch>` →
  a second working tree of the same repo, separate session, zero
  collision. Use when two phases must progress at once.
- /goal for objectives that persist until met; /advisor for an Opus
  review pass before load-bearing design.

WHERE IT APPLIES (decided, not ad hoc)
  Phase 1 heartbeat ............ NO  (one small file)
  Phase 2 keys ................. NO  (bottleneck is design, not calls)
  Phase 3 weight chain ......... NO  (integrity-critical, ordered)
  Phase 4 books ................ LIGHT (parallel scanner queries)
  Phase 5 forensic study ....... YES/MASSIVE (one agent per cohort)
  Phase 6 feeds ................ YES (one agent per provider)
  Phase 7 detection ............ sweep YES / design NO
  Phase 8 backfill ............. YES

STANDING RULE: fan out where it is safe and additive; gate
money-adjacent and integrity-critical code personally. Parallelising
careful design yields six copies of the same mistake, faster.

OWED, and a worktree is how you settle it: the ADR-032 hook LIVE-FIRE.
The SHA-256 and guard logic are verified headless, but headless pytest
cannot exercise the Claude runtime. Spin a throwaway worktree, run a
real session, attempt an edit to hermes/governor.py, confirm the hook
BLOCKS. Positive and negative test both.
