# HERMES CANON v1.2 — EVIDENCE-AUDITED
**Wolf Pack single source of truth. Supersedes all prior spec versions and AI-generated
summaries. Date: 2026-07-04. Authors: Tyr (Alex Payne) + Fenrir (Claude/Fable 5).**

## WHY THIS VERSION EXISTS

Documents circulating between pack AIs accumulated **validation inflation** — claims
drifting from "idea" to "proven" with each retelling. Tyr called it. This version purges
it. From now on, every factual claim in canon carries one of four tags, and any AI
receiving this document must preserve the tags:

- **[MEASURED]** — we ran it ourselves; n and method stated. Trust it.
- **[LITERATURE]** — sourced from external research; needs citation before load-bearing use.
- **[HYPOTHESIS]** — our idea, untested. The whole point of Hermes is to test these.
- **[DELETED]** — was circulating as fact; is not. Do not restate as fact ever again.

**Standing rule: no number enters canon without a provenance tag. An AI that states an
untagged number as fact is malfunctioning and should be corrected.**

---

## 1. WHAT IS ACTUALLY PROVEN [MEASURED]

Phase 1 code (ledger.py, reconcile.py, governor.py) ran end-to-end 2026-07-04 in a live
container against real Yahoo daily closes. 60 backdated predictions resolved on
BBAI/KTOS/INSW/FRO/NAT/VG. What this run legitimately established:

1. **The plumbing works.** Predictions log, mature, resolve against real prices; EWMA
   weights update; every change writes a reason row; the governor enforces caps
   deterministically. [MEASURED]
2. **Calibration scoring detects overconfidence.** Two signals with IDENTICAL picks,
   claiming p=0.60 vs p=0.80, separated on avg Brier: 0.313 vs 0.500. [MEASURED —
   note: this proves the Brier math discriminates stated confidence quality. It says
   NOTHING about pick quality, because the picks were identical by design.]
3. **A first rough base-rate estimate:** naive "+5% within 14d" long on these 6 tickers
   over Apr–Jun 2026 hit ~30% (9/30 unique pick-windows). [MEASURED, WEAK — small n,
   overlapping windows, hand-picked tickers with selection bias. Treat as placeholder
   bar, recompute on the full 153-ticker universe before treating as real.]

**What Phase 1 did NOT prove:** that any signal has skill. No real signal has ever been
run through this system. The system has zero EARNED signals. Hermes today is an infant
with working organs and no knowledge. That is the honest state.

## 2. WHAT COMES FROM OUTSIDE RESEARCH [LITERATURE]

These informed the design and are believed credible, but are not our measurements.
Before any becomes load-bearing (e.g., sets a threshold), pull and cite the source:

- Insider cluster buys (opportunistic, multiple executives, short window) show
  post-filing abnormal returns. [LITERATURE — the specific "~82 bps/month" figure
  circulating in our docs needs its citation re-verified before reuse.]
- Pure price-pattern/TA signals decay toward zero edge after publication; alpha decays
  post-publication generally (McLean & Pontiff). [LITERATURE]
- Risk-of-ruin / fractional Kelly: overbetting destroys growth even with real edge.
  [LITERATURE — mathematically standard, safe to rely on.]
- Triple-barrier outcome labeling beats fixed-horizon hit tests (López de Prado).
  [LITERATURE — adopt in Phase 2 reconcile upgrade.]
- 13F holdings arrive up to 45 days stale; using them as origination buys an echo.
  [LITERATURE + one consistent personal observation (Under Armour trade). Confirmation-
  tier only.]
- Volatility clusters in time; moves concentrate around known catalysts. [LITERATURE]

## 3. WHAT WE BELIEVE AND HAVE NOT TESTED [HYPOTHESIS]

This is the actual research agenda. Stating any of these as proven is the exact
inflation this document kills. Hermes exists to grade them:

- H1: Causal/document-derived signals (filings, transcripts, forced-flow chains)
  outperform price-derived signals at multi-week horizons in our universe.
