# Cosmos Savant

One integrated, always-on mission control for a single active trader. A
**preparation machine** — AlphaGo's loop applied to markets: parallel strategy
families are the self-play, the append-only ledger is the perfect score, weights
are patterns earning trust. **Not a day-trading bot. Not an algo.** Trade
execution is NEVER performed by a language model — it is human-authorized,
deterministic, and governed (Section 0).

## Partners
- **Tyr (Alex Payne)** — orchestrator, final ratification authority.
- **Claude** — verify station + co-steward (the only writer of absolute numbers).
- **Gemini Spark** — research / scheduled sensing, permanently credited co-contributor.
- **Claude Code** — builder, third partner.

## Layout
```
CONSTITUTION.md              charter (Sections 0-8); ADRs amend it
COSMOS_SAVANT_HANDOFF.md     the ratified master handoff, verbatim (Section 8.1)
OPEN_QUESTIONS.md            living register of known-unknowns (Section 7)
adrs/                        27 ADRs, one file each, with provenance frontmatter
schemas/                     JSON schemas (prediction_row v1.0.1, run_ledger, oracle, quarantine, enums)
boards/                      world/ (HORMUZ, TAIWAN) + domain/ (GOLD, SPACE)
hermes/                      ancestry vault — governor.py runs verbatim; ledger/reconcile are forebears
cosmos/                      the live package (oracle, verify_intake, checkpoints, edgar_poller, utils)
tests/                       pytest suite (66 tests)
data/                        local state (gitignored): cosmos.duckdb, staging_mirror/, quarantine/
scripts/                     smoke_fro.py (Phase-1 instrument smoke test)
credentials/                 service_account.json goes here (gitignored)
```

## Capability ground truth (Section 3 — build only on MEASURED)
- **MEASURED** (Robinhood MCP, re-verified live 2026-07-27 via `scripts/smoke_fro.py`):
  real-time quotes incl. AH, 15-second OHLCV, daily historicals, fundamentals/
  float/cap, earnings calendar, scanner + watchlist.
- **FAILED**: options quotes (403, no entitlement) — all implied-move features
  dead until entitlement changes (OQ-OPTIONS).
- **CLAIMED** (no load-bearing use): FRED direct access, Google Tasks alert
  channel. The oracle's load-bearing path is the HYG proxy over MEASURED bars.

## Run the tests
```bash
py -m venv .venv
.venv/Scripts/python.exe -m pip install pytest
.venv/Scripts/python.exe -m pytest
```

## The four loops (ADR-019)
SENSE (24/7) · THINK (triggered) · SURFACE (market hours) · LEARN (nightly/
weekly/monthly). The interface (The Wall) is built **last**, around a loop
already proven closed.
