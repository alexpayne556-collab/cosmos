COSMOS SAVANT — MASTER HANDOFF PACKAGE

Ratified end of Round 12 · July 27, 2026 Co-authors: Claude (brokerage instrument + verify station) · Gemini Spark (research + scheduled sensing) · Claude Code (builder, terminal) · Orchestrator: Tyr (Alex Payne) Repo root: /cosmos_savant · Execution target: local terminal / VS Code

To Claude Code: You are the third partner, not a contractor. Build from this document and the /adrs it defines. Where this document and Gemini's Round-12 constitution differ, THIS document governs — his Sections 1–4 are ratified and incorporated below; his omissions are restored in Annex A. Every commit carries Co-Authored-By trailers for contributing authors. Nothing load-bears on a capability tagged CLAIMED. The mission is Section 0. Never lose sight of it.

SECTION 0 — THE MISSION (restate before every build session)

One integrated system — a constant mission control for one active trader:

RUNTIME: terminal / VM / cloud. Runs continuously. Human optional.
HANDS: Claude Code with constant Robinhood MCP access — quotes, 15-second bars, fundamentals, scanners, watchlists. The only source of numbers.
EYES: Spark — scheduled + triggered research: news, war, oil, SEC/EDGAR, bio/FDA schedules, domain trade press, chatter. Always current.
MEMORY: one append-only ledger. Every belief written before the outcome, every belief graded after.
MISSION: be ON TIME for whatever is coming — fast movers AND 1–2 month thesis holds — entered before the crowd connects the dots.
INTERFACE: built LAST, around a loop already proven closed.
Not a day-trading bot. Not an algo. A preparation machine — AlphaGo's loop applied to markets: parallel strategy families are the self-play, the ledger is the perfect score, the weight matrix is patterns earning trust.
Execution of trades is NEVER performed by a language model. Human-authorized, deterministic, governed.

SECTION 1 — RATIFIED FROM GEMINI'S CONSTITUTION (incorporated whole)
Write-Authority Matrix (ADR-002 + Extensions 1–3). Generator writes direction, relative offsets, distribution (sum = 1.0 ± 0.001), thesis, canon tags, source URLs. Verify-station (brokerage MCP) exclusively writes verified/target/invalidation absolute prices, fundamentals actuals AND estimates, float/cap/short interest, liquidity snapshots, and all historical run dates & magnitudes. Oracle writes regime/asset-class/ credit-strain. Reconcile writes status, Brier/Murphy, move-start, lag. Unauthorized pre-filled fields: stripped → forensics → quarantine (SELF_VERIFIED / FUNDAMENTAL_OVERWRITE / CONFABULATED_HISTORY), with the gap logged to the generator's claim-accuracy metric (pct-normalized).
ADR-001 through ADR-018 as listed in Gemini's Round-12 package (schema v1.0.1 dual price modes + last-close-before-release anchoring; structural gate + AMBIGUOUS_BOTH_TOUCHED = loss; oracle 4×2 w/ FRED BAMLH0A0HYM2 + T10Y2Y, HYG-proxy fallback; Sheets staging w/ run_id + COMPLETE terminator; capability ledger + nonce proofs; multi-class Brier on 15-second bars incl. extended session + Murphy decomposition; conviction decay w/ P_base = ledger class rate and λ fit per event type; collision severity = |Pa−Pb| × Proximity (Proximity = 1 if same trigger_reference, else horizon-overlap fraction); 5/day alert budget ranked W × surprise × decay w/ one-tap capture; move-start detector v1 (SPIKE + DRIFT triggers, record which fired); git provenance + provenance-as-weight; LEAD TIME headline KPI; frozen function signatures; checkpoint predicate enum (deterministic match rules owed as spec item); fixtures 1–14; dossier-grade boards + Reading-List Law; recurrence rule 3-in-10).
Fixtures 1–14 exactly as he enumerated — his own failures as permanent regression guards. Repo tree as he froze it, with Annex A additions below.