- H2: Stock-vs-sector-ETF divergence (name moves, ETF doesn't) marks early idiosyncratic
  theses and is a usable signal either direction.
- H3: Convergence of multiple independent weak signals outperforms any single signal.
- H4: Weights accrued to LINES OF REASONING (bottleneck-physics vs narrative-momentum vs
  insider-following) will separate — some thought-families pay, others don't.
- H5: "Thesis still running vs completed" (check-writing growth) beats "already ran"
  price heuristics for hold/exit decisions.
- H6: Regime context (sector rotation state) changes which signals work; per-regime
  scoring will reveal this.
- MU $90→$757 and the liquid-cooling chain are **motivating case studies** — n=small,
  selected after the fact. They inspire H1/H5; they do not prove them. [HYPOTHESIS
  SUPPORT, NOT VALIDATION]

## 4. DELETED FROM CANON [DELETED — never restate as fact]

- "Bottleneck-physics claims on pre-narrative names hit at 55%+." Invented by an AI
  summarizer. Never measured by anyone.
- "Narrative-momentum chasing hits at 25%." Same. Invented.
- "insider_cluster_toy beat coinflip_toy" as evidence of signal skill. Wrong reading:
  identical picks, only confidence differed. Calibration demo only.
- Any sentence of the form "we have validated X" where X is not in Section 1.
- Prior Wolf Pack pattern stats (P1/P2/P3/P6 precisions, FLOAT_CHURN 82%, magic-signal
  28%, wounded-prey AUC 0.50, etc.) are **quarantined pending re-verification**: they
  came from earlier research sessions whose methods/data are not reproducible inside
  Hermes today. They remain useful as candidate signals and kill-list lessons
  [HYPOTHESIS / historical notes], but no numeric claim from that era is load-bearing
  until re-measured through the Hermes ledger itself.

## 5. THE IDEAS (what to actually tell a new AI — this is the real payload)

Hermes is a persistent thought factory with a scorekeeper attached. Stateless LLMs
think (read documents, extract claims, generate falsifiable hypotheses); a permanent
SQLite ledger remembers, grades every matured prediction against reality, and updates
trust deterministically (EWMA, min-sample guards, full reason logging). Sizing is
governed by hard rules that cannot see confidence. Nothing resets. The human makes all
execution decisions. Doctrine: markets are emotional crowds; no theory is 100%; hold
many partial truths weighted by graded track record; causal signals over price-derived;
documents are the data at long horizons, price only measures crowd arrival;
comprehension edge, not latency edge; attention is the scarce resource — the system
screens breadth so the human spends judgment on the surfaced few; honest negative
results are kept forever. Growth is staged (infant→savant) with gates: signals earn
trust only through resolved outcomes (n≥10 provisional floor, 30–50 before anything
affects money); universe expands only as fast as reconciliation can grade it.

## 6. IMMEDIATE NEXT ACTIONS

1. Wire the FIRST REAL SIGNAL (insider cluster via Form 4) to ledger.log_prediction —
   paper only. Until then Hermes knows nothing and that's fine; babies know nothing.
2. Recompute the base rate properly: all 153 tickers, non-overlapping windows, both
   directions. Replace the placeholder ~30%.
3. Phase 1.1 code hygiene (from external review, accepted): rename price fetcher
   honestly (yahoo_closes), validate confidence∈[0,1] and direction at log time, dedupe
   seed reruns, log bankroll+open-count context in sizing_log, cache price pulls, track
   fetch failures in a table, add explicit baseline row to every report.
4. Phase 2 schema adds (accepted as design, all outputs [HYPOTHESIS] until graded):
   claims table, hypotheses table, reasoning_style + thesis_source + movement_type +
   etf_confirmed + exit_reason fields.
5. Gemini onboarding: hand it THIS file only. Its first mission: small-cap earnings
   transcript coverage for the $5–$200 universe (the open Stage 3 data gap), and
   re-sourcing the insider-cluster literature citation.

## 7. PACK SEATS (v1.2)

Tyr: direction, final reads, all execution. Fenrir (Claude/Fable 5): synthesis,
architecture, honesty enforcement, nightly cognition (future). Claude Code: builds from
this document. Gemini (Pro): deep research missions, NotebookLM pack library
(grounded-only archivist), long-context corpus reasoning, Flash-tier extraction
candidate. DeepSeek: red team. Convergence protocol unchanged: ≥2 independent AIs →
candidate for canon, but **now requires provenance tags to merge.**

LLHR. Results are the results. Real science. No serving any priesthood — including
our own past claims.
