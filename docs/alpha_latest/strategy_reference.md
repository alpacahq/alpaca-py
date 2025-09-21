# Strategy Reference (Alpha Latest)

Purpose: deterministic, machine-readable playbook for the trading assistant. These rules **do not** place orders by themselves; they qualify setups for simulation (DRY_RUN) and, if confirmed by the user and all gates pass, for live execution via Alpaca.

---

## Shared Indicators & Definitions

- **PIR** (Position in Range): `(Last - Low) / (High - Low) * 100`. If `High == Low`, treat as undefined and skip the play.
- **RVOL** (Relative Volume): `current volume / average volume` (same resolution window as the signal under test).
- **ATR(N)**: Average True Range over N sessions (default 14).
- **RSI(14)**: Standard Wilder RSI.
- **Trend filters**:
  - `> SMA50` (above 50‑day simple moving average) implies intermediate uptrend.
  - `> SMA200` implies long‑term uptrend.
- **Levels**: Prior swing highs/lows, daily/weekly range edges, and VWAP.

**Pre‑conditions (apply to all plays):**
**Classifier gate (embedded):**
- Proceed only if `score ≥ 0.70` **and** `label ∈ {StrongBuy, Buy}`.
- If gate fails: **PASS** (no simulate/live) and create a `watchlist_entry {strategy, symbol, reason, added_ts}`.
- Re‑check when RVOL/PIR/news materially change.

1) **Earnings proximity**: block new swing entries if next earnings < **48h**; if 48–72h and user insists, size at **0.5×**.
2) **Quote staleness**: use price only if provider timestamp age ≤ **10s**; otherwise refresh before sizing/limits.
3) **EXT rules**: no brackets/trailing in extended hours; use **limit + Day + extended** only.
4) **Risk skeleton**: per‑trade risk ≤ **2% equity** (default); per‑name exposure ≤ **20%**; daily loss halt **−5%**.

---

## Plays

### 1) Breakout
**Setup:** Price resolves **above** a well‑defined range/resistance.  
**Minimums:** `RVOL ≥ 1.5`, `PIR ≥ 80`, `> SMA50` (ideally > VWAP).

**Entry:**  
- Primary: Break of range high on confirming volume.  
- Alternate: First pullback to the broken level or VWAP after the break.

**Stops:**  
- Below the breakout level **or** `1.0–1.5 × ATR` below entry (choose tighter of the two).

**Targets:**  
- Measured move from range height **or** prior swing high.  
- Begin trailing **after +1R**.

**Disqualifiers:**  
- Extension **> 3× ATR** from the base at the moment of signal (avoid chasing).

---

### 2) Pullback
**Setup:** Uptrend (`> SMA50` and preferably `> SMA200`) pulls back to a dynamic level.  
**Context:** `RSI 35–55`, `RVOL 0.8–1.2`.

**Entry:**  
- Reclaim of SMA20 / VWAP / prior breakout level **with uptick or bullish engulfing**.

**Stops:**  
- Under the swing low **or** `1 × ATR` (tighter prevails).

**Targets:**  
- Prior high **or** `1.5–2R`.  
- Trail under higher lows once > `+1R`.

**Disqualifiers:**  
- Loss of SMA50 on closing basis **and** failure to reclaim on the next bar.

---

### 3) Range Reversion
**Setup:** Horizontal support/resistance range; **mean‑reversion** bias.  
**Context:** `RVOL ≤ 1.2`, stable ATR; for longs, `PIR ≤ 20`.

**Entry (long):**  
- Near support with a clear reversal cue (hammer, engulfing, reclaim of level).

**Stops:**  
- Below the support zone.

**Targets:**  
- Range high; allow **scales** into strength.

**Disqualifiers:**  
- Range breaks **on volume**; switch bias or stand aside.

---

### 4) Catalyst / Momentum
**Setup:** Fresh **news** or **unusual flow** fuels an impulse move in an existing uptrend.  
**Minimums:** `RVOL ≥ 2`, `> SMA50`.

