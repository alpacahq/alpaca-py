# FinRL Actions Endpoints

All FinRL endpoints are part of a FastAPI service that wraps a reinforcement-learning engine. Except for `/healthz`, every endpoint requires a valid API key in the `X-API-Key` header. For `POST` endpoints, the `Content-Type` header must be set to `application/json`.

## 1. Health Check

```
GET /healthz
```

- **Authentication:** None.
- **Description:** Returns a simple JSON object indicating the service status.
- **Response Example:**
  ```json
  { "status": "ok" }
  ```

## 2. Train

```
POST /train
```

- **Authentication:** `X-API-Key` header required.
- **Mode:** Local or Remote.
- **Headers:**
  - `Content-Type: application/json`
  - `X-API-Key: <API key>`
- **Local Payload:**
  ```json
  {
    "symbols": ["AAPL", "MSFT"],
    "start": "2020-01-01",
    "end": "2025-01-01",
    "config_version": "ppo_default",
    "timesteps": 10000,
    "stop_distance": 0.02,
    "pullback_threshold": 0.01,
    "entry_delay": 1,
    "save_params": true
  }
  ```
  - `symbols` **required**. A non-empty array of ticker symbols triggers local mode.
  - `start` and `end` specify the training window in `YYYY-MM-DD` format.
  - `config_version`, `timesteps`, `stop_distance`, `pullback_threshold` and `entry_delay` are optional hyperparameters.
  - `save_params` indicates whether to persist model weights to the journaling service (requires `JOURNAL_STORAGE_BASE_URL` and `JOURNAL_API_KEY` set in the FinRL service).
- **Remote Payload:**
  ```json
  {
    "journal_data": [
      {
        "symbol": "AAPL",
        "side": "long",
        "entry_time": "2025-08-28T09:30:00Z",
        "exit_time": "2025-08-28T10:00:00Z",
        "entry_price": 180.50,
        "exit_price": 182.00,
        "stop_price": 178.00,
        "tp_price": 185.00,
        "R_multiple": 1.2
      }
    ],
    "save_params": true
  }
  ```
  - `journal_data` triggers remote mode. It is an array of historical trade records used to derive heuristics.
- **Local Response:**
  ```json
  { "job_id": "abc123" }
  ```
  The job runs asynchronously and must be polled via `/status/{job_id}`.
- **Remote Response:**
  ```json
  {
    "metrics": { "sharpe": 0.99, "cumulative_return": 0.25, "max_drawdown": -0.07, "win_rate": 0.52 },
    "heuristics": {...}
  }
  ```
  Immediate metrics are returned; no job ID is generated.

## 3. Status (local mode only)

```
GET /status/{job_id}
```

- **Authentication:** `X-API-Key` header required.
- **Parameters:** `job_id` (path) – the identifier returned by `/train` or `/backtest` in local mode.
- **Response:**
  ```json
  {
    "status": "running" | "completed" | "error",
    "result": {
      /* training or backtest metrics and model details when completed */
    }
  }
  ```
- **Mode:** Only valid when local mode was used. Remote mode does not create background jobs.

## 4. Predict

```
GET /predict?symbol=AAPL&start=2025-09-01&end=2025-09-20&version=latest
```

- **Authentication:** `X-API-Key` header required.
- **Mode:** Local or Remote.
- **Query Parameters:**
  - `symbol` **required** – ticker symbol for the prediction.
  - `start` and `end` – date window for the walk-forward backtest in `YYYY-MM-DD` format.
  - `version` – model version identifier. Use `latest` to fetch the most recently saved parameters.
- **Local Response:**
  ```json
  {
    "trade": {
      "entry": {"date": "2025-09-02", "price": 230.92},
      "exit": {"date": "2025-09-19", "price": 245.69}
    },
    "metrics": {
      "total_reward": 14.45,
      "sharpe": 0.99,
      "win_rate": 0.525,
      "steps": 223
    }
  }
  ```
- **Remote Response:**
  ```json
  {
    "metrics": {
      "total_reward": ..., 
      "sharpe": ..., 
      "win_rate": ...
    }
  }
  ```
  When remote mode is active, the service fetches the latest parameter blob from the journaling service and computes the metrics. No trade path is returned.

## 5. Backtest

```
POST /backtest
```

- **Authentication:** `X-API-Key` header required.
- **Mode:** Local or Remote.
- **Headers:** `Content-Type: application/json`
- **Payload:**
  ```json
  {
    "symbol": "AAPL",
    "start": "2020-01-01",
    "end": "2025-01-01",
    "version": "latest"
  }
  ```
- **Local Response:** `{ "job_id": "backtest123" }` – asynchronous job.
- **Remote Response:** Immediate metrics similar to the remote `/predict` call.

## 6. Signal (local mode only)

```
GET /signal?symbol=AAPL&version=latest&interval=1h
```

- **Authentication:** `X-API-Key` header required.
- **Mode:** Local only.
- **Query Parameters:**
  - `symbol` – ticker to generate a signal for.
  - `version` – model version, typically `latest`.
  - `interval` – bar interval for the signal (e.g. `1h`, `15m`).
- **Response:**
  ```json
  { "side": "buy" | "sell" | "none", "confidence": 0.5 }
  ```
  A quick recommendation and a confidence score between 0 and 1.

## 7. Risk (local mode only)

```
GET /risk?symbol=AAPL&start=2025-01-01&end=2025-09-20&interval=1d
```

- **Authentication:** `X-API-Key` header required.
- **Mode:** Local only.
- **Query Parameters:**
  - `symbol` – ticker symbol.
  - `start` and `end` – date range.
  - `interval` – bar interval (e.g. `1d`).
- **Response:**
  ```json
  { "vix": 15.0, "volatility": 0.2, "turbulence": 0.1, "risk_level": "low" }
  ```

## 8. Batch Training

```
POST /runAll
```

- **Authentication:** `X-API-Key` header required.
- **Mode:** Local only.
- **Headers:** `Content-Type: application/json`
- **Payload:**
  ```json
  { "symbols": ["AAPL", "MSFT", "GOOGL"] }
  ```
- **Response:**
  ```json
  { "job_id": "batch_job_id" }
  ```
  Poll each symbol’s job via `/status/{job_id}`.

## 9. Job Proxy (remote mode only)

```
GET /jobs/{job_id}
```

- **Authentication:** `X-API-Key` header required.
- **Mode:** Remote only.
- **Parameters:** `job_id` – job identifier created by the upstream FinRL API.
- **Response:** 
  ```json
  { "status": "running" | "completed" | "error", "result": { ... } }
  ```

## 10. Order (not supported)

```
POST /order
```

- **Authentication:** `X-API-Key` header required.
- **Headers:** `Content-Type: application/json`
- **Payload:**
  ```json
  {
    "symbol": "AAPL",
    "side": "buy",
    "qty": 10,
    "type": "market",
    "time_in_force": "day",
    "client_order_id": "optional-id"
  }
  ```
- **Response:** `{}` (empty object). 
- **Note:** This endpoint is currently a stub and should never be used for live orders. Use Alpaca actions instead.

## Required Environment for Local Mode

- `USE_LOCAL_FINRL` must be set to `true` for local training, prediction, backtest, signal and risk.
- To save or load parameter blobs, set `JOURNAL_STORAGE_BASE_URL` and `JOURNAL_API_KEY` in the environment. These settings enable the service to persist model weights and retrieve them for remote mode.
