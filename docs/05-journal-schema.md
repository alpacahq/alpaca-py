# Journal Schema

## Required fields (by event)
- Common: timestamp (ISO-8601 UTC), event_type, symbol, strategy.
- signal: side, signal_time, entry_ref_price, stop, target_or_trailing, rationale, tags[], atr_at_signal, market_regime_tag.
- trade_open: side, quantity_or_notional, entry_time, entry_price, stop, target_or_trailing, user_confirmation (bool), trade_id.
- adjustment: trade_id, field_changed (e.g., stop), new_value, note.
- trade_close: trade_id, exit_time, exit_price, outcome (win/loss/flat), realized_R, profit_loss, exit_reason.
- error/info: message, context.

## Additional fields
- fees_slippage, finrl_profile/params_version, signal_confidence, protection_actions[].

## Example: signal
{
  "timestamp": "2025-09-02T14:35:22Z",
  "event_type": "signal",
  "symbol": "AAPL",
  "strategy": "Breakout Long",
  "side": "BUY",
  "signal_time": "2025-09-02T14:35:00Z",
  "entry_ref_price": 150.50,
  "stop": 147.00,
  "target_or_trailing": {"target": 158.00},
  "rationale": "Close above resistance with 1.7x volume; RSI>60.",
  "tags": ["breakout","trend_up"],
  "atr_at_signal": 2.1,
  "market_regime_tag": "risk_on",
  "signal_confidence": 0.78
}

## Example: trade_open
{
  "timestamp": "2025-09-02T14:40:10Z",
  "event_type": "trade_open",
  "trade_id": "AAPL-20250902-01",
  "symbol": "AAPL",
  "strategy": "Breakout Long",
  "side": "BUY",
  "quantity_or_notional": {"qty": 100},
  "entry_time": "2025-09-02T14:40:07Z",
  "entry_price": 150.72,
  "stop": 147.00,
  "target_or_trailing": {"target": 158.00},
  "user_confirmation": true
}

## Example: adjustment (trailing)
{
  "timestamp": "2025-09-02T16:10:00Z",
  "event_type": "adjustment",
  "trade_id": "AAPL-20250902-01",
  "field_changed": "stop",
  "new_value": 152.50,
  "note": "Trail to lock gains (+1R)."
}

## Example: trade_close
{
  "timestamp": "2025-09-03T10:15:00Z",
  "event_type": "trade_close",
  "trade_id": "AAPL-20250902-01",
  "exit_time": "2025-09-03T10:14:57Z",
  "exit_price": 155.00,
  "outcome": "win",
  "realized_R": 1.38,
  "profit_loss": 428.00,
  "exit_reason": "target_hit"
}

