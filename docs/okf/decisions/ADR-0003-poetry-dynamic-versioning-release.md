---
type: Architecture Decision
title: ADR-0003 Poetry build with dynamic versioning, released on version tags
description: The package version comes from the git tag at build time and publication is triggered by pushing a version tag.
status: accepted
date: unknown
deciders: []
supersedes: []
affects: [alpaca_py, ext_pypi]
allium: []
evidence: ["pyproject.toml", ".github/workflows/publish-pypi.yaml", ".github/workflows/ci.yaml", "alpaca/_version_resolve.py", "Makefile", "CONTRIBUTING.md"]
tags: [alpacahq, adr, generated]
timestamp: 2026-09-11T00:00:00+00:00
generated_by: claude-opus-5 / layered-docs 2026-09
source_commit: 48fd544334a595c53e386043cc9282824b1e9c58
source_branch: docs/layered-2026-09
generated_at: 2026-09-11T00:00:00+00:00
confidence: high
review_status: draft-needs-review
---

# ADR-0003 Poetry build with dynamic versioning, released on version tags

## Context

The package is distributed publicly and its version must match the released tag. Keeping a version number in `pyproject.toml` in step with tags by hand is error prone, and the repository is contributed to by outside forks (`CONTRIBUTING.md`).

## Decision

Build with poetry and derive the version from the git tag. The manifest carries `version = "0.0.0"` with the comment "placeholder for poetry-dynamic-versioning", enables the plugin, and declares the build backend as `poetry_dynamic_versioning.backend` with substitution into the `alpaca` package folder (`pyproject.toml`). Publication is triggered only by tags matching a version pattern, and the workflow runs the test suite before building and publishing with a stored token (`.github/workflows/publish-pypi.yaml`).

## Consequences

Version resolution needs runtime support in the package itself (`alpaca/_version_resolve.py`). Development installs report the placeholder version unless the plugin runs. The publish workflow pins the poetry version and the publish action, and includes a workaround for the container home directory used by the publish action, so the git checkout is trusted inside it (`.github/workflows/publish-pypi.yaml`). Pull-request CI runs lint, docs build and tests on Python 3.10 and 3.11 separately from publication (`.github/workflows/ci.yaml`), and a public-API breakage check can be run against a published release (`Makefile`).

## Alternatives considered

Not evidenced in the repository.