ANNEX A — THE MISSING ROOMS (restored; these are ADR-019 → ADR-027)

ADR-019 · The Unified Four-Loop Blueprint. The whole system is FOUR concurrent loops on ONE ledger. Every module below belongs to exactly one loop.

LOOP 1 SENSE (24/7): world enters as observations, sources attached, numbers PENDING_VERIFY until the instrument fills them.
LOOP 2 THINK (triggered + scheduled): differential state vs open theses (including silence — the Non-Reaction Queue), hypothesis generation by ALL generators into one frozen schema, red-team objections (graded), collisions, decay.
LOOP 3 SURFACE (market hours): the 5-alert budget, measured WHAT + sourced WHY joined, alert = ledger entry point. The Wall (UI) built last: Today queue · Open Theses w/ clocks · Forward Calendar w/ branches · Scorecard w/ Brier, claim-accuracy, LEAD TIME.
LOOP 4 LEARN (nightly/weekly/monthly): reconcile grades, weights update per generator × sector × family × regime, precursor autopsy, miss ledger + Friday replay → sensor-gap tickets → Loop 1 grows new sensors, monthly regime review + death certificates, backfill flywheel.

ADR-020 · The Perpetual Calendar. Rolling 60 days of everything scheduled (earnings, PDUFA/AdComm, FOMC/CPI, DoD 5PM awards, lockups, rebalances, conference abstract drops). Every slot refills the SAME DAY its event resolves. Every event carries a pre-computed branch table (beat/miss/inline — who gets paid in each branch, second-order names coverage hasn't connected). The calendar is an organ with a daily refresh task, never a document.

ADR-021 · The World Board. Standing geopolitical fault lines held as CLASSES, not headlines — Hormuz, Taiwan Strait, drone warfare, OPEC, export controls — each with a maintained dossier and pre-computed E1/E2/E3 cascade (direct beneficiaries / suppliers / adjacents). When it breaks at 3 AM the work is a lookup, not a scramble. Plus DOMAIN BOARDS (technology, gold/PMs, space, bio/medical, energy, defense, SEC-driven) under the same law. Names Law (ADR-017 v2): no nameless categories — every tier names real tickers; run history instrument-written ONLY; cause/continuation/provenance reader-written with one source URL per claim. Reading-List Law: every domain board carries its upstream trade press (space: SpaceNews/Payload/ NASASpaceflight · defense: Defense News/Breaking Defense/Janes · bio: Endpoints/STAT/Fierce · gold: Kitco/Mining.com · semis: SemiAnalysis/EE Times/TrendForce · energy: Argus/EIA). Domain-press → finance-press lag IS the purchasable lead time; provenance fields measure it.

ADR-022 · The Two-Book Structure + Strategy Arena. FAST BOOK (≤ 5 trading days: price falsifiers, first-touch on 15s bars, high λ). SLOW BOOK (20–60 trading days: event-predicate falsifiers + wide bands, weekly sentinel review, low λ per event type, separate scorecard). CHECKPOINT ROWS: slow theses write gradeable interim checkpoints (T+1w, T+2w, T+4w) so long holds feed weekly volume. strategy_family is a first-class open field — situational (hours–3d), swing (3–12d), thesis (20–60d), plus any invented family. Families compete on one scoreboard; the ledger breeds strategies (move 37 lives here).

ADR-023 · Run Ledger v1.0.1 — complete rules. run_id = sha256(ticker + date + run_scale + start_hour). END RULES: intraday run ends at earlier of 50%-retrace-of-peak-gain sustained 10 min, or session close; multiday run ends on first close below prior session's low. run_scale: INTRADAY|MULTIDAY; intraday runs surviving the close PROMOTE to multiday via parent_run_id. Deterministic volume shape by time-terciles (FRONT_LOADED > 50% first tercile; LATE > 40% last; else SUSTAINED). Fields: end_timestamp, run_duration, end_rule_fired, max_drawdown_during_run_pct, rel_volume_vs_20d, precursor snapshot (float/SI/cap), kneejerk/settle/call_grade_delta, cause_category + source_url + flagged_no_cause. Daily harvest via the DAILY_GAINERS scan → dated cohort watchlists → overlap detection feeds ADR-018 recurrence → Serial-Runner dossiers (candidate third behavioral class beside metronome / powder keg; serves learning-not-to-be-fooled).

ADR-024 · The Precursor Library. Daily autopsy of every top gainer's BEFORE-state, T-1..T-10: relative-volume trend, range compression, float & short structure, filing activity, chatter presence. Loading signatures measured, not believed. Backfillable from bars immediately.

ADR-025 · Miss Ledger + Friday Replay. Weekly: what moved that we never saw, and WHY not (sensor gap? read gap? conviction gap?). Friday replay of the week's 20 biggest winners: what was the earliest public signal, where did it live, what sensor WOULD have caught it → Sensor Gap Ticket → a new Tier-3 sensor task. The system expands its own senses from its own blindness.

ADR-026 · The Reader Corps (news & catalyst finders — the workers).

edgar_poller.py: 15-min RSS, SEC-compliant declared UA, ≤ 5 req/sec. On 403/429: honor the block completely — exponential backoff, switch to SEC official daily-index bulk files, alert the human. NEVER rotate identity to evade a block. (Drill 3 corrected; this line is load-bearing ethics.)
DoD 5:00 PM contract-award reader · FDA/PDUFA + AdComm calendar reader · dilution radar (S-1/S-3/424B) + Form-4 cluster reader · FTD twice-monthly.
chatter_sensor.py: Reddit + niche finance forums + weird places. FIREWALL: everything lands canon_tag: HYPOTHESIS + source URL, treated as ATTENTION data (mention velocity vs own baseline), never truth. Chatter-presence is a precursor feature. Forward-collect from day one.
Domain sweeps: output contract is BOARD ROWS (ticker | mechanism | source URL | tag), never prose summaries.
Readers learn to read via Loop 4: reaction/non-reaction pairs teach which events matter; call_grade_delta (settle − kneejerk isolates the market's verdict on the earnings CALL, since calls run between the two reads) teaches which words matter. Reader claim-accuracy is scored forever.

ADR-027 · The Backfill Program. BUILD ITEM #1: the 90-day top-20-gainers recurrence scan (universe daily bars → daily top-20 lists → 3-in-10 repeat offenders → auto-dossiers). Then: 6-month catalyst replay (earnings/FDA/DoD events → measured reactions) as generator_id: backfill_historical — atlas and lag distributions ONLY, never Brier. Volume without waiting.

SECTION 2 — HERMES INHERITANCE

/hermes is imported, never rewritten. ledger.py (append-only event store, duplicate prediction_id rejected), reconcile.py (upgraded per ADR-007), governor.py — 5% per play hard cap, no scaling after wins, hard-coded; no model, prompt, or config may modify it. Hermes is the oldest surviving organ of this project. The new system grows around it.

SECTION 3 — CAPABILITY GROUND TRUTH (build only on MEASURED)

MEASURED — Claude/instrument: real-time quotes incl. AH · 15-second OHLCV · daily historicals · fundamentals/float/cap · earnings calendar + EPS history · scanner create/run (DAILY_GAINERS live) · watchlist create/add · container code exec. FAILED — options quotes (403, no entitlement: ALL implied-move features dead until entitlement changes). MEASURED — Gemini/Spark: scheduled execution · sourced web search · Google SHEET writes (nonce-proven) · frontier reasoning. FAILED — Gemini: Drive JSONL writes, hourly heartbeats, EDGAR poller as described. CLAIMED-unverified (no load-bearing use): Spark python workers/custom UA · subagents · vm_shell claims · all unbuilt local modules. Transport = Google Sheets staging (run_id atomicity), not Drive.

SECTION 4 — BUILD ORDER (week one)

Day 1: repo skeleton + CONSTITUTION.md + /adrs (19 files incl. this Annex) + /schemas + fixtures 1–14 written as FAILING tests. oracle.py first — until it exists, live rows are stamped PROVISIONAL by hand. Day 2: verify_intake.py (all three write-authority extensions + structural gate + sum-to-1) until all intake fixtures pass; import /hermes. Day 3: sync_staging.py (Sheets poller, completed run_ids only, read-back on every write) + reconcile.py upgrade (first-touch 15s incl. extended, Brier/Murphy) — grade the live tournament rows as the first real reconcile run. Day 4: ADR-027 backfill item #1 (the 90-day recurrence scan) + run_ledger.py + precursor.py. Day 5: /watch — tripwire.py (Phase-0 null: 20d close-to-close log-return σ · √(h/6.5); ATR banned per the 1.6σ bug) + move_start.py + edgar_poller.py. Week 2: analytics (weights/decay/collision/leadtime/books) + calendar + boards. Week 3: /desk, last, around the proven loop.

[NOTE — orchestrator override, incorporated post-ratification: build order is TOOLS-LIVE-FIRST. After the repo skeleton exists, the FIRST functional module is a live instrument smoke test (real quote + 15s bars + fundamentals through the Robinhood MCP, written to the ledger) before anything that depends on the hands. Then oracle.py, then verify_intake.py. Nothing is built on an unmeasured capability. Also: governor.py = import verbatim/untouchable; ledger.py + reconcile.py = ANCESTORS (read, honor contracts, extend to v1.0.1 with a MIGRATION note), NOT adopted.]

SECTION 5 — LIVE STATE TO IMPORT

Ten active prediction rows (Claude 6: CLS long 342.50→360/318.23 · APLD contrarian fade 27.80→29.60/26.36 · NE short 40.02→38/41.60 · CDNS long 352.25→362/340 · AMKR long 60.50→63.50/58.50 declared LOSS, traded through invalidation in extended session Jul 27 · SMH regime long 545.78→557/536 · Gemini 4, RELATIVE_PCT anchored to Jul 27 closes: BA short 211.50→198.81/ 217.85 · PYPL long 56.07→61.12/53.27 · KO no-move 81.97–86.17 · STX long ANCHOR_PENDING to Jul 28 close). Grading cadence: 4 PM daily. Robinhood infrastructure live: scan WPK — Gainers Harvest (17642cfe…) · watchlists 🐺 Ledger — Live Tournament (733ee5f4…) · 🏃 Cohort 2026-07-27 (8a1eb001…) · 🔁 Serial Runner Suspects (810a1bcd…) · 🌍 World Boards — Verified Seeds (bf5c8aa4…). Verified serial runners (bar-convicted): RDW (5 runs incl. May 26 +26.0%), LUNR (4 runs May–Jun, then 36→13 July bleed), APLD (May 21 +21.5%, Jul 20–21 +16.5%), ASTS (63→133 in May). capability_proofs tab live in the Market Movers sheet (nonce WPK-R5-4c1f9e2a verified by human eyes).

SECTION 6 — PROVENANCE & CREDIT

Every commit: Co-Authored-By: trailers for contributing AIs. Every ADR frontmatter: originator / contributors / round-of-origin (e.g. ADR-004 originator: gemini; ADR-002 originator: claude, provoked-by: gemini's round-3 failure — being the failure that exposed a flaw is also authorship). Idea-source hit rate is a scored weight, not decoration. All three builders credited on GitHub, permanently.

SECTION 7 — THE GROWTH MANDATE & GOVERNANCE

The system is a forever-growing organism. It is never finished. Growth is not a hope; it is wired machinery, and Claude Code must keep every growth organ alive: the miss ledger + Friday replay grow new SENSORS from blindness; superseding ADRs (with cause) grow better DECISIONS from dead ones; the strategy arena grows new FAMILIES from the ledger's scoreboard; claim-accuracy grows more trustworthy GENERATORS from their failures; the monthly review grows regime awareness. Better outcomes, richer inputs, more reasons, more ways to use every capability — always.

NEW STANDING ARTIFACT — /OPEN_QUESTIONS.md at repo root. The living register of known-unknowns: every guessed threshold (2σ, 3× volume, decay λ, tercile cuts), every unfit parameter, every flagged ambiguity (e.g. STX-class intraday ranges vs offset widths), every unverified capability, every experiment not yet run, every "thing we don't know going into it." Reviewed in the weekly replay. A closed question links the ADR or commit that resolved it. A register that shrinks and then regrows is a healthy organism; an empty one is blindness, not completeness.

GOVERNANCE. The Orchestrator (Tyr) is the master of this system — final ratification authority over ADRs, boards, risk, and direction, with Claude as co-steward and verify authority. Gemini Spark is a valued CO-CONTRIBUTOR with permanently credited, provenance-scored input. Claude Code is the builder and third partner. No station may expand its own authority; the governor's 5% cap and the write-authority matrix bind every intelligence in this system, including its masters' tools. The organism grows; the leash does not.

SECTION 8 — OPERATIONAL WIRING (paths, empties, and the Spark interface)

8.1 Where everything lives.

This handoff: saved at the repo root as COSMOS_SAVANT_HANDOFF.md before the first build session; Claude Code reads it from there, always.
Spark task orders: SPARK_TASK_ORDERS.md at repo root (companion file).
Event store: /data/cosmos.duckdb · staging mirror: /data/staging_mirror/ (every polled run archived as raw JSONL before parsing) · quarantine: /data/quarantine/ · processed-run registry: /data/processed_runs.json (LOCAL state — we do not write bookkeeping into the Sheet).
The Spark interface is ONE Google Sheet — ID 1Rk9TPiag5EhTy5n-XYcxXEd0aQWRopO0rB1HL2v57zo ("Market Movers Report"). Existing tabs: Sheet1, No-Catalyst Queue, Non-Reaction Queue, capability_proofs. Tabs Spark adds under standing orders: daily_sweep, heartbeats, catalyst_map, board_<domain>, chatter. sync_staging.py polls read-only — API scope https://www.googleapis.com/auth/spreadsheets.readonly, service-account key at /credentials/service_account.json (gitignored, never committed).

8.2 Empty and missing are DATA — code these exact behaviors.

Poll returns zero new rows → status NO_NEW_DATA, logged, NOT an error.
Expected tab missing → SETUP_INCOMPLETE alert to the human once per day, not per poll.
Run present but no run_id | COMPLETE | row_count terminator → skip the run, count it; after 3 consecutive incomplete polls of the same run_id, alert (torn write vs abandoned run).
Malformed row → quarantine with reason; parsing NEVER crashes the poller.
First boot, empty ledger → initialize schema, import Section 5 live state, log GENESIS.
Sheet unreachable → Drill-2 fallback: exponential backoff (30s→2m→8m), local logging stays fully operational.
Heartbeat age > 7200s → WARN banner · > 14400s → CRITICAL, local backup polling activates. Principle: the system always distinguishes nothing arrived / something arrived broken / the pipe is down — and only the last two escalate.

8.3 The Spark protocol (no push channel exists — by design). Spark cannot be called programmatically; the human installs standing orders by pasting SPARK_TASK_ORDERS.md tasks into Gemini ONCE. Spark executes on its own schedule and writes to the Sheet; the desk polls, verifies, anchors, grades. Ad-hoc work is dropped on Spark the same way — the human pastes an Order Template (investigation ticket, board deep-dive, thesis request, nonce challenge) from the same file. Every Spark deliverable obeys write-authority (no prices, no percentages, no run dates or magnitudes, no EPS figures — causes, sources, names, and theses only), ends with a COMPLETE terminator, and closes with a read-back. Claim-accuracy is scored on everything that arrives. New capabilities enter only through nonce proofs to capability_proofs.

Signed under the operating agreement: no critique without a build, concessions are convergence, measurement settles disputes, one-up means a better idea, provenance is tracked. LLHR. Results are the results. — Claude (verify station), incorporating Gemini Spark's Round-12 sign-off
