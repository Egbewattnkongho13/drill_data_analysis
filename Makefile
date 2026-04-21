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

# Glue Job targets - Ingestion
.PHONY: glue-ingestion-build glue-ingestion-test glue-ingestion-lint glue-ingestion-lint-check glue-ingestion-format glue-ingestion-run glue-ingestion-clean glue-ingestion-install
glue-ingestion-build:
	@echo "Building Glue ingestion job package"
	@$(MAKE) -C glue-jobs/glue-ingestion build-wheel

glue-ingestion-test:
	@echo "Running Glue ingestion job tests"
	@$(MAKE) -C glue-jobs/glue-ingestion test

glue-ingestion-lint:
	@echo "Linting Glue ingestion job code"
	@$(MAKE) -C glue-jobs/glue-ingestion lint

glue-ingestion-lint-check:
	@echo "Checking Glue ingestion job code linting"
	@$(MAKE) -C glue-jobs/glue-ingestion lint-check

glue-ingestion-format:
	@echo "Formatting Glue ingestion job code"
	@$(MAKE) -C glue-jobs/glue-ingestion format

glue-ingestion-run:
	@echo "Running Glue ingestion job locally"
	@$(MAKE) -C glue-jobs/glue-ingestion run

glue-ingestion-clean:
	@echo "Cleaning Glue ingestion job build artifacts"
	@$(MAKE) -C glue-jobs/glue-ingestion clean

glue-ingestion-install:
	@echo "Installing Glue ingestion job dependencies"
	@$(MAKE) -C glue-jobs/glue-ingestion install

# Backwards compatibility aliases (deprecated - use glue-ingestion-* instead)
.PHONY: glue-build glue-test glue-lint glue-lint-check glue-format glue-run glue-clean glue-install
glue-build: glue-ingestion-build
glue-test: glue-ingestion-test
glue-lint: glue-ingestion-lint
glue-lint-check: glue-ingestion-lint-check
glue-format: glue-ingestion-format
glue-run: glue-ingestion-run
glue-clean: glue-ingestion-clean
glue-install: glue-ingestion-install

# CI/CD targets that mirror GitHub Actions workflows using new descriptive targets
.PHONY: ci-lint
ci-lint: ## Run CI linting workflow locally
	@echo "Running CI Lint Workflow"
	@echo "Linting all Lambdas..."
	@for lambda in $(LAMBDAS); do \
		echo "  Linting $$lambda..."; \
		./ci/scripts/lint-all-lambdas.sh $$lambda 2>/dev/null || true; \
	done
	@echo "Linting Glue jobs..."
	@$(MAKE) -C glue-jobs/glue-ingestion lint-check

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
	@echo "  glue-ingestion-build  Build the Glue ingestion job package"
	@echo "  glue-ingestion-test   Run Glue ingestion job tests"
	@echo "  glue-ingestion-lint   Lint Glue ingestion job code"
	@echo "  glue-ingestion-lint-check Check linting without fixing"
	@echo "  glue-ingestion-format Format the Glue ingestion job code"
	@echo "  glue-ingestion-run    Run the Glue ingestion job locally"
	@echo "  glue-ingestion-clean  Clean build artifacts"
	@echo "  glue-ingestion-install Install dependencies"
	@echo ""
	@echo "  (Legacy aliases: glue-build, glue-test, etc. point to glue-ingestion-*)"
	@echo ""
	@echo "CI/CD Targets:"
	@echo "  ci-lint               Run CI linting workflow locally"
	@echo "  ci-all                Run all CI workflows locally"
	@echo ""
	@echo "General Targets:"
	@echo "  help                  Show this help message"

.PHONY: all help ci-ingestion-test ci-silver-transform-test ci-gold-transform-test ci-lint ci-all ingestion-test ingestion-install ingestion-build silver-transform-test silver-transform-install silver-transform-build gold-transform-test gold-transform-install gold-transform-build
