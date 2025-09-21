# Watchlist Workflow

**Purpose:** Centralise opportunity discovery and tracking. Maintain strategy‑specific watchlists; surface high‑conviction, capital‑aware candidates.

## Sources
- **Classifier:** score setups; gate at `score ≥ 0.70` and labels {StrongBuy, Buy}.
- **Quotes/Candles:** Finnhub for price/volume; respect TTL rules.
- **FinRL (optional/consent):** signals/backtests to support conviction.
- **Account/Positions:** Alpaca balances + current holdings.
- **Journal:** persistent store for watchlist entries and daily summaries.

## Data Contract
Use `watchlist_entry.schema.json` for entries:  
`{ "strategy": "<name>", "symbol": "<TICKER>", "reason": "<short>", "added_ts": "<ISO8601>" }`.

## Daily Session Routine
1) **Load prior entries** from Journal; prune stale (TTL 10 sessions by default).
2) **Scan candidates**:
   - Screen by strategy minima (e.g., Breakout: RVOL≥1.5, PIR≥80; Pullback: RSI 35–55, RVOL 0.8–1.2).
   - Run **Classifier**; tag as:
     - `active` if gate passes (score/label OK),
     - `monitor` if close‑miss on minima (e.g., RVOL short, PIR < threshold).
3) **Cross‑check account**:
   - Compare against **balances/buying power** and **positions**.
   - If adding a new trade exceeds per‑name exposure (20%) or daily halt threshold, **downgrade** priority.
4) **Risk & session gates**:
   - Default **per‑trade risk = 2% of equity**; compute size from planned SL distance.
   - RTH: allow bracket TP+SL; EXT: limit+Day+extended, no brackets/trailing.
5) **Surface actions**:
   - For `active` items: propose a **Trade Preview** (DRY_RUN) with `risk.perTradePct=0.02`.
   - For `monitor` items: keep on list; set price/indicator alerts (journal note).
6) **Journal**:
   - Append a session summary: counts {active, monitor}, top symbols, notable changes.

## Add / Update / Remove
- **Add:** when a symbol first matches a strategy minimum or passes Classifier gate.
- **Update:** if status changes (monitor→active, active→exit); record cause (RVOL/PIR/level reclaim).
- **Remove:** stale (TTL exceeded), thesis broken (range break against plan), earnings block inside 48h.

## Prioritisation
Rank by:
1) **Classifier score**, then
2) **Liquidity/Spread fitness**, then
3) **Proximity to trigger** (e.g., distance to breakout level), then
4) **Portfolio fit** (exposure by sector/name; correlation to holdings).

## Example Entry
```json
{
  "strategy": "breakout",
  "symbol": "AAPL",
  "reason": "RVOL 1.8, PIR 86, above SMA50; nearing range high 198.50",
  "added_ts": "2025-09-21T18:30:00Z"
}
```

## Hand‑offs
- **From Watchlist → Simulation (DRY_RUN):**
  - Build `trade_preview` with:
    - `order.type="limit"`, `order.tif="day"`, `order.session="RTH|EXT"`,
    - `exits.stop` per strategy (tightest of level vs ATR rule),
    - `exits.target` measured move / prior high,
    - `risk.perTradePct=0.02` (default), `rr` if requested.
- **From Simulation → Live:**
  - Only on explicit **CONFIRM: LIVE** and after re‑checking drift and gates.

## Notes
- If a symbol fails the gate, **do not trade**—leave on watchlist with a clear reason.
- Re‑evaluate after material changes (RVOL spike, level reclaim, catalyst).
