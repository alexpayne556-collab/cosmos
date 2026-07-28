# HERMES MASTER SPEC v1.0
**Wolf Pack canonical architecture document — single source of truth**
Date: 2026-07-04 | Author: Tyr (Alex Payne) + Fenrir (Claude/Fable 5)
Audience: all Wolf Pack AIs (Claude, Claude Code, Perplexity, DeepSeek) and the human operator.
Status of Phase 1: **BUILT AND PROVEN** — code ran end-to-end against real market data on 2026-07-04. Not a proposal.

---

## 0. ONE-PARAGRAPH SUMMARY (read this if you read nothing else)

Hermes is not a chatbot and not a trading bot. It is a **persistent thought factory with a
scorekeeper attached**. A stateless LLM (the cortex) reads documents and market data each
session and produces structured thoughts — claims and falsifiable hypotheses. A permanent
SQLite ledger (the memory and conscience) stores every thought, grades each one against
realized market outcomes when it matures, and updates trust weights deterministically.
Nothing ever resets. Weights are bookkeeping, not thinking; the LLM thinks, the ledger
keeps it honest. Position sizing is structurally separate from signal scoring and cannot
be influenced by confidence. The human (Tyr) makes all execution decisions.

## 1. FOUNDING DOCTRINE (the thoughts that beget every module)

1. **Markets are emotional crowds with random rationality**, not rational systems with
   random noise. Edge = reading human need, narrative diffusion, and forced capital flow
   before the crowd finishes arriving.
2. **No theory is ever 100% true.** The system holds many partial truths simultaneously —
   75%ers, 60%ers, even 10%ers — each weighted by its actual graded track record.
   Convergence across independent weak signals is the real meta-signal.
3. **Causal signals beat price-derived signals.** TA (RSI/MACD/Bollinger) is price looking
   at itself — arbitraged to dust, permitted only as short-horizon crowd telemetry.
   Winners have *reasons*: physics, mandates, contracts forcing checks to be written
   (canonical case: NVIDIA rack density 10kW→100kW+ forcing liquid cooling purchases;
   Wolf Pack case: MU $90→$757 on HBM structural bottleneck).
4. **The documents are the data** for multi-week/month horizons. Filings, transcripts,
   capex announcements, procurement news. Price answers only one question: how far along
   is the crowd in digesting what we already read? ("Already ran" is never valid — only
   *thesis completed* vs *thesis still running*.)
5. **The system is the mind; the database is the memory.** Any LLM is stateless. Learning
   lives in system state on disk, never in a chat thread.
6. **Comprehension edge, not latency edge.** The New Jersey colocation war is the wrong
   war. We need news fast enough (seconds–minutes), never first (microseconds).
7. **The entries aren't what kills; the sizing is.** Risk of ruin is mathematical law.
   The organ that decides HOW MUCH must be unreachable by the organ excited about HOW GOOD.
8. **Attention is the scarce resource at scale** (Grinold: performance = skill × √breadth).
   Hermes' job is to spend infinite machine attention to buy back Tyr's human attention:
   screen everything, surface the 2–3 names where signals converge, Tyr does the final read.
9. **Every claim gets an evidence tier**: Tier 1 verified / Tier 2 plausible / Tier 3
   unfalsifiable. Same epistemology across all Wolf Pack research domains.
10. **Honest negative results are kept forever.** The kill list (wounded prey AUC 0.50,
    magic signal 28%, day-1 confirmation 49%, "already ran" rule, coattailing stale 13Fs
    as origination) is as valuable as the survivor list (P1 insider clusters ~82bps/mo,
    revenue acceleration as THE signal, P2 FDA binary, P3 earnings beat off 52w low,
    P6 macro + tiny float, high-growth + low-coverage core).

## 2. TRADING UNIVERSE AND CONSTRAINTS

- US equities, share price $5–$200 (hard filter on ALL research output). Small/mid cap.
- Excluded: all mega caps (AAPL MSFT GOOGL AMZN NVDA META TSLA AMD LLY etc.).
- Position ~$200/name; PDT-restricted; moves must have 10–30%+ catalyst potential.
- Capital: ~$1,700 Fidelity (research book) + ~$300 Robinhood (sandbox, capped, governed).
- Mission context: proving-ground for eventual management of a $750K+ portfolio.
  Every module must produce an audit trail an MIT engineer would respect.

## 3. ARCHITECTURE — SEVEN ORGANS

