# 08-finnhub-quick-reference.md
version: 2025-09-04
status: non-normative
scope: quick-ref
contracts:
  inputs: {task, symbol?, resolution?, from?, to?}
  outputs: {endpoint, required_params[], example}
map:
  quote: {endpoint:"/quote", required_params:["symbol"], example:'GET /quote?symbol=AAPL'}
  candles: {endpoint:"/stock/candle", required_params:["symbol","resolution","from","to"], example:'GET /stock/candle?symbol=AAPL&resolution=60&from=...&to=...'}
  rsi: {endpoint:"/indicator", required_params:["symbol","resolution","indicator=rsi","timeperiod"], example:'...&indicator=rsi&timeperiod=14'}
  ema: {endpoint:"/indicator", required_params:["symbol","resolution","indicator=ema","timeperiod"], example:'...&indicator=ema&timeperiod=50'}
  macd: {endpoint:"/indicator", required_params:["symbol","resolution","indicator=macd"], example:'...&indicator=macd'}
  peers: {endpoint:"/stock/peers", required_params:["symbol"], example:'GET /stock/peers?symbol=AAPL'}
  news: {endpoint:"/company-news", required_params:["symbol","from","to"], example:'GET /company-news?symbol=AAPL&from=YYYY-MM-DD&to=YYYY-MM-DD'}
  earnings: {endpoint:"/calendar/earnings", required_params:["from","to"], example:'GET /calendar/earnings?from=...&to=...'}
notes:
  - "Derived metrics (RVOL, ATR, Gap%, PIR) computed from candles/quotes; print tz"
router:
  node: infra_docs
  triggers: ["Finnhub docs","endpoints","params","examples"]
  prechecks: []
tests:
  smoke:
    - "RSI for MSFT 15m" -> "indicator params listed"
    - "Peers for NVDA" -> "endpoint + example"
changelog:
  - 2025-09-04: clarify derived metric computation for strategy filters