**Entry:**  
- Intraday **flag break**; may add on higher‑low flags while RVOL persists.

**Stops:**  
- `1–1.5 × ATR` under flag low.

**Targets:**  
- Prior high **or** `≥ 2R`.

**Disqualifiers:**  
- Extension > `3× ATR` from the last base; fading RVOL with failure to hold VWAP.

---

### 5) Gaps
**Gap‑and‑Go (long):**  
- **Gap ≥ 3%**, holds **above open/VWAP** with supportive RVOL.  
- **Entry:** High‑of‑day break.  
- **SL:** Below VWAP or opening range low.  
- **TP:** Gap projection or prior high.

**Gap‑Fill (long bias after failed go):**  
- If the stock **loses VWAP/open** with RVOL dropping, **wait for reclaim** before long.  
- Stops/targets mirror reclaim level logic.

---

### 6) Earnings (post‑event momentum)
**Setup:** Positive surprise + gap up + **hold above open/VWAP** with `RVOL ≥ 2`.  
**Entry:** First **pullback** after the hold.  
**SL:** Under pullback low.  
**TP:** Gap high, then measured move.

---

## Machine‑Readable Profiles (for deterministic checks)

> These JSON blocks encode minimums, entries, exits, and disqualifiers. They are **guidance** for the assistant’s structured outputs (e.g., `trade_preview`, `watchlist_entry`).

```json
{
  "strategies": [
    {
      "name": "breakout",
      "min": { "rvol_min": 1.5, "pir_min": 80, "above_sma50": true },
      "entry": [
        { "type": "level_break", "level": "range_high", "confirm": "volume_spike_or_hold_above" },
        { "type": "first_pullback", "to": "broken_level_or_vwap" }
      ],
      "risk": {
        "stop": { "rule": "tightest", "candidates": [
          { "type": "under_level", "ref": "range_high" },
          { "type": "atr_multiple", "value": 1.25 }
        ] }
      },
      "targets": [
        { "type": "measured_move", "from": "range", "to": "projection" },
        { "type": "prior_swing_high" }
      ],
      "management": [
        { "type": "trail_after_r", "r": 1.0 }
      ],
      "disqualifiers": [
        { "type": "extension_gt_atr_multiple", "value": 3.0, "ref": "base" }
      ]
    },
    {
      "name": "pullback",
      "min": { "trend": { "above_sma50": true, "above_sma200_preferred": true }, "rsi_range": [35, 55], "rvol_range": [0.8, 1.2] },
      "entry": [
        { "type": "reclaim_level", "level": "sma20_or_vwap_or_prior_breakout", "confirm": "uptick_or_bullish_engulf" }
      ],
      "risk": {
        "stop": { "rule": "tightest", "candidates": [
          { "type": "under_swing_low" },
          { "type": "atr_multiple", "value": 1.0 }
        ] }
      },
      "targets": [
        { "type": "prior_high" },
        { "type": "risk_multiple", "rr": 1.5 }
      ],
      "management": [
        { "type": "trail_on_higher_lows", "activate_after_r": 1.0 }
      ],
      "disqualifiers": [
        { "type": "close_below_sma50_and_no_reclaim_next_bar" }
      ]
    },
    {
      "name": "range_reversion",
      "min": { "rvol_max": 1.2, "atr_state": "stable", "pir_max_for_longs": 20 },
      "entry": [
        { "type": "reversal_at_level", "level": "support", "pattern": "hammer_or_engulf_or_reclaim" }
      ],
      "risk": { "stop": { "type": "under_level", "ref": "support" } },
      "targets": [ { "type": "range_high" } ],
      "management": [ { "type": "scale_out_into_strength" } ],
      "disqualifiers": [ { "type": "range_break_on_volume" } ]
    },
    {
      "name": "catalyst_momentum",
      "min": { "rvol_min": 2.0, "above_sma50": true, "catalyst_required": true },
      "entry": [
        { "type": "flag_break_intraday" },
        { "type": "add_on_higher_low_flags_while_rvol_persists" }
      ],
      "risk": { "stop": { "type": "atr_multiple_under_flag", "value": [1.0, 1.5] } },
      "targets": [ { "type": "prior_high" }, { "type": "risk_multiple", "rr": 2.0 } ],
      "disqualifiers": [
        { "type": "extension_gt_atr_multiple", "value": 3.0 },
        { "type": "lose_vwap_with_fading_rvol" }
      ]
    },
    {
      "name": "gap_and_go",
      "min": { "gap_pct_min": 3.0, "hold_above": "open_or_vwap", "rvol_support": true },
      "entry": [ { "type": "hod_break" } ],
      "risk": { "stop": { "rule": "tightest", "candidates": [
        { "type": "under_vwap" },
        { "type": "under_opening_range_low" }
      ] } },
      "targets": [ { "type": "gap_projection" }, { "type": "prior_high" } ]
    },
    {
      "name": "gap_fill_reclaim",
      "min": { "lost_vwap_or_open": true, "rvol_dropping": true },
      "entry": [ { "type": "reclaim_level_then_trigger", "level": "vwap_or_open" } ],
      "risk": { "stop": { "type": "under_reclaim_level" } },
      "targets": [ { "type": "range_mid_or_prior_high" } ]
    },
    {
      "name": "earnings_post_momentum",
      "min": { "surprise": "positive", "gap_direction": "up", "hold_above": "open_or_vwap", "rvol_min": 2.0 },
      "entry": [ { "type": "first_pullback_after_hold" } ],
      "risk": { "stop": { "type": "under_pullback_low" } },
      "targets": [ { "type": "gap_high" }, { "type": "measured_move" } ]
    }
  ]
}
```

