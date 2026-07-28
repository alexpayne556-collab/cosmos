# GENESIS live state — captured 2026-07-27 (Section 5)

Import source for the first-boot GENESIS event (Section 8.2). These absolute
prices are VERIFY-station values (instrument-written in Round 12) — captured
here verbatim so nothing is lost. They are NOT yet written to the ledger; ledger
import is Day 2+ (`verify_intake.py` + descendant ledger), logged as GENESIS.

## Ten active prediction rows

### Claude (6) — ABSOLUTE
| Ticker | Thesis | Entry | Target | Invalidation | Status |
|--------|--------|-------|--------|--------------|--------|
| CLS  | long        | 342.50 | 360 | 318.23 | open |
| APLD | contrarian fade | 27.80 | 29.60 | 26.36 | open |
| NE   | short       | 40.02 | 38  | 41.60 | open |
| CDNS | long        | 352.25 | 362 | 340 | open |
| AMKR | long        | 60.50 | 63.50 | 58.50 | **LOSS** (traded through invalidation, extended session Jul 27) |
| SMH  | regime long | 545.78 | 557 | 536 | open |

### Gemini (4) — RELATIVE_PCT, anchored to Jul 27 closes (ADR-001)
| Ticker | Thesis | Anchor | Target | Invalidation | Status |
|--------|--------|--------|--------|--------------|--------|
| BA   | short   | 211.50 | 198.81 | 217.85 | open |
| PYPL | long    | 56.07 | 61.12 | 53.27 | open |
| KO   | no-move | band 81.97–86.17 | — | — | open |
| STX  | long    | ANCHOR_PENDING → Jul 28 close | — | — | pending (OQ-STX-ANCHOR) |

Grading cadence: 4 PM daily.

## Robinhood infrastructure (live)
- Scan: **WPK — Gainers Harvest** (`17642cfe…`)
- Watchlists: **🐺 Ledger — Live Tournament** (`733ee5f4…`) · **🏃 Cohort 2026-07-27** (`8a1eb001…`) · **🔁 Serial Runner Suspects** (`810a1bcd…`) · **🌍 World Boards — Verified Seeds** (`bf5c8aa4…`)

## Verified serial runners (bar-convicted)
- **RDW** — 5 runs incl. May 26 +26.0%
- **LUNR** — 4 runs May–Jun, then 36→13 July bleed
- **APLD** — May 21 +21.5%, Jul 20–21 +16.5%
- **ASTS** — 63→133 in May

## Capability proof
`capability_proofs` tab live in the Market Movers sheet — nonce **WPK-R5-4c1f9e2a**, verified by human eyes.
