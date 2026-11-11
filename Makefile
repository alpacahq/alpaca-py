# The default "help" goal nicely prints all the available goals based on the funny looking ## comments.
# Source: https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.DEFAULT_GOAL := help
.PHONY: help
help:  ## Display this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: ## Install the SDK and its dependencies using poetry
	poetry install

.PHONY: lint
lint: ## Run the linters
	poetry run black --check alpaca/ tests/ consumer_checks/

# Same mypy config as CI (`pyproject.toml`): public SDK signatures stay visible,
# and implementation errors in imported `alpaca.*` modules are outside this gate.
.PHONY: typecheck
typecheck: ## Check the return types that type checkers infer for the public client overloads
	poetry run mypy tests/type_checks/

.PHONY: generate
generate: ## Generate the documentation
	./tools/scripts/generate-docs.sh

.PHONY: test
test: ## Run the unit tests
	poetry run pytest

# Compare the current tree's public API against a published PyPI release, or
# against a git ref (e.g. origin/master) with BASELINE_REF.
# Optional: AGAINST=0.43.5 BASELINE_REF=origin/master WORKDIR=/tmp/aexpy-alpaca
.PHONY: check-api-breakage
check-api-breakage: ## Compare public API vs a release (AGAINST=version) or ref (BASELINE_REF=origin/master)
	python3 tools/scripts/compare_api_breakage.py \
		$(if $(AGAINST),--against $(AGAINST)) \
		$(if $(BASELINE_REF),--baseline-ref $(BASELINE_REF)) \
		$(if $(WORKDIR),--workdir $(WORKDIR) --keep-workdir) \
		$(if $(VERBOSE),--verbose) \
		--fail-on-breaking

# Consumer checks (consumer_checks/README.md): SDK code written like user code,
# replayed from recordings of the paper API made with the BASELINE release.
.PHONY: consumer-check
consumer-check: consumer-typecheck consumer-replay ## Type-check and replay the consumer scenarios (offline)

.PHONY: consumer-typecheck
consumer-typecheck: ## Type-check the consumer scenarios against the current SDK
	poetry run mypy --follow-imports=silent --warn-unused-ignores consumer_checks/scenarios

.PHONY: consumer-replay
consumer-replay: ## Replay recorded scenarios: requests and outputs must match
	poetry run pytest consumer_checks $(ARGS)

.PHONY: consumer-live
consumer-live: ## Run scenarios against the paper API (keys from env or .env)
	poetry run pytest consumer_checks --consumer-mode=live $(ARGS)

.PHONY: consumer-record
consumer-record: ## Record scenarios that have no recording yet, with the BASELINE release on the paper API (ARGS="--consumer-rerecord -k name" to redo)
	consumer_checks/record_baseline.sh $(ARGS)

.PHONY: consumer-migrate
consumer-migrate: ## Upgrade old-format recordings offline, with the BASELINE release (no API calls)
	CONSUMER_MODE=migrate consumer_checks/record_baseline.sh $(ARGS)

.PHONY: consumer-refresh
consumer-refresh: ## Re-take snapshots offline after a pandas/numpy/pydantic change in poetry.lock
	CONSUMER_MODE=refresh consumer_checks/record_baseline.sh $(ARGS)

.PHONY: consumer-surface
consumer-surface: ## Check that public surface new since BASELINE is exercised by recorded scenarios
	poetry run python consumer_checks/check_surface.py --strict --show-all

.PHONY: consumer-surface-baseline
consumer-surface-baseline: ## Write surface_baseline.json, the public surface of the BASELINE release
	CONSUMER_MODE=surface consumer_checks/record_baseline.sh

.PHONY: consumer-coverage
consumer-coverage: ## Show which public client methods have no consumer scenario
	poetry run python consumer_checks/check_coverage.py --show-uncovered
