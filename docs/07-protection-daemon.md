# Protection Daemon Logic

## Trailing
- Trigger: near +1R or threshold (+2–3%).
- Method: trail by fixed % or ATR multiple; never widen.
- Steps: move to breakeven at +1R → tighten at +5%, +10% gains.
- Update cadence: no more than once per bar or on milestones.
- Implementation: modify stop or cancel+recreate; journal adjustment.

## Time-based exits
- Intraday strategies: flat before close.
- Swing: max holding window per strategy; close on expiry.
- Stagnation rule (optional): exit if no progress after N days.
- Weekends/holidays: user-configurable; default flat if specified.

## Event risk
- Earnings: close before event unless user overrides.
- Macro events: tighten or reduce/exit ahead of high-impact releases.
- Breaking news: severity filter; alert, tighten, or exit if adverse.
- Always journal reason: exit_reason = time_exit or event_exit.

## Overrides
- User may disable trailing/time/event rules per trade.
- Daemon respects overrides; journals the decision.

## Notifications
- On exits or major adjustments, notify + journal.
- Minor trailing updates can be silent but are always logged.

