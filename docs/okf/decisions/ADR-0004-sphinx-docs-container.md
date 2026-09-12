---
type: Architecture Decision
title: ADR-0004 Documentation shipped as a Sphinx site in an nginx image
description: The API reference is generated with Sphinx, baked into an nginx image and rolled out by Cloud Build.
status: accepted
date: unknown
deciders: []
supersedes: []
affects: [alpaca_py, alpaca_py.docs_site, ext_gcp]
allium: []
evidence: ["Dockerfile", "cloudbuild.yaml", "docs/Makefile", "docs/api_reference/", "pyproject.toml", ".github/workflows/ci.yaml", "README.md"]
tags: [alpacahq, adr, generated]
timestamp: 2026-09-11T00:00:00+00:00
generated_by: claude-opus-5 / layered-docs 2026-09
source_commit: 48fd544334a595c53e386043cc9282824b1e9c58
source_branch: docs/layered-2026-09
generated_at: 2026-09-11T00:00:00+00:00
confidence: medium
review_status: draft-needs-review
---

# ADR-0004 Documentation shipped as a Sphinx site in an nginx image

## Context

The README states that the SDK has "a supplementary documentation site which contains references for all clients, methods and models found in this codebase" and points at a hosted address (`README.md`, Documentation section). The reference therefore has to be generated from the source and served somewhere, and it has to stay in step with the code in the same repository.

## Decision

Generate the site with Sphinx from reStructuredText sources and docstrings, then bake the built HTML into an nginx image. The `Dockerfile` is multi-stage: a poetry dependency stage, a builder stage that runs the docs make target, and a final `nginx:alpine` stage that copies the built HTML into the nginx web root. `cloudbuild.yaml` builds and caches the dependency and application images, pushes them to Container Registry, and — only when the `_KUBE_API_SERVER`, `_KUBE_CA_CRT`, `_KUBE_NAMESPACE`, `_KUBE_DEPLOYMENT` substitutions and a service-account token are all supplied by the trigger — uses kubectl to set the image (on tags only) and restart the deployment, choosing a staging service-account token on the default branch and a production one on tags. With any of those values empty the kubectl step is a no-op (`cloudbuild.yaml` lines 62-67).

## Consequences

Sphinx, furo and the toolbox extensions are dev dependencies of the package (`pyproject.toml`), and the documentation build is also run in pull-request CI so that documentation errors fail the build (`.github/workflows/ci.yaml`). The reference tree is hand-maintained per module under `docs/api_reference/`, so new modules need a matching page. The deployment target is parameterised by substitution variables that are not defined in the repository, so the cluster and namespace cannot be determined from here.

> Unverified: the environment, cluster and namespace the documentation site runs in. Confidence: low.

## Alternatives considered

Not evidenced in the repository.
