# Live probe (paper/sandbox smoke tests)

Opt-in pytest suite that hits real Alpaca APIs to prove a method works after an SDK change.

Default `poetry run pytest` / CI **skips** these tests. Artifacts are written under `artifacts/live_probe/` (gitignored).

## Quick start

1. Copy `.env.example` to `.env` and fill credentials (or export the same env vars).
2. Prove one method you changed:

```bash
poetry run pytest tests/live -k get_account --run-live
```

Redacted **request + response** are printed to the console automatically (no `-s` needed). JSON artifacts are also written under `artifacts/live_probe/<timestamp>/`.

Use `--live-quiet` to suppress console dumps.

## Common commands

```bash
# list live tests
poetry run pytest tests/live --collect-only -q

# trading paper smokes
poetry run pytest tests/live/test_trading_rest.py --run-live

# data smokes
poetry run pytest tests/live/test_data_rest.py --run-live

# broker sandbox smokes
poetry run pytest tests/live/test_broker_rest.py --run-live

# streaming smokes (crypto quotes are reliable off-hours)
poetry run pytest tests/live/test_streaming.py --run-live
poetry run pytest tests/live -k crypto_data_stream --run-live

# alternate gate
ALPACA_RUN_LIVE=1 poetry run pytest tests/live -k get_clock
```

## Credentials

| Use | Variables |
|---|---|
| Trading + Market Data | `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY` |
| Broker | `ALPACA_BROKER_API_KEY`, `ALPACA_BROKER_API_SECRET` |

Env vars override values loaded from `.env`.

## Environments

| Area | Default | Override |
|---|---|---|
| Trading | paper | `ALPACA_TRADING_PAPER=false` for live trading API |
| Broker | sandbox | `ALPACA_BROKER_SANDBOX=false` for production broker API |
| Stream wait | 30s | `ALPACA_LIVE_STREAM_TIMEOUT` (seconds) |
| Option symbol | connect-only | `ALPACA_LIVE_OPTION_SYMBOL` (OCC) to require a quote |

## Safety

- Starter tests are **read-only**.
- Mutative tests (when added) must use `@pytest.mark.live_mutative` and require `--allow-mutative` in addition to `--run-live`.
- Missing credentials with `--run-live` fail fast (`pytest.UsageError`).

## Adding coverage

Add a normal pytest function in `tests/live/`, mark it `@pytest.mark.live`, and use `live_call` so failures are still recorded:

```python
@pytest.mark.live
def test_get_account(trading_client_live, live_call):
    account = live_call("get_account", trading_client_live.get_account)
    assert account is not None
```

Name the test after the method so `-k` targeting stays easy (`test_get_orders` → `-k get_orders`).

## Artifact shape

```json
{
  "id": "tests/live/test_trading_rest.py::test_get_account",
  "method": "get_account",
  "status_code": 200,
  "passed": true,
  "request": {
    "method": "GET",
    "url": "https://paper-api.alpaca.markets/v2/account",
    "headers": {"APCA-API-KEY-ID": "***REDACTED***"},
    "body": null
  },
  "response_body": {},
  "error": null
}
```

## Streaming probes

`tests/live/test_streaming.py` covers `TradingStream`, `StockDataStream`, `CryptoDataStream`, `OptionDataStream`, and `NewsDataStream`.

- Stock / crypto quotes **require ≥1 message** within the timeout.
- Trading + news prove **connect + auth + subscribe** (updates/news can be idle).
- Artifacts use `"method": "WS"` with captured `User-Agent` headers and a small message sample.

## Optional CI

Default PR CI should keep skipping these tests. A secrets-gated nightly or `workflow_dispatch` job can run the same suite later (`pytest tests/live --run-live`) without changing the test layout.
