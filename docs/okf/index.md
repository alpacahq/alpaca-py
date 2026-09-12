# Alpaca-py — knowledge bundle (OKF)

Generated draft (layered-docs 2026-09) — review required. Concept id = path without `.md`.

- [system](system.md) — System: the official Python SDK for the Alpaca Trading, Broker and Market Data APIs.
- [decisions/ADR-0001-oop-request-models-pydantic](decisions/ADR-0001-oop-request-models-pydantic.md) — Architecture Decision: every method takes a dedicated pydantic-validated request object.
- [decisions/ADR-0002-client-per-api-product](decisions/ADR-0002-client-per-api-product.md) — Architecture Decision: one client class per API product and asset class over a shared REST core.
- [decisions/ADR-0003-poetry-dynamic-versioning-release](decisions/ADR-0003-poetry-dynamic-versioning-release.md) — Architecture Decision: poetry build with tag-derived versions, published on version tags.
- [decisions/ADR-0004-sphinx-docs-container](decisions/ADR-0004-sphinx-docs-container.md) — Architecture Decision: the API reference is a Sphinx site served from an nginx image.