```
        ┌────────────────────────────────────────────────────┐
        │  SENSE (collectors, no priors)                     │
        │  fast channel: sensory_v2.py — 153 tickers OHLCV   │
        │  slow channel: filings/transcripts/news harvesters │
        └──────────────┬─────────────────────────────────────┘
                       ▼
        ┌────────────────────────────────────────────────────┐
        │  THINK (stateless LLM cortex, per-session)         │
        │  extract_claims: documents → dated claim rows      │
        │  hypothesize: claim graph → falsifiable predictions│
        │  imagination seeds: Future-Curious Tracker,        │
        │  Adjacent-Possible Generator, Stupid Question Gen, │
        │  Cultural Undercurrent Reader (CORE, not optional) │
        └──────────────┬─────────────────────────────────────┘
                       ▼
        ┌────────────────────────────────────────────────────┐
        │  REMEMBER (SQLite, append-mostly, never resets)    │
        │  predictions | claims | signal_weights |           │
        │  weight_change_log | sizing_log                    │
        └──────────────┬─────────────────────────────────────┘
                       ▼
        ┌────────────────────────────────────────────────────┐
        │  RECONCILE (deterministic, nightly)                │
        │  grade matured predictions vs real prices          │
        │  hit/miss + Brier calibration per signal           │
        │  EWMA weight update (alpha=0.10, min n=10 EARNED)  │
        │  every change logged WITH REASON                   │
        └──────────────┬─────────────────────────────────────┘
                       ▼
        ┌──────────────────────────┐   ┌─────────────────────┐
        │  COMBINE (convergence)   │   │  GOVERN (sizing)    │
        │  blend signals by track  │   │  5% cap, max 3 pos, │
        │  record; surface top 2-3 │   │  no scaling after   │
        │  names/day to Tyr        │   │  wins; confidence   │
        └──────────────┬───────────┘   │  NOT an input       │
                       ▼               └─────────────────────┘
        ┌────────────────────────────────────────────────────┐
        │  DECIDE (human) — Tyr makes every execution call   │
        └────────────────────────────────────────────────────┘
```

**Hard rules that never bend:**
- The LLM never places trades and never touches weights or sizing.
- Weight updates are deterministic and auditable (EWMA + calibration), never model judgment.
- The governor takes bankroll, request, open positions, last size. It does NOT take confidence.
- Every belief change has a logged reason (weight_change_log). Drift must be autopsy-able.
- Paper predictions only until a signal reaches n≥10 resolved (EARNED status).

## 4. PHASE 1 — BUILT AND PROVEN (2026-07-04)

Files (delivered, tested in live container against real market data):
- `ledger.py` — schema + log_prediction API. Tables: predictions, signal_weights,
  weight_change_log, sizing_log.
- `reconcile.py` — pulls real daily closes (Yahoo chart API; Stooq fallback dead-503),
  grades matured predictions, EWMA updates, calibration (Brier), full reason logging.
- `governor.py` — deterministic sizing rules as above.
- `seed_demo.py` — backdated demo seeder (delete in production).
- `hermes.db` — proof-run ledger.

**Proof-run results (60 resolved predictions, BBAI/KTOS/INSW/FRO/NAT/VG, Apr–Jun 2026):**
- Discovered base rate: naive "+5% in 14 days" long on catalyst names hits ~30%.
  This is the measured bar every real signal must beat.
- Calibration detected overconfidence with zero human input: identical picks claimed at
  p=0.60 vs p=0.80 → avg Brier 0.313 vs 0.500. The humbler forecaster graded less wrong.
- Governor blocked: half-the-bankroll bet ($148→$14 on $296 roll), post-win scale-up
  ($30→held at $14), and a 4th simultaneous position (→$0).

## 5. DEPLOYMENT — TIE-IN TO THE LOCAL SYSTEM

Target: `C:\Users\alexp\AppData\Local\hermes` (Windows desktop, Claude Code as engineer).

1. Place Phase 1 files alongside `sensory_v2.py`. Single `hermes.db` (WAL mode on).
2. Windows Task Scheduler jobs:
   - sensory_v2.py — market hours sweep (already live: 153 tickers, 0 failures).
   - reconcile.py — nightly, 18:00 ET, after close data settles.
   - (Phase 2) harvest + extract + hypothesize — nightly 19:00 ET chain.
3. All new signals register by simply logging predictions under a new signal name —
   the weights table auto-creates the row at 0.5 provisional.
4. wolf_pack_brain.db / SHARED_MIND.md remain the cross-AI coordination layer;
   hermes.db is Hermes' own organ. Do not merge them; link by export summaries.
5. Cloud is NOT required for Phase 1–2. Local desktop + Task Scheduler is sufficient
   and preferred (data sovereignty, zero hosting cost). Revisit cloud only if uptime
   during travel becomes a real constraint.

