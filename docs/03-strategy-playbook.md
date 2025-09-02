# Strategy Playbook

## Conventions
- Confirmation: require reversal/continuation proof, not anticipation.
- Stops: below invalidation for longs; above invalidation for shorts; ATR-aware.
- Targets: structural (prior high/low, measured move) or trailing.
- Filters: market/sector trend, news risk, liquidity, volatility.
- R/R ≥ 2:1 default.

## Pullback Long
- Context: Uptrend; price above rising 50-DMA.
- Entry: After pullback, confirm with break of prior day high or bullish reversal (hammer/engulfing) + uptick in volume.
- Stop: Below swing low or 1.5×ATR below entry.
- Target: Prior swing high; partials allowed; then trail.
- Filters: Avoid if index/sector breaking down; skip near earnings unless plan says otherwise.

## Breakout Long
- Context: Base or range under resistance.
- Entry: Close above resistance with volume ≥1.5× 20-day avg.
- Stop: Below breakout level/base low or 1.5×ATR.
- Target: Measured move to next resistance; then trail if momentum persists.
- Filters: Avoid if >10% above 50-DMA at entry (overextended).

## Breakdown Short
- Context: Distribution under support; downtrend or failed retests.
- Entry: Close below support with rising volume or failed bounce to broken support.
- Stop: Above broken support or 1.5×ATR.
- Target: Next demand zone/measured move; trail when in profit.
- Filters: Shortable, borrow/locate allowed; avoid into major bullish catalysts.

## Range Trade
- Context: Sideways with clear support/resistance.
- Long near support on reversal; stop just below; target midline → resistance.
- Short near resistance on reversal; stop just above; target midline → support.
- Filters: Stand down if range resolves with strong breakout/breakdown.

## News Catalyst
- Enter after initial spike settles.
- Long: positive surprise; buy reclaim of spike high after pullback.
- Short: negative surprise; short loss of bounce low.
- Tight stops around event swing; partial profit early; tight trailing thereafter.
- Avoid holding through subsequent scheduled events unless planned.

## RL Blend (FinRL)
- Take signals only above confidence threshold.
- Require no hard contradiction from technicals/news.
- Use tuned stop_distance and entry_delay from /predict.
- Exit on opposite model signal or standard stops/targets.

## Trailing Rules (overview)
- Move to breakeven near +1R.
- Trail by % or ATR; tighten at +5%, +10%, etc.
- Never widen stops.

