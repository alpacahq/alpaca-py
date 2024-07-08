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
