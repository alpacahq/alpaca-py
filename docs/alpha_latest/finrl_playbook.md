# FinRL Playbook

## Purpose

This playbook describes how the trading assistant should use the **FinRL actions** service. FinRL is a reinforcement-learning engine that can train models, backtest them, and produce signals and risk diagnostics. The service never executes trades. Use it only when the user explicitly opts in.

## When to Use FinRL

- **Training** – Build a trading model using historical OHLCV data and optional alpha signals. 
- **Backtesting** – Evaluate the performance of a trained model on a historical window.
- **Prediction** – Generate a walk-forward backtest with entries and exits for a specific symbol and window.
- **Signal** – Produce a quick buy/sell recommendation with a confidence score (local mode only).
- **Risk** – Compute simple risk metrics such as VIX, realised volatility and turbulence (local mode only).
- **Batch training** – Train multiple symbols in parallel.

Only call FinRL when the user has explicitly **consented** to reinforcement-learning analysis.

## Consent Gate

Before calling any FinRL endpoint other than `/healthz`, confirm that the user wants to run an RL training, backtest, prediction, signal, risk analysis or batch job. Do not call FinRL implicitly. Use FinRL outputs only as evidence to support strategy decisions; never use them to trigger an order.

## Local vs. Remote Modes

FinRL operates in two mutually exclusive modes:

| Mode   | Trigger                         | Endpoints available                     | Behaviour                                                  | Use cases |
|-------|---------------------------------|-----------------------------------------|------------------------------------------------------------|----------|
| **Local** | A JSON body containing a `symbols` array in `/train` or an explicit call to `/predict`, `/backtest`, `/signal`, `/risk`, or `/runAll` | `/train`, `/status`, `/predict`, `/backtest`, `/signal`, `/risk`, `/runAll` | Uses a local reinforcement-learning engine. Training returns a `job_id` and runs asynchronously. Predictions, backtests and signals operate on saved models. Risk metrics are computed from local data. Batch training returns a job ID and processes symbols sequentially. | When `USE_LOCAL_FINRL=true` and the user wants to train locally or run detailed backtests and risk diagnostics. |
| **Remote** | A JSON body containing a `journal_data` array in `/train` or the absence of `symbols` when calling `/predict` or `/backtest` | `/train`, `/predict`, `/backtest`, `/jobs` | Proxies requests to the upstream FinRL API. Training and backtesting return immediate metrics instead of a job ID. Predictions fetch the most recent saved parameters from the journaling service. Only training and backtesting are supported; risk and signal are not available. | When local training is disabled or remote infrastructure is preferred for quick heuristics and backtests. |

FinRL does **not** allow mixed mode. For a given session, choose either local or remote training based on the parameters provided.

## Staleness and TTL

- **Model training**: Treat a trained model as valid only for the session in which it was created. For backtests or predictions, regenerate models if they are older than **30 calendar days**.
- **Signals and risk metrics**: Consider signals or risk outputs valid only for the current trading session. They must be recalculated at the start of each session.
- **Metrics and predictions**: FinRL metrics and predictions rely on underlying market data. When used in a decision, verify that the underlying data window ends within **1 trading day** of the current date. Otherwise, re-run the call.

## Non-Goals

- **Order execution**: Do **not** use FinRL to place orders. The `/order` endpoint is a stub for development and should never be called by the trading assistant. Use the Alpaca actions for placing, modifying, or cancelling orders.
- **Real-time quotes**: FinRL is not a quote or market-data service. Use Finnhub actions to obtain quotes, candles and indicators.
- **Classifier gating**: The FinRL classifier is not a gating mechanism. Use the Alpha Classifier for rating setups; use FinRL outputs as supplementary evidence.
- **Background tasks**: The assistant must never poll FinRL jobs in the background. Only call `/status/{job_id}` or `/jobs/{job_id}` when the user explicitly asks for status.

## Typical Workflow

1. **User request** – The user explicitly requests a reinforcement-learning operation, e.g. “Backtest AAPL from 2020–2025 using FinRL”.
2. **Plan** – Decide whether the request requires local or remote mode based on the presence of `symbols` vs `journal_data`.
3. **Consent** – Confirm with the user before training/backtesting/predicting using FinRL.
4. **Invoke** – Call the appropriate FinRL endpoint with required headers and parameters.
5. **Await result** – For local training or batch jobs, store the returned `job_id` in the journal and tell the user to check status later. For remote operations, wait for the immediate metrics.
6. **Interpret** – Summarise the metrics concisely in plain language and record them in the journal using the `finrl_metrics` schema.
7. **Act** – Use FinRL results as one piece of evidence. Only place trades if the setup aligns with the defined strategies and passes the Alpha Classifier gate.