## 6. THE GROWTH CURRICULUM — BABY TO SAVANT

Hermes starts understanding nothing. That is by design (tabula rasa, no hand priors).
Development is staged like an organism, and each stage has an entry gate:

**Stage 0 — Infant (now → first EARNED signal).**
Coverage: current 153 tickers. Signals: P1 insider clusters (first real signal wired to
log_prediction), revenue-acceleration flags. Everything provisional. No live sizing.
Gate to Stage 1: ≥2 signals EARNED (n≥10) and reconciliation running unattended 14 days.

**Stage 1 — Toddler: sector eyes.**
Add per-sector anchor sets: ~3 names per sector across all 11 GICS sectors, PLUS the
sector ETFs (XLK XLE XLF XLV XLI XLY XLP XLU XLB XLC XLRE) as reference bodies.
New perception: **stock-vs-sector divergence** — log when a name moves and its ETF
doesn't (idiosyncratic: thesis-specific cause likely) vs when the ETF moves and the
name doesn't (laggard candidate or dead name). Divergence events become claim rows.
Gate to Stage 2: divergence signal itself reaches EARNED status either way (even a
proven-useless result is a kept negative).

**Stage 2 — Child: breadth expansion.**
Grow each sector from 3 → 10 → 20 → 40 names, but ONLY as reconciliation capacity and
data quality keep up (never add names faster than outcomes can be graded). Universe
ceiling ~400–500 names, always inside the $5–$200 filter. Sector-rotation perception:
weekly relative-strength ranking of sector ETFs logged as regime context on every
prediction, so signals can later be scored PER REGIME (a signal that only works in
risk-on tape should learn that about itself).

**Stage 3 — Adolescent: the reading brain.**
Slow channel goes live: EDGAR (Form 4 near-real-time, 8-K, 10-K/Q sections via
edgartools — MIT licensed), transcripts, tiered news (Benzinga free API tier first;
Basic $27/mo when justified; Bloomberg parked until AUM justifies ~$24K/yr).
extract_claims.py: document in → claim rows out (entity A needs X / entity B supplies X /
dated / tiered). hypothesize.py: nightly LLM reasoning pass over the claim graph →
hypothesis rows (thesis, reasoning-type tag, falsifiable prediction, horizon, confidence).
Cost routing: cheap model for extraction, strong model for synthesis, batch API nightly
(pattern proven elsewhere to cut LLM cost 5–10x).
**Key upgrade: weights accrue to LINES OF REASONING** (bottleneck-physics thoughts vs
narrative-momentum thoughts vs insider-following thoughts), not just to signals. The
system learns which KINDS of thinking pay.

**Stage 4 — Savant: convergence mind.**
Full loop at breadth: causal graph proposes (quarters horizon), crowd telemetry times
(days horizon), convergence layer surfaces 2–3 names/day, per-regime calibrated weights,
Tyr decides. Cannibalized parts inventory: hermes-financial (SEC/agent framework, MIT),
LevyHsu/Hermes (60+ RSS harvester + 2-stage LLM pipeline, free sources), River (online
learning, Stage 3+ only), Nous hermes-agent (orchestration shell, optional — plain
Python + Task Scheduler is the default and is sufficient).

## 7. DIVISION OF LABOR (WOLF PACK PROTOCOL)

- **Tyr (human):** direction, final reads, all execution, the unscalable judgment.
- **Claude / Fable 5 (Fenrir):** synthesis, architecture, nightly hypothesize pass, memory.
- **Claude Code:** engineering on the desktop; builds from THIS document.
- **Perplexity:** deep research missions (tool landscapes, literature, source discovery).
- **DeepSeek:** red team — attack this spec, find the overfit, find the leak.
- Convergence protocol: when ≥2 AIs independently produce the same design/finding, it is
  promoted to canonical and merged into this document with a version bump.

## 8. STANDING KILL CRITERIA (conscience)

Any signal, module, or idea dies or shelves if:
- No one is writing growing checks anywhere in its causal chain.
- It cannot state a falsifiable prediction with a horizon.
- Its EARNED weight sits at/below the measured base rate (~30% for +5%/14d class)
  after n≥30 with no regime in which it outperforms.
- It requires latency we do not have or capital tiers we are not at.
- It sounds too clean (flag chains that explain everything).

## 9. VERSION LOG

- v1.0 (2026-07-04): Consolidated from Fable 5 sessions (doctrine, thought-factory
  architecture, MU/cooling causal doctrine, weights-vs-thinking distinction), Perplexity
  research (assemble-don't-invent stack, event-sourcing framing, five-layer confirmation),
  DeepSeek pending red team. Phase 1 code built and proven same day.
