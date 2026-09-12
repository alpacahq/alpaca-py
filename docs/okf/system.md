---
type: System
title: Alpaca-py
description: The official Python SDK for the Alpaca Trading, Broker and Market Data APIs, for developers building trading and brokerage applications.
resource: likec4://alpacahq/alpaca_py
tags: [alpacahq, sdk, python, generated]
status: active
owners: ["@hiohiohio", "@AlexandrosKyriakakis", "@carlostasada", "@daniil-alpaca"]
timestamp: 2026-09-11T00:00:00+00:00
generated_by: claude-opus-5 / layered-docs 2026-09
source_commit: 48fd544334a595c53e386043cc9282824b1e9c58
source_branch: docs/layered-2026-09
generated_at: 2026-09-11T00:00:00+00:00
confidence: medium
review_status: draft-needs-review
links:
  repository: https://github.com/alpacahq/alpaca-py
  architecture: ../architecture/alpaca_py.c4
---

# Alpaca-py

## Purpose

Alpaca-py is the official Python client library for the Alpaca API products. It exposes the REST, WebSocket and SSE endpoints as typed client classes so that application developers can stream market data, place orders, and operate brokerage accounts without writing HTTP plumbing (`README.md`, `pyproject.toml`). The package description is "The Official Python SDK for Alpaca APIs" and it is published under Apache-2.0 (`pyproject.toml`, `LICENSE`).

The audience is external and internal developers building algorithmic trading strategies, investing apps and full brokerage experiences (`README.md` Usage section; `examples/` contains stock, options and crypto sample projects and notebooks). It is a library, not a running service; the only deployable artefact in the repository is the documentation site image (`Dockerfile`, `cloudbuild.yaml`).

## Capabilities

- Trading API access: orders, positions, assets, account and trade-update streaming — evidence: `alpaca/trading/client.py`, `alpaca/trading/stream.py`, `alpaca/trading/requests.py`
- Broker API access: accounts, funding, journals, documents, rebalancing, broker-side trading — evidence: `alpaca/broker/client.py`, `alpaca/broker/models/`, `alpaca/broker/requests.py`
- Market data: historical stocks, options, crypto, news, screener and corporate actions — evidence: `alpaca/data/historical/`
- Live market data streaming over WebSocket with msgpack framing and reconnect handling — evidence: `alpaca/data/live/websocket.py`, `tests/test_streaming_reconnect_issues.py`
- Request and response validation through pydantic models, with a shared validating base model — evidence: `alpaca/common/models.py`, `CONTRIBUTING.md` Models section
- Pagination, retry on HTTP 429 and 504, and credential handling shared across all clients — evidence: `alpaca/common/rest.py`, `alpaca/common/constants.py`
- Hand-maintained Sphinx API reference built from docstrings (autodoc), published as a static site — evidence: `docs/api_reference/` (one hand-written page per module), `docs/conf.py` (autodoc, napoleon, enum_tools.autoenum; no autosummary or apidoc step), `docs/Makefile`, `tools/scripts/generate-docs.sh`
- Public API breakage check against a published release — evidence: `Makefile` check-api-breakage goal, `tools/scripts/compare_api_breakage.py`

## Interfaces

**Inbound:** a Python import surface only. The clients named in `README.md` are `BrokerClient`, `TradingClient`, `StockHistoricalDataClient`, `CryptoHistoricalDataClient`, `NewsClient`, `OptionHistoricalDataClient`, `StockDataStream`, `CryptoDataStream`, `NewsDataStream` and `OptionDataStream` (`alpaca/trading/client.py`, `alpaca/broker/client.py`, `alpaca/data/historical/`, `alpaca/data/live/`). No HTTP server or CLI entrypoint is declared in `pyproject.toml`. The documentation container serves static HTML on nginx (`Dockerfile`).

**Outbound:** HTTPS, WebSocket and server-sent-event calls to the Alpaca trading, paper-trading, broker and market-data hosts. The SSE surface is opened by the Broker client itself, which sets `Accept: text/event-stream` and wraps the streamed response in `sseclient.SSEClient` (`alpaca/broker/client.py`, five event-stream methods, e.g. line 1893). The base URLs are enumerated in `alpaca/common/enums.py` and used by `alpaca/common/rest.py`, `alpaca/trading/stream.py` and `alpaca/data/live/websocket.py`. The build publishes the package to the Python package index (`.github/workflows/publish-pypi.yaml`).

## Dependencies

- requests, websockets, msgpack, sseclient-py — transport for REST, streaming and server-sent events — evidence `pyproject.toml`
- pydantic v2 — model and request validation — evidence `pyproject.toml`, `CONTRIBUTING.md`
- pandas, pytz — dataframe conversion of market data and timezone handling — evidence `pyproject.toml`, `alpaca/data/models/`
- poetry with poetry-dynamic-versioning — build and version resolution — evidence `pyproject.toml`, `alpaca/_version_resolve.py`
- Sphinx, furo, sphinx-copybutton, enum-tools, sphinx-toolbox — documentation build — evidence `pyproject.toml` dev group, `docs/`
- GitHub-hosted workflows for continuous integration, the documentation build and the tag-triggered release — evidence `.github/workflows/ci.yaml`, `.github/workflows/publish-pypi.yaml`, `.github/workflows/stale.yml`
- Google Cloud Build and Container Registry, and a Kubernetes deployment, for the documentation image — evidence `cloudbuild.yaml`
- AWS Lambda, DynamoDB and the Serverless Framework — used by one bundled example project only, not by the SDK package — evidence `examples/stocks/lbr-anti-setup-trading-bot/serverless.yml`