---

## Watchlist Behavior

If a symbol **nearly** meets criteria but fails one or more minimums, **do not simulate or execute**. Instead:
- Add a `watchlist_entry` `{ strategy, symbol, reason, added_ts }`.
- On session open, score watchlist via Classifier (and optionally FinRL signal) and compare against balances/positions to surface the best opportunities.

---

## Session & Risk Integration (quick cues)

- **RTH defaults:** New entries use **limit @ validated last**, Day TIF, bracket `TP+SL` in RTH only.  
- **EXT defaults:** **Limit + Day + extended**, no bracket/trailing. Queue or adjust per user intent.  
- **Drift check:** If `|current - preview| / preview > 0.5%`, refresh preview and reconfirm.  
- **Idempotency:** Always set a unique `client_order_id` per intent; on timeout/5xx, **GET by client id before retry**.

---

## Notes on Data & Tools

- **Quotes & candles:** Finnhub actions for real‑time and historical.  
- **Orders & account/positions:** Alpaca actions.  
- **Classifier:** Feature set includes trend, RVOL, PIR, ATR, RSI, and news flags.  
- **FinRL (consent‑gated):** Training/backtesting/signals/risk inform strategy development; never execute orders.

---

## Examples (concise)

**Breakout (AAPL):**  
- Min checks: RVOL 1.8 ✓, PIR 86 ✓, >SMA50 ✓.  
- Entry: Break 198.50 on volume, or PB to 198.50/VWAP.  
- SL: 197.70 (under level) vs `1.2×ATR=1.10` → use 197.70 (tighter).  
- TP: Measured move from 194–198.5 (=4.5) → 203.0; trail after +1R.

**Pullback (MSFT):**  
- Min checks: `>SMA50/SMA200` ✓, RSI 44 ✓, RVOL 1.0 ✓.  
- Entry: Reclaim SMA20 with bullish engulf.  
- SL: Under swing low 416.  
- TP: Prior high 427 or `1.8R`; trail on higher lows > +1R.

---

## Implementation Hints

- Keep human text concise; produce a **`trade_preview` JSON** alongside human preview for any simulated plan.
- Default **per‑trade risk = 2% of equity** unless the user specifies otherwise.
- If **any** gate fails (classifier, earnings window, session rules, quote TTL, order validation), **fail closed** and provide the next precise step (e.g., add to watchlist, refresh quote, switch to RTH).
