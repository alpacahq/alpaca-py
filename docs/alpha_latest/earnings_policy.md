# Earnings Proximity Policy

**Objective:** Reduce event risk around earnings.

- **Block new swing entries** if the next earnings event is within **< 48 hours**.
- **Reduce size (0.5x)** if earnings are **48–72 hours** away and user insists.
- **Post-earnings:** If positive surprise + gap up + holds above open/VWAP with RVOL ≥ 2, allow pullback entry; set `SL` under pullback; stage TP to gap high then measured move.
- **Existing positions:** Manage risk; allow trims/tighten stops into earnings per plan.
- **Journal:** Note the earnings timestamp used and decision rationale.
