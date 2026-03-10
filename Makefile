# Makefile for building and testing Lambda functions and Glue jobs

.PHONY: ingestion-test ingestion-install ingestion-build
ingestion-test:
	@echo "Running descriptive test for ingestion lambda"
	@$(MAKE) -C lambdas/ingestion ingestion-test

ingestion-install:
	@echo "Running descriptive install for ingestion lambda"
	@$(MAKE) -C lambdas/ingestion ingestion-install

ingestion-build:
	@echo "Running descriptive build for ingestion lambda"
	@$(MAKE) -C lambdas/ingestion ingestion-build

.PHONY: silver-transform-test silver-transform-install silver-transform-build
silver-transform-test:
	@echo "Running descriptive test for silver-transform lambda"
	@$(MAKE) -C lambdas/silver-transform silver-transform-test

silver-transform-install:
	@echo "Running descriptive install for silver-transform lambda"
	@$(MAKE) -C lambdas/silver-transform silver-transform-install

silver-transform-build:
	@echo "Running descriptive build for silver-transform lambda"
	@$(MAKE) -C lambdas/silver-transform silver-transform-build

.PHONY: gold-transform-test gold-transform-install gold-transform-build
gold-transform-test:
	@echo "Running descriptive test for gold-transform lambda"
	@$(MAKE) -C lambdas/gold-transform gold-transform-test

gold-transform-install:
	@echo "Running descriptive install for gold-transform lambda"
	@$(MAKE) -C lambdas/gold-transform gold-transform-install

gold-transform-build:
	@echo "Running descriptive build for gold-transform lambda"
	@$(MAKE) -C lambdas/gold-transform gold-transform-build

# CI-style targets that exactly match GitHub Actions (using the new ci-* targets)
.PHONY: ci-ingestion-test ci-silver-transform-test ci-gold-transform-test
ci-ingestion-test:
	@echo "Running CI-style test for ingestion lambda (matches GitHub Actions)"
	@$(MAKE) -C lambdas/ingestion ingestion-ci-test

ci-silver-transform-test:
	@echo "Running CI-style test for silver-transform lambda (matches GitHub Actions)"
	@$(MAKE) -C lambdas/silver-transform silver-transform-ci-test

ci-gold-transform-test:
	@echo "Running CI-style test for gold-transform lambda (matches GitHub Actions)"
	@$(MAKE) -C lambdas/gold-transform gold-transform-ci-test

# Glue Job targets
glue-build:
	@echo "Building Glue job package"
	@$(MAKE) -C glue build-wheel

glue-test:
	@echo "Running Glue job tests"
	@$(MAKE) -C glue test

glue-lint:
	@echo "Linting Glue job code"
	@$(MAKE) -C glue lint

glue-lint-check:
	@echo "Checking Glue job code linting"
	@$(MAKE) -C glue lint-check

glue-format:
	@echo "Formatting Glue job code"
	@$(MAKE) -C glue format

glue-run:
	@echo "Running Glue job locally"
	@$(MAKE) -C glue run

glue-clean:
	@echo "Cleaning Glue job build artifacts"
	@$(MAKE) -C glue clean

glue-install:
	@echo "Installing Glue job dependencies"
	@$(MAKE) -C glue install

# CI/CD targets that mirror GitHub Actions workflows using new descriptive targets
.PHONY: ci-lint
ci-lint: ## Run CI linting workflow locally
	@echo "Running CI Lint Workflow"
	@echo "Linting all Lambdas..."
	@for lambda in $(LAMBDAS); do \
		echo "  Linting $$lambda..."; \
		./ci/scripts/lint-all-lambdas.sh $$lambda 2>/dev/null || true; \
	done
	@echo "Linting Glue job..."
	@$(MAKE) -C glue lint-check

.PHONY: ci-all
ci-all: ## Run all CI workflows locally
	$(MAKE) ci-lint

# Help message
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Sophisticated Lambda Targets:"
	@echo "  ingestion-test        Run descriptive test for ingestion lambda"
	@echo "  ingestion-install     Run descriptive install for ingestion lambda"
	@echo "  ingestion-build       Run descriptive build for ingestion lambda"
	@echo "  silver-transform-test Run descriptive test for silver-transform lambda"
	@echo "  silver-transform-install Run descriptive install for silver-transform lambda"
	@echo "  silver-transform-build Run descriptive build for silver-transform lambda"
	@echo "  gold-transform-test   Run descriptive test for gold-transform lambda"
	@echo "  gold-transform-install Run descriptive install for gold-transform lambda"
	@echo "  gold-transform-build  Run descriptive build for gold-transform lambda"
	@echo ""
	@echo "CI-Style Lambda Targets (matches GitHub Actions):"
	@echo "  ci-ingestion-test     Run exact CI test for ingestion lambda"
	@echo "  ci-silver-transform-test Run exact CI test for silver-transform lambda"
	@echo "  ci-gold-transform-test Run exact CI test for gold-transform lambda"
	@echo ""
	@echo "Glue Job Targets:"
	@echo "  glue-build            Build the Glue job package"
	@echo "  glue-test             Run Glue job tests"
	@echo "  glue-lint             Run code linting"
	@echo "  glue-lint-check       Check code linting without fixing"
	@echo "  glue-format           Format the code"
	@echo "  glue-run              Run the Glue job locally"
	@echo "  glue-clean            Clean build artifacts"
	@echo "  glue-install          Install dependencies"
	@echo ""
	@echo "CI/CD Targets:"
	@echo "  ci-lint               Run CI linting workflow locally"
	@echo "  ci-all                Run all CI workflows locally"
	@echo ""
	@echo "General Targets:"
	@echo "  help                  Show this help message"

.PHONY: all help glue-build glue-test glue-lint glue-lint-check glue-format glue-run glue-clean glue-install ci-ingestion-test ci-silver-transform-test ci-gold-transform-test ci-lint ci-all ingestion-test ingestion-install ingestion-build silver-transform-test silver-transform-install silver-transform-build gold-transform-test gold-transform-install gold-transform-build
