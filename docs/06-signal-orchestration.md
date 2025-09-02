# Signal Generation & Orchestration

## Inputs
- Watchlists.
- Finnhub: quotes, candles, indicators, news/sentiment, peers, profile2, calendars.
- FinRL: /predict tuned thresholds (per strategy/profile from prior /train).
- Journal segments: strategy_card, market_regime_tag, time-of-day.

## Process
1) Fetch /predict for active strategy segment.
2) Scan symbols with Finnhub:
   - Pullback: RSI rising from <30, reclaim prior high, above rising 50-DMA.
   - Breakout: close > resistance with ≥1.5x volume.
   - Breakdown short: close < support with volume; failed retests.
   - Range: reversal at extremes.
   - News: post-spike reclaim/fail levels with sentiment check.
3) Cross-check:
   - News veto, structural trend, liquidity/volatility thresholds.
   - FinRL thresholds gate entries (stop_distance, entry_delay).
4) Compute R/R and sizing; drop ideas <2:1 unless justified.
5) Group by symbol; merge congruent signals (AI + technical).
6) Prioritize by confidence, structure quality, liquidity, and portfolio fit.
7) Present concise proposals; await Confirm.
8) Journal “signal”; on confirm, place and journal “trade_open”.

## Segmented training loop
- After closes: append to journal → /train per segment (save_params=true) → refresh /predict before next scans.

