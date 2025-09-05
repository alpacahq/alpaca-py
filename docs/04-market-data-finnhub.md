# 04-market-data-finnhub.md
version: 2025-09-04
status: canonical
scope: market-data
implementation:
  source: "Finnhub (fetched server-side by classifier action)"
  guidance: "Do NOT call Finnhub from the chat layer."
contracts:
  inputs: {symbol, timeframe, range?}
  outputs: {field:"price|ohlcv|indicator|news|derived", ts_utc, tz:"America/New_York", source:"Finnhub", data}
tasks:
  quotes: "Real-time quote via action"
  candles: "OHLCV via action with explicit resolution"
  indicators: "RSI, SMA/EMA, MACD via action"
  peers: "Peer symbols"
  news: "Company news and sentiment"
  earnings: "Earnings calendar"
derived_metrics:
  rvol: "relative volume vs time-of-day baseline"
  atr: "ATR from daily candles"
  gap_pct: "((open - prev_close)/prev_close)*100"
  pos_in_range: "position in current or lookback range (e.g., 5d, 1d)"
invariants:
  - use Finnhub only for live prices and snapshots
  - if premium-gated or unavailable: say 'unavailable with current plan'
  - print explicit timestamp and timezone
pitfalls:
  - symbol formats differ per venue
  - rate limiting; back off and report
router:
  node: market_data
  triggers: ["price","quote","ohlcv","volume","news","peers","short interest","float","earnings"]
  prechecks: []
tests:
  smoke:
    - "Show TSLA 1h OHLCV now" -> "table + ET timestamp"
    - "AAPL price" -> "quote with ts and source"
    - "Compute RVOL, ATR, PIR, gap%" -> "derived block present"
changelog:
  - 2025-09-04: clarify server-side Finnhub calls through action; no direct REST
