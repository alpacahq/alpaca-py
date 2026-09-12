---
type: Architecture Decision
title: ADR-0002 One client class per API product and asset class
description: The SDK exposes separate client classes per API product and per asset class instead of a single facade.
status: accepted
date: unknown
deciders: []
supersedes: []
affects: [alpaca_py, alpaca_py.trading_client, alpaca_py.broker_client, alpaca_py.market_data, alpaca_py.rest_core]
allium: []
evidence: ["README.md", "alpaca/trading/client.py", "alpaca/broker/client.py", "alpaca/data/historical/", "alpaca/data/live/", "alpaca/common/rest.py", "alpaca/common/enums.py"]
tags: [alpacahq, adr, generated]
timestamp: 2026-09-11T00:00:00+00:00
generated_by: claude-opus-5 / layered-docs 2026-09
source_commit: 48fd544334a595c53e386043cc9282824b1e9c58
source_branch: docs/layered-2026-09
generated_at: 2026-09-11T00:00:00+00:00
confidence: high
review_status: draft-needs-review
---

# ADR-0002 One client class per API product and asset class

## Context

Alpaca offers several API products on distinct hosts, with distinct credentials: trading and market data keys on one side and broker keys on the other, each with a sandbox or paper variant (`README.md`, API Keys section; `alpaca/common/enums.py` base URL values). The README states plainly that the SDK "has a lot of client classes. There is a client for each API and even asset class specific clients" (`README.md`, Many Clients section).

## Decision

Expose one client per API product and, for market data, one per asset class and per delivery mode, rather than a single facade object. The README lists `BrokerClient` for the Broker API, `TradingClient` for the Trading API, and for Market Data the historical clients together with the streaming clients. This is reflected in the package layout: `alpaca/broker/client.py`, `alpaca/trading/client.py`, `alpaca/data/historical/` with one module per asset class, and `alpaca/data/live/` with the streaming counterparts. Common concerns are pushed down into an abstract base rather than duplicated: `alpaca/common/rest.py` holds credential validation, base URL selection, API versioning, pagination and retry.

## Consequences

Callers must pick and choose clients for their use case, which the README acknowledges directly. Credentials, sandbox selection and retry policy are configured per client instance (`alpaca/common/rest.py` constructor). Some data clients work without credentials at all, which the README demonstrates for crypto bars and news. The documentation site mirrors the same split, with one reference tree per product (`docs/api_reference/broker/`, `docs/api_reference/data/`, `docs/trading.rst`).

## Alternatives considered

Not evidenced in the repository.
