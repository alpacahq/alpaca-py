version: 2025-09-03
status: canonical
scope: global-rules
contracts:
  inputs: [request_text, user_mode: PAPER|LIVE, tz?]
  outputs: [decision: {node, triggers}, footer_log, errors?]
invariants:
  - live orders require token "CONFIRM: LIVE"
  - earnings holds default: forbid; override token "OVERRIDE: EARNINGS"
  - no background jobs; act in-reply only
  - every trade has a stop; do not widen stops
  - respect buying power, PDT, market hours, exchange rules
  - timestamps include timezone on all data prints
  - use Finnhub only for live quotes/snapshots
  - journaling required: signal, open, adjust, close, error
sizing:
  risk_tiers: {Tier1: "1.5-2% equity", Tier2: "1%", Tier3: "<=0.5%"}
  formula: "shares = floor(risk_$ / abs(entry - stop))"
entry_timing_modes:
  confirm_15m: "Daily setup then 15m structure/ORB confirm"
  open_breakout: "Next-session open break; require rvol_1m >= 3.0 and confirmation within first 30m"
holly_integration:
  watchlist_policy: "Pull HOLLY trades after close; humans review; candidates feed RL_Blend"
  autonomy: "HOLLY ideas are not auto-traded; they gate review only"
proxies_and_filters:
  a_table_proxy:
    rs_12w_vs_SPY_min: 0.10
    short_float_min: 0.15
    note: "Proxy for SCoRe+short-squeeze screens when TI SCoRe not available"
confirmation:
  dry_run_default: true
  drift_reconfirm: "reconfirm if quote moved >0.5% from preview"
dependencies: [Finnhub, Alpaca, FinRL]
router:
  node: meta
  triggers: ["rules","prompt","constraints","policy","sizing","confirm token","earnings"]
  prechecks: []
tests:
  smoke:
    - "What token is needed for live?" -> "CONFIRM: LIVE"
    - "Can we hold through earnings?" -> "forbid unless 'OVERRIDE: EARNINGS'"
    - "Open-breakout mode?" -> "allowed with rvol_1m >= 3.0"
changelog:
  - 2025-09-03: add entry_mode toggle; default earnings-hold forbid; A-Table proxy; HOLLY EOD use
