# SPARK_TASK_ORDERS — standing orders + ad-hoc templates

The human installs these by pasting them into Gemini **once** (§8.3). Spark has
no push channel by design; it runs on its own schedule and writes the one Google
Sheet ("Market Movers Report", `1Rk9…57zo`). The desk polls read-only, verifies,
anchors, grades.

## Write-authority (binds every deliverable — ADR-002)
Spark writes **causes, sources, names, theses ONLY**. NEVER prices, percentages,
run dates, run magnitudes, or EPS figures — those are the verify-station's lane.
Every deliverable: land as BOARD ROWS or queue rows, end with a `COMPLETE`
terminator (+ `run_id`, `row_count`), and close with a read-back. Claim-accuracy
is scored on everything. New capabilities enter ONLY via a nonce proof to
`capability_proofs`.

## Standing orders (recurring)
1. **daily_sweep** — top movers with a one-line sourced mechanism each (board-row format).
2. **catalyst_map** — refresh the rolling 60-day calendar (ADR-020); one row per scheduled event + branch table.
3. **board_<domain>** — maintain HORMUZ / TAIWAN / GOLD / SPACE (+ new fault lines) under Names Law (ADR-017).
4. **chatter** — mention-velocity vs baseline; `canon_tag: HYPOTHESIS` + source URL, ATTENTION data only, never truth.
5. **heartbeats** — periodic liveness row (age drives §8.2 WARN/CRITICAL).

## Ad-hoc Order Templates (paste one when needed)
- **INVESTIGATION TICKET** — "Investigate <ticker/theme>. Return: mechanism, upstream source URLs, second-order names. No numbers."
- **BOARD DEEP-DIVE** — "Extend board_<domain> tier <E1/E2/E3>. Names + mechanism + one source URL per claim."
- **THESIS REQUEST** — "Draft a thesis on <catalyst>. Direction + relative offsets + distribution (sum 1.0) + canon tags + sources. No absolute prices."
- **NONCE CHALLENGE** — "Prove capability <X>. Write nonce <value> to capability_proofs and the requested artifact."

> STATUS: scaffolded by the builder from §8.3 + ADR-002/017/020. The exact ratified
> order wording is PENDING the companion file's canonical text (tracked with the
> ADR-fulltext gap). Nothing here load-bears until ratified.
