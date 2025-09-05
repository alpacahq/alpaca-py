# 02-strategy-signals.md
version: 2025-09-04
status: canonical
scope: strategy-signals
contracts:
  inputs: [symbol, htf:"1d", ltf:"15m", params?]
  outputs: [signal:"long|short|stand_down", confidence:0..1, levels:{entry, stop, targets[]}, notes?]
invariants:
  - two-step: daily setup then 15m confirmation unless entry_mode=open_breakout
  - indicators from Finnhub-derived data; print tz on timestamps
params_defaults:
  ema_fast: 20
  ema_base: 50
  rsi_len: 14
  min_conf: 0.55
  rvol_15m_min: 1.2
  rvol_1m_min: 3.0            # for open_breakout gating
  entry_mode: confirm_15m     # or open_breakout
  a_table_proxy: {rs_12w_vs_SPY_min: 0.10, short_float_min: 0.15}
strategies:
  pullback_long:
    htf: ["price > SMA50", "pos_in_5d_range <= 25%", "daily setup bar closes in top 25% of day"]
    ltf_confirm:
      confirm_15m: ["break of prior 15m high", "rvol_15m >= rvol_15m_min"]
      open_breakout: ["break of setup-bar high within first 30m", "rvol_1m >= rvol_1m_min"]
    stop: "below setup-bar low or ATR(14)*1.2"
    targets: ["R=1", "R=2 default", "runner optional"]
  breakout_long:
    context: ["ATH preferred → 'blue-sky'"]
    ltf_confirm:
      confirm_15m: ["15m ORB break-and-hold", "rvol_15m >= rvol_15m_min"]
      open_breakout: ["opening range break", "rvol_1m >= rvol_1m_min"]
    stop: "below breakout level - buffer"
    targets: ["measured move or R=2"]
  breakdown_short:
    context: ["ATL preferred → 'abyss'"]
    ltf_confirm:
      confirm_15m: ["15m low break with acceptance"]
      open_breakout: ["opening range breakdown", "rvol_1m >= rvol_1m_min"]
    stop: "above trigger high + buffer"
    targets: ["R=1 then R=2"]
  range:
    htf: ["defined channel support/resistance (pos_in_range near edges)"]
    ltf_confirm: ["reversal candle at edge", "oscillator turn"]
    stop: "outside range edge"
    targets: ["mid then opposite edge"]
  news_catalyst:
    htf: ["fresh news/earnings reaction"]
    ltf_confirm: ["first pullback hold then break"]
    stop: "pre-catalyst swing"
    targets: ["R-based; respect volatility"]
  rl_blend:
    candidates_from: ["holly_eod", "playbook scans"]
    gates: ["min_conf", "technical confirm per selected play"]
    stop: "per FinRL stop_dist or technical"
    targets: ["per play; default R=2"]
output_format:
  levels: {entry: number, stop: number, targets: [number, ...]}
router:
  node: strategy_signals
  triggers: ["signal","entry","exit","rsi","macd","sma","ema","atr","setup"]
  prechecks: []
tests:
  smoke:
    - "Pullback long for AAPL" -> "entry above setup-bar high; stop = setup-bar low"
    - "Breakout long ATH with open_breakout" -> "requires rvol_1m >= 3.0"
    - "RL blend requires min_conf" -> ">= 0.55 and confirm"
changelog:
  - 2025-09-04: add open_breakout path, RVOL gates, setup-bar rules, A-Table proxy & HOLLY candidates
