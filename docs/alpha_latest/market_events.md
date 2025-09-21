# Market Events & Sessions Policy

**Scope:** US equities (NYSE/Nasdaq).

## Session States
- `RTH` — 09:30–16:00 Eastern.
- `EXT` — pre/post as supported by broker.
- `CLOSED`, `HALTED`.

## Rules
- **Blockers:** Do not place new entries when `CLOSED` or `HALTED`.
- **Pricing:** Prefer limit orders in fast tape; no market orders outside RTH.
- **EXT constraints:** limit + Day + extended only; **no bracket/trailing**.
- **Detection:** Use broker/exchange status from actions when available; otherwise derive from timestamp and weekday.
- **Holidays:** Maintain a holiday list in journal/config; if unknown, fail closed and ask to confirm session.
- **Queueing:** If user intends EXT but symbol/session not eligible, propose RTH queue or adjust.

## Earnings Proximity
- **Block new swing entries** if the next earnings event is within **< 48 hours**.
- **Size reduce to 0.5×** if earnings are **48–72 hours** away and user insists.
- **Post-earnings momentum:** Positive surprise + gap up + hold above open/VWAP with RVOL ≥ 2 → allow pullback entry; SL under pullback; TP to gap high then measured move.
- **Existing positions:** Manage risk; allow trims/tighten stops into earnings per plan.
- **Journal:** Note the earnings timestamp used and decision rationale.
