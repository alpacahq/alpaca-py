# Watchlist Workflow
# (daily scan → classifier gate ≥0.70 → account fit → DRY_RUN; default per-trade risk 2%)
## Deterministic Shortlist Scoring (EV)
Score s = 0.40·Classifier + 0.20·Liquidity + 0.20·TriggerProximity + 0.20·PortfolioFit − ExposurePenalty

- Classifier: normalized [0,1] from model score (labels Neutral/Sell => 0).
- Liquidity: min(1, ADV / 1e7) × spread_fitness (tight=1, wide=0).
- TriggerProximity: 1 − min(1, |last − trigger| / ATR).
- PortfolioFit: 1 − |corr(symbol, book)| (prefer low correlation) and sector concentration < 25%.
- ExposurePenalty: 1 if per‑name exposure would exceed 20% or daily loss halt breached; else 0.

**Competes‑with‑holding rule:** If a new s exceeds any current position’s s by ≥0.15 and adding breaches exposure limits, recommend trim/rotate with rationale (which metric(s) drove the difference).
