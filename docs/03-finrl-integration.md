# 03-finrl-integration.md
version: 2025-09-04
status: canonical
scope: finrl-integration
contracts:
  train:
    request: {segment, features[], horizon}
    method: POST /train
    response: {model_id, ts_utc}
  predict:
    request: {model_id, symbol}
    method: GET /predict
    response: {confidence:0..1, stop_dist, entry_delay}
invariants:
  - no code edits from chat
  - model outputs gate entries; do not auto-trade
  - log profile/version in journal
candidate_flow:
  inputs: ["playbook scans", "HOLLY EOD list (read-only)"]
  policy: "treat model-positive names as candidates; still require technical + risk checks"
ps7_examples:
  train: |
    $body = @{ segment="pullback_long"; features=@("rsi","ema50"); horizon=20 } | ConvertTo-Json
    Invoke-RestMethod -Method Post -Uri $FinRL/train -Body $body -ContentType "application/json"
  predict: |
    Invoke-RestMethod -Method Get -Uri "$FinRL/predict?model_id=$mid&symbol=AAPL"
router:
  node: backtest_train
  triggers: ["backtest","train","finrl","optimize","walk-forward","tune","predict"]
  prechecks: []
tests:
  smoke:
    - "Train pullback segment" -> "model_id returned"
    - "Predict TSLA" -> "{confidence, stop_dist, entry_delay}"
changelog:
  - 2025-09-04: add HOLLY EOD as candidate input to RL_Blend flow
