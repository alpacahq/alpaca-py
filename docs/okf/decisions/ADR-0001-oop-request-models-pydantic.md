---
type: Architecture Decision
title: ADR-0001 Object-oriented request models validated with pydantic
description: Every SDK method takes a dedicated request object, and all models extend a validating pydantic base.
status: accepted
date: unknown
deciders: []
supersedes: []
affects: [alpaca_py, alpaca_py.rest_core, alpaca_py.trading_client, alpaca_py.broker_client, alpaca_py.market_data]
allium: []
evidence: ["README.md", "CONTRIBUTING.md", "alpaca/common/models.py", "alpaca/trading/requests.py", "alpaca/data/requests.py", "alpaca/broker/requests.py", "pyproject.toml"]
tags: [alpacahq, adr, generated]
timestamp: 2026-09-11T00:00:00+00:00
generated_by: claude-opus-5 / layered-docs 2026-09
source_commit: 48fd544334a595c53e386043cc9282824b1e9c58
source_branch: docs/layered-2026-09
generated_at: 2026-09-11T00:00:00+00:00
confidence: high
review_status: draft-needs-review
---

# ADR-0001 Object-oriented request models validated with pydantic

## Context

The README contrasts this SDK with the previous Python SDK and states that it "uses a more OOP approach to submitting requests compared to the previous SDK" (`README.md`, What is New section). The same section explains that request data arriving as JSON from an application can be parsed and validated through the request models, which matters because the SDK is embedded in user-facing trading applications.

## Decision

Each SDK method takes a dedicated request object rather than loose keyword arguments, and every model is a pydantic model. The README pairs request models with methods explicitly, for example `GetOrdersRequest` for `TradingClient.get_orders()` and `CryptoBarsRequest` for the crypto bars call (`README.md`). The contributing guide makes the rule binding for new code: new models "must extend the `alpaca.common.models.ValidateBaseModel` class and implement a pydantic validator if needed to ensure that models are always in a consistent state" (`CONTRIBUTING.md`, Models section).

## Consequences

The request surface is large and mirrored across packages: `alpaca/trading/requests.py`, `alpaca/broker/requests.py`, `alpaca/data/requests.py` and `alpaca/common/requests.py` all exist as separate modules. pydantic v2 is a hard runtime dependency (`pyproject.toml`). Validation errors surface at construction time in the caller rather than as API errors, and the SDK ships type information (`alpaca/py.typed` is included in the package, `pyproject.toml`). The breadth of the public model surface is also why a dedicated public-API breakage check exists (`tools/scripts/compare_api_breakage.py`, `Makefile`).

## Alternatives considered

The README names the predecessor SDK approach as the alternative that was moved away from, but the repository records no discussion of other options.
