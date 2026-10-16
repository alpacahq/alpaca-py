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
	poetry run black --check alpaca/ tests/

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
