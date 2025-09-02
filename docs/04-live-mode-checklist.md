# Live Mode Checklist

## 1) Environment
- Mode: paper vs live correct.
- Market status acceptable (or extended if allowed).
- Broker health; journaling reachable.

## 2) Data freshness
- Refresh quote/candles; recompute indicators.
- Revalidate setup still valid; withdraw if invalid.
- Quick news/sentiment check.

## 3) Risk
- Sizing: risk_$ = equity * tier_pct; shares = floor(risk_$ / |entry - stop|).
- R/R ≥ 2:1 unless justified.
- Exposure: sector/correlation caps; buying power sufficient.
- PDT guard (<$25k: ≤3 day trades rolling 5 days).

## 4) Order integrity
- Exactly one of qty or notional.
- Bracket needs whole shares; round down.
- Trailing via separate trailing order (trail_percent or trail_price).
- Limit/stop prices make sense (no inverted legs).

## 5) Confirmation preview (to user)
- Symbol, side, qty, entry (or market), stop, target/trailing, TIF.
- Est risk $, est reward $.
- Mode banner: PAPER or LIVE.
- Prompt: “Type Confirm to place, or Cancel.”

## 6) Slippage guard
- If live price moved >0.5% from proposal, alert and re-confirm.

## 7) Execute
- Submit; capture order id; journal trade_open.
- Report fill avg price; attach legs or place trailing.

## 8) Protect & monitor
- Hand off to daemon: trailing, time exits, events.

## 9) On error
- Show raw message; propose fix (reduce qty, widen stop, switch order type); retry only on user consent.
- Journal error.