## Data & storage

The SDK owns no datastore. It holds credentials in memory on each client instance and keeps one requests.Session per client (`alpaca/common/rest.py`). Market data responses are mapped into pydantic models and optionally into pandas dataframes (`alpaca/data/models/`, `alpaca/data/mappings.py`). Credentials are supplied by the caller as API key and secret, or an OAuth token, and the example environment file names the variables without values (`.env.example`).

## Operations

The library is installed with poetry (`Makefile` install goal) and released by pushing a version tag, which triggers the publish workflow (`.github/workflows/publish-pypi.yaml`). Continuous integration runs black lint checks, the documentation build and pytest on Python 3.10 and 3.11 (`.github/workflows/ci.yaml`). Pre-commit hooks are configured in `.pre-commit-config.yaml`. The multi-stage `Dockerfile` builds the Sphinx HTML and serves it from nginx; `cloudbuild.yaml` builds and pushes that image and, when the `_KUBE_*` substitutions and a service-account token are supplied by the trigger, sets the image (on tags only) and restarts the Kubernetes deployment, selecting a staging token on the default branch and a production token on tags; with any of those values empty the whole kubectl step is skipped (`cloudbuild.yaml` lines 62-67). No Terraform, Helm chart or compose file is present in the repository, so the deployment topology beyond those Cloud Build steps is not evidenced here.

## Behaviour (Allium)

none — no Allium specification files exist in this repository (checked with git ls-files) and no accepted spec is recorded for it.

## Decisions

- [ADR-0001 Object-oriented request models validated with pydantic](decisions/ADR-0001-oop-request-models-pydantic.md)
- [ADR-0002 One client class per API product and asset class](decisions/ADR-0002-client-per-api-product.md)
- [ADR-0003 Poetry build with dynamic versioning, released on version tags](decisions/ADR-0003-poetry-dynamic-versioning-release.md)
- [ADR-0004 Documentation shipped as a Sphinx site in an nginx image](decisions/ADR-0004-sphinx-docs-container.md)

## Evidence

- `README.md`, `CONTRIBUTING.md`, `LICENSE`, `CODEOWNERS`
- `pyproject.toml`, `poetry.lock`, `Makefile`, `.pre-commit-config.yaml`, `.env.example`
- `Dockerfile`, `cloudbuild.yaml`
- `.github/workflows/ci.yaml`, `.github/workflows/publish-pypi.yaml`, `.github/workflows/stale.yml`
- `alpaca/common/rest.py`, `alpaca/common/constants.py`, `alpaca/common/enums.py`, `alpaca/common/models.py`
- `alpaca/trading/client.py`, `alpaca/trading/stream.py`, `alpaca/broker/client.py`, `alpaca/data/historical/`, `alpaca/data/live/websocket.py`
- `docs/Makefile`, `docs/api_reference/`, `tools/scripts/compare_api_breakage.py`
- `examples/stocks/lbr-anti-setup-trading-bot/serverless.yml`

## Open questions

- Unverified: which environment the documentation Kubernetes deployment actually runs in. `cloudbuild.yaml` reads the cluster, namespace and deployment name from substitution variables that are not defined in the repository. Confidence: low.
- Unverified: whether the repository is the sole source of the published package, or whether release tags are cut elsewhere. Only two commits are present in this clone, so the commit history could not be mined for decisions. Confidence: low.
- Unverified: ownership beyond the `CODEOWNERS` handles; no team name is stated in the repository. Confidence: low.
- Unverified: the external id for the Alpaca API hosts. The org external dictionary has no entry for the first-party API surface, so a new id (`ext_alpaca_api`) was declared for this model and must be reconciled at the central merge. Confidence: low.
- Unverified: the external id for the package index. The org external dictionary has no entry for it either, so a new id (`ext_pypi`) was declared for this model and must be reconciled at the central merge. Confidence: low.
- The four Python code modules (`rest_core`, `trading_client`, `broker_client`, `market_data`) are modelled as LikeC4 containers for readability, but they ship as one wheel (`pyproject.toml` `packages = [{ include = "alpaca" }]`) and are not independently deployable; only `docs_site` is a separately built and deployed artefact (`Dockerfile`, `cloudbuild.yaml`). A reviewer may prefer them re-levelled as components. Confidence: low on the level assignment.
- Unverified: whether the `examples/` tree's Serverless/AWS deployment is operated by this org at all. `examples/stocks/lbr-anti-setup-trading-bot/serverless.yml` declares a third-party Serverless account, so it is recorded here as an example-only dependency and is deliberately not modelled in the architecture. Confidence: low.
