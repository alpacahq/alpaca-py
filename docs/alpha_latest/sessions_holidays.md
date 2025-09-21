# Sessions & Holidays Policy

**Scope:** US equities (NYSE/Nasdaq).

- **Session states:** `RTH` (09:30–16:00 Eastern), `EXT` (pre/post as supported by broker), `CLOSED`, `HALTED`.
- **Blockers:** Do not place new entries when `CLOSED` or `HALTED`.
- **Pricing:** Prefer limit orders in fast tape; no market orders outside RTH.
- **Detection:** Use broker/exchange status from connected actions when available; otherwise derive from timestamp and weekday.
- **Holidays:** Maintain a holiday list in journal/config; if unknown, fail closed and ask to confirm session.
- **Queueing:** If user intends EXT but symbol/session not eligible, propose RTH queue or adjust.
