# FinRL Error Taxonomy and Remedies

This document enumerates the common error categories that may occur when using the FinRL actions and suggests corrective steps. The trading assistant should integrate these remedies into the error ladder.

## 1. Authentication Errors

- **Missing API key:** The request lacks an `X-API-Key` header.
  - *Remedy:* Attach the correct API key in the `X-API-Key` header. Without a valid key, all endpoints except `/healthz` will fail.
- **Invalid API key:** The provided API key is incorrect.
  - *Remedy:* Verify the key value in the GPT's configuration. If the key is expired or revoked, obtain a new key.

## 2. Input Validation Errors

- **Missing required fields:** The request body or query string lacks mandatory parameters, such as `symbols` in local training or `symbol` in prediction.
  - *Remedy:* Read the endpoint specification. Provide all required fields in the correct case and format (e.g. ISO dates for `start` and `end`). Retry with valid input.
- **Date range errors:** `end` precedes `start`, or dates are not in `YYYY-MM-DD` format.
  - *Remedy:* Swap the dates or correct the format. Reject invalid ranges and ask the user to provide a valid window.
- **Unsupported interval or version:** An invalid bar interval (`interval`), unsupported model version, or empty symbol list.
  - *Remedy:* Choose a valid interval (e.g. `1h`, `1d`) and use `"latest"` as the version unless a specific saved version exists.

## 3. Mode and Endpoint Mismatch

- **Local mode endpoint used with remote payload:** Supplying `journal_data` to an endpoint that only supports local mode (`/signal`, `/risk`) will fail.
- **Remote mode endpoint used with local payload:** Supplying `symbols` to `/jobs/{job_id}` or other remote-only endpoints.
- **Risk or Signal in remote mode:** `/risk` and `/signal` are unavailable in remote mode.
  - *Remedy:* Check whether `USE_LOCAL_FINRL` is true and ensure you are calling an endpoint supported in that mode. Do not request signal or risk metrics in remote mode.

## 4. Job Status Errors

- **Unknown job ID:** Calling `/status/{job_id}` or `/jobs/{job_id}` with an identifier that does not exist.
  - *Remedy:* Store the `job_id` returned by `/train` or `/backtest` in the journal. Verify that you are querying the correct job. If the job expired or was removed, retrain or backtest again.
- **Stalled job:** A job remains in the `"running"` state for an unusually long time.
  - *Remedy:* Inform the user that the job may have failed. Suggest retrying training or using remote mode. Do not auto-retry indefinitely.

## 5. Upstream Errors

- **Remote API unreachable:** The upstream FinRL API cannot be reached (network failure).
- **Internal server error:** The service returns a 5xx error due to an unexpected exception or resource exhaustion.
  - *Remedy:* Apply the error ladder: retry once after a short delay, then gracefully degrade. For example, if a training request fails, fall back to using the Alpha Classifier or historical indicators for analysis. Explain to the user that RL analysis is temporarily unavailable.

## 6. Journaling Errors

- **Missing journaling configuration:** `JOURNAL_STORAGE_BASE_URL` or `JOURNAL_API_KEY` are not set, preventing model parameters from being saved or retrieved.
- **Parameter blob not found:** Remote prediction requests a version that has not been saved or cannot be retrieved.
  - *Remedy:* Ensure journaling settings are configured. When saving parameters (`save_params=true`), check that the call succeeded. When retrieving a version, use `version=latest` or a known version ID present in the journal.

## 7. Unsupported or Deprecated Endpoints

- **/order endpoint:** Always returns an empty object and should not be used for order execution.
  - *Remedy:* Do not call `/order`. Use Alpaca actions (`order.create`, `order.modify`, `order.cancel`) for trading.
- **Unknown path or HTTP method:** Requesting an undefined endpoint or using a `GET` where a `POST` is required.
  - *Remedy:* Refer to the endpoint list and use the correct HTTP verb.

## 8. Consent Violations

- **No explicit user consent:** The GPT attempts to call FinRL without user confirmation.
  - *Remedy:* Before invoking FinRL, ask the user if they wish to perform a reinforcement-learning operation. If the user declines, skip the call and proceed with other analyses.

When an error occurs, follow the error ladder: identify the root cause, provide the user with the exact corrective step, retry only when appropriate, and avoid generic fixes. If the GPT cannot resolve the error with certainty, apologise briefly and ask the user to check their configuration or to try again later.
