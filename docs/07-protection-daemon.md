version: 2025-09-03
status: canonical
scope: risk-protection
contracts:
  limits:
    max_position_pct: 10
    max_daily_loss_pct: 3
    max_leverage: 2
    concentration_pct: 30
    circuit_breakers: ["halted_symbol","extreme_gap"]
    earnings_hold: "forbid"
  evaluate:
    input: {account, positions[], pnl_day, orders[]}
    output: {pass|fail, breaches:[{rule, current, limit}], fixes:[{action, min_change}]}
actions:
  after_fill:
    - "ensure OCO exists"
    - "at >= +1R: consider convert SL->trailing"
    - "stale swing < +0.5R past window: tighten to breakeven or exit"
    - "event risk: before earnings, close or refuse new swing unless override token present"
invariants:
  - journal every adjustment with reason tag
  - smallest-change fix first
router:
  node: risk_check
  triggers: ["risk","limits","exposure","killswitch","protection","earnings"]
  prechecks: []
tests:
  smoke:
    - "risk check now" -> "pass/fail with breaches"
    - "earnings in 2 days" -> "propose close or deny new swing without override"
changelog:
  - 2025-09-03: default 'no swing through earnings'; add explicit override token
