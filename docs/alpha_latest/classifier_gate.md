# Classifier Gate

**Purpose:** Deterministic gating of trade setups before simulation or execution.

- **Threshold:** Proceed only if `score ≥ 0.70`.
- **Labels:** Accept if `label ∈ {StrongBuy, Buy}`; otherwise **PASS**.
- **Action on fail:** Do not simulate or trade. Create a `watchlist_entry` with `{strategy, symbol, reason, added_ts}`.
- **Re-check:** If the setup changes materially (RVOL, PIR, news), re-run the classifier and re-evaluate.
- **Journal:** Record the gate decision and inputs in the journal entry.
