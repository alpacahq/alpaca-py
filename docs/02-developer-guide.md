# Developer Guide

## Stack
- Orchestrator: controls flow, state, and prompts.
- Strategy Engine: playbook modules + RL blend.
- Market Data: Finnhub.
- Broker: attached broker action (Alpaca REST).
- Journal: external journaling action (persistent).
- Protection Daemon: trailing, time exits, event handling.
- FinRL: /train (segmented), /predict (fetch thresholds).

## Orchestration flow
1) Refresh data (quotes, candles, indicators, news, calendars).
2) Generate signals:
   - Playbook scans (RSI/MAs/BB/volume/patterns).
   - FinRL thresholds via /predict inform stop_distance, entry_delay, etc.
3) Validate:
   - Technical + news checks; veto on conflicts or stale data.
   - R/R ≥ 2:1, risk and exposure limits, PDT.
4) Propose:
   - Mini-thesis, explicit levels, sizing, scenario framing.
5) Confirm:
   - Await explicit “Confirm”.
6) Execute:
   - POST order; bracket when target is structural; trailing via separate order.
7) Journal:
   - signal → trade_open → adjustments → trade_close.
8) Protect:
   - Daemon trails stops, time exits, event risk handling.
9) Learn:
   - After closes: journal → /train per segment → refresh /predict.

## Finnhub usage (common)
- Quote/candles for prices and ATR proxy.
- Indicators: RSI, MACD, SMA/EMA, BB.
- Recommendation trends; news & sentiment.
- Peers, profile2 (sector/industry).
- Earnings/economic calendars.

## Broker action (Alpaca specifics)
- GET /v2/account for buying power, equity, PDT status.
- GET /v2/positions for exposure checks.
- POST /v2/orders:
  - Exactly one of qty or notional.
  - Bracket: order_class=bracket with take_profit/stop_loss; prefer whole shares.
  - Trailing: separate trailing stop (trail_percent or trail_price); do not assume trailing leg inside bracket.
- Auto-remediation:
  - Downsize if insufficient buying power.
  - Round fractional qty down for brackets.
  - Surface errors verbatim; propose fix.

## FinRL orchestration (zero-code path)
- Segment journal by strategy_card, market_regime_tag, time-of-day.
- POST /train for each segment with save_params=true.
- GET /predict before scanning/execution; treat as tuned thresholds store.
- Apply thresholds client-side across watchlists with Finnhub scans.

## Sizing and exposure
- risk_$ = equity * tier_pct.
- shares = floor( risk_$ / abs(entry - stop) ).
- Cap total open risk; downgrade new size when sector or factor exposure is high (profile2, peers).
- Warn on high correlation and duplicate beta.

## Errors
- Catch API errors; show message; suggest correction (e.g., widen stop, reduce qty).
- Never proceed on partial failure without user consent. Always journal errors.

