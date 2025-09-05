# 05-order-execution-alpaca.md
version: 2025-09-04
status: canonical
scope: order-execution
implementation:
  mode: "Preview by default; execution must use Alpaca SDK/API outside chat."
  note: "Examples show payload shapes only. Do NOT invoke live HTTP from chat."
contracts:
  order:
    schema: {symbol, side, qty|notional, type, time_in_force, stop?, limit?, extended_hours?, client_order_id?}
  bracket:
    schema: {order_class:"bracket", take_profit:{limit_price}, stop_loss:{stop_price, limit_price?}}
  oco_exit:
    schema: {order_class:"oco", take_profit:{limit_price}, stop:{stop_price|stop_limit}}
  trailing_stop:
    schema: {type:"trailing_stop", trail_percent|trail_price}
invariants:
  - exactly one of qty or notional
  - refuse orders without a stop
  - DRY_RUN unless "CONFIRM: LIVE"
  - reconfirm if price drift >0.5% from preview
  - idempotency via client_order_id recommended
prechecks:
  - symbol tradable (Finnhub + broker status)
  - session open or ext-hours allowed
  - risk limits pass (protection daemon)
  - buying power available
  - position sizing valid
  - no duplicate open order
examples_ps7_preview_only:
  place_dry_run_shape: |
    $order = @{ symbol="AAPL"; side="buy"; qty=100; type="limit"; time_in_force="day"; limit_price=195; stop_price=190 }
    $order | ConvertTo-Json -Depth 5   # PREVIEW ONLY
  cancel_shape: |
    # PREVIEW ONLY: show intended resource id
    $cancel = @{ order_id = "<id>" }; $cancel
execution_paths_outside_chat:
  sdk: "alpaca-py (TradingClient + OrderRequest types)"
  rest: "Alpaca Orders API"
router:
  node: place_order
  triggers: ["buy","sell","short","cover","market","limit","stop","bracket","oco","trailing_stop"]
  prechecks: ["symbol","session","risk","bp","sizing","duplicate"]
tests:
  smoke:
    - "Buy 100 AAPL 195 limit" -> "requires stop; DRY_RUN preview"
    - "Cancel order 123abc" -> "cancel payload preview"
changelog:
  - 2025-09-04: make execution preview-only in docs; point to Alpaca SDK/API for real sends
