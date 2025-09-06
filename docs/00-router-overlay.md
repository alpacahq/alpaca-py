# 00-router-overlay.md
version: 2025-09-04
status: non-normative
scope: router-overlay

meta: {shell:"PS7", dry_run_default:true, live_token:"CONFIRM: LIVE",
       tz_policy:"Print timestamps with timezone.",
       ambiguity:"If unclear, default to market_data, state assumption, ask one follow‑up.",
       footer_log:"{node:<node>, triggers:[...], prechecks_passed:true|false}"}

precedence: [cancel_order, place_order, risk_check, account_status, market_data, strategy_signals, backtest_train, automation_ops, infra_docs, meta]

symbol_detection: {method:"Uppercase tokens 1‑6 chars; confirm via Finnhub.",
                   stoplist:["ALL","FOR","BUY","SELL","OPEN","CLOSE","LONG","SHORT","USD","DAY"]}

timeframe: {default:"1d"}
order_schema: {required:["symbol","side","qty_or_notional","type","time_in_force"],
               defaults:{type:"market", time_in_force:"day", extended_hours:false},
               qty_or_notional:"$=notional else shares"}

prechecks:
  symbol_tradable: "Confirm via Finnhub + broker."
  session_open: "If closed, report next session."
  risk_limits: "Apply protection‑daemon limits."
  buying_power: "Check Alpaca."
  position_sizing: "Apply unified sizing."
  duplicate_order: "If identical open order exists, amend/cancel first."

nodes:
  cancel_order: {triggers:["cancel","close order","flatten"], pre:["list open orders","validate ids"], action:"Prepare cancel payload. DRY_RUN unless live token."}
  place_order:  {triggers:["buy","sell","short","limit","stop","bracket","oco"], pre:["symbol_tradable","session_open","risk_limits","buying_power","position_sizing","duplicate_order"], action:"Build payload. DRY_RUN unless live token. Refuse if no stop."}
  risk_check:   {triggers:["risk","exposure","limits"], action:"Compare exposure vs limits. Propose fix."}
  account_status:{triggers:["positions","orders","pnl","balance","fills","equity","bp","history"], action:"Fetch metrics. Flag anomalies."}
  market_data:  {triggers:["price","quote","ohlcv","volume","news","short interest","float"], action:"Finnhub query. Print value + timestamp + tz."}
  strategy_signals:{triggers:["signal","entry","exit","rsi","macd","sma","ema","atr"], action:"Compute per strategy doc. Output signal + confidence."}
  backtest_train:{triggers:["backtest","train","finrl","optimize"], action:"Emit FinRL config or PS7 script. Report metrics."}
  automation_ops:{triggers:["orchestrate","daemon","schedule","restart","deploy","logs"], action:"Map to ops. Show PS7/Railway cmd."}
  infra_docs:   {triggers:["Railway","OpenAPI","Alpaca docs","FinRL docs","keys","env"], action:"Point to doc section. Minimal example."}
  meta:         {triggers:["change rules","prompt","constraints","policy"], action:"Recite rules. Refuse unsafe changes."}

# Batch screening policy (schema-only Finnhub)
batch_screen:
  chunk_size: 6
  pulls:
    daily:   {resolution: "D",  lookback_days: 120}
    intraday:{resolution: "15", lookback_days: 10}
  compute:
    - sma50: "mean(last 50 closes)"
    - atr14: "Wilder TR avg over last 14 daily bars"
    - pir_5d_pct: "position in 5-day high/low"
    - rvol15_20: "last 15m volume / avg prior 20 bars"
  classify_rules:
    - "Pullback Long if close > sma50 AND pir_5d_pct <= 25"
    - "Breakout Long if close >= 20-day high*0.999"
    - "Breakdown Short if close <= 20-day low*1.001 AND close < sma50"
    - "Range if 30 <= pir_5d_pct <= 70"
  confirmation_gate: {rvol15_min: 1.2}
  output_table_cols: [symbol, close, sma50, atr, pir_pct, rvol15, candidates, confirm]
  retries_on_429: [1, 2, 4]
  tz_policy: "Print ET"
