# Error Taxonomy (General)

Use this taxonomy to resolve issues deterministically.

## Categories
- **AUTH:** Missing/invalid credentials.
- **VALIDATION:** Missing/invalid params, bad dates/symbols.
- **SESSION:** Market closed/halts/EXT rules violated.
- **RATE_LIMIT:** 429 responses from providers.
- **RETRYABLE:** Transient 5xx/timeouts.
- **UNSUPPORTED:** Mode/endpoint not available.

## Remedies
- **AUTH:** Supply correct key; stop after failure.
- **VALIDATION:** Report exact field; suggest fix; do not guess.
- **SESSION:** Fail closed; propose RTH queue or refresh.
- **RATE_LIMIT:** Honor reset headers; jitter; single retry; no fan‑out.
- **RETRYABLE:** Retry once; then degrade (e.g., Classifier‑only).
- **UNSUPPORTED:** Suggest supported path (e.g., local vs remote).

## Ladder
1) Identify root cause → 2) Adjust if certain → 3) Retry once if allowed → 4) PASS with precise next step.
