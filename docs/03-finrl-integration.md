version: 2025-09-04
status: planned
scope: finrl-integration
note: "No live FinRL endpoints exist in this project. Treat the flow below as conceptual."
concepts:
  train:
    request_shape: {segment, features[], horizon}
    response_shape: {model_id, ts_utc}
  predict:
    request_shape: {model_id, symbol}
    response_shape: {confidence:0..1, stop_dist, entry_delay}
invariants:
  - no code edits from chat
  - model outputs gate entries; do not auto-trade
  - log profile/version in journal
candidate_flow:
  inputs: ["playbook scans", "HOLLY EOD list (read-only)"]
  policy: "treat model-positive names as candidates; still require technical + risk checks"
examples_ps7_preview_only:
  train_preview: |
    # PREVIEW ONLY (no endpoint)
    $body = @{ segment="pullback_long"; features=@("rsi","ema50"); horizon=20 } | ConvertTo-Json
    $body  # show payload shape; do not POST
  predict_preview: |
    # PREVIEW ONLY (no endpoint)
    $qs = "?model_id=<id>&symbol=AAPL"
    $qs  # show query shape; do not GET
router:
  node: backtest_train
  triggers: ["backtest","train","finrl","optimize","walk-forward","tune","predict"]
  prechecks: []
tests:
  smoke:
    - "Train pullback segment" -> "preview shows model payload"
    - "Predict TSLA" -> "preview shows query shape"
changelog:
  - 2025-09-04: mark as planned; replace endpoint calls with preview-only shapes
