# MiniPAM Development Makefile

# Include local configuration if it exists
-include Makefile.local

# Default configuration (can be overridden in Makefile.local)
API_BASE_URL ?= http://localhost:8000/api/v1

# Docker configuration
IMAGE_TAG := latest
LOCAL_IMAGE := minipam:$(IMAGE_TAG)

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help setup build test local init clean build-ui

help: ## Show this help message
	@echo "$(GREEN)MiniPAM Development Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Available Commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(YELLOW)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

init: ## Initialize local development environment
	@echo "$(GREEN)Setting up local development environment...$(NC)"
	@if [ ! -f "Makefile.local" ]; then \
		echo "$(YELLOW)Creating Makefile.local for custom configuration$(NC)"; \
		echo "# MiniPAM Local Configuration" > Makefile.local; \
		echo "# Add your custom settings here" >> Makefile.local; \
		echo "# API_BASE_URL := http://localhost:8000/api/v1" >> Makefile.local; \
	else \
		echo "$(YELLOW)Makefile.local already exists$(NC)"; \
	fi

build: ## Build Docker image for development
	@echo "$(GREEN)Building development Docker image...$(NC)"
	@if docker buildx version >/dev/null 2>&1; then \
		docker buildx build --target development -t $(LOCAL_IMAGE) --load .; \
	else \
		docker build --target development -t $(LOCAL_IMAGE) .; \
	fi
	@echo "$(GREEN)Built image: $(LOCAL_IMAGE)$(NC)"

build-prod: ## Build Docker image for production
	@echo "$(GREEN)Building production Docker image...$(NC)"
	@if docker buildx version >/dev/null 2>&1; then \
		docker buildx build --target production -t $(LOCAL_IMAGE)-prod --load .; \
	else \
		docker build --target production -t $(LOCAL_IMAGE)-prod .; \
	fi
	@echo "$(GREEN)Built image: $(LOCAL_IMAGE)-prod$(NC)"

local: build ## Run locally with Docker
	@echo "$(GREEN)Starting MiniPAM locally...$(NC)"
	@echo "$(YELLOW)Access at: http://localhost:8000$(NC)"
	@echo "$(YELLOW)API at: http://localhost:8000/api/v1$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	@echo ""
	docker run --rm -it -p 8000:8000 $(LOCAL_IMAGE)

test: ## Run tests
	@echo "$(GREEN)Running tests...$(NC)"
	python -m pytest

test-coverage: ## Run tests with coverage
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	python -m pytest --cov=src/minipam --cov-report=html --cov-report=term

clean: ## Clean up local Docker images and UI build artifacts
	@echo "$(GREEN)Cleaning up local images and UI artifacts...$(NC)"
	docker rmi $(LOCAL_IMAGE) $(LOCAL_IMAGE)-prod 2>/dev/null || true
	docker system prune -f
	rm -rf src/minipam/ui temp-ui-build 2>/dev/null || true

build-ui: ## Build and package external UI locally
	@echo "$(GREEN)Building external UI...$(NC)"
	@if [ ! -d "src/minipam/ui/dist" ]; then \
		./scripts/build-ui.sh; \
	else \
		echo "$(YELLOW)UI already built. To rebuild, run: make clean build-ui$(NC)"; \
	fi

populate-local: ## Populate local service with sample CIDR data
	@echo "$(GREEN)Populating local service with sample CIDR data...$(NC)"
	@echo "$(YELLOW)Using API: $(API_BASE_URL)$(NC)"
	@./scripts/populate_from_seed.sh "$(API_BASE_URL)" data/seed-data.json

clear-data-local: ## Remove all CIDR data from local service
	@echo "$(YELLOW)⚠️  This will delete ALL CIDR data from $(API_BASE_URL)!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "$(GREEN)Clearing all CIDR data...$(NC)"
	@echo "$(YELLOW)Using API: $(API_BASE_URL)$(NC)"
	@curl -s -X GET "$(API_BASE_URL)/cidrs" | jq -r '.blocks[].cidr' | while read cidr; do \
		echo "Deleting: $$cidr"; \
		curl -s -X DELETE "$(API_BASE_URL)/cidrs/$$cidr" | jq -r '.message // "Deleted"'; \
	done
	@echo "$(GREEN)✅ All CIDR data cleared!$(NC)"

# Development helpers
dev: ## Start development server with hot reload
	@echo "$(GREEN)Starting development server...$(NC)"
	./dev-server.sh

install-dev: ## Install package in development mode
	@echo "$(GREEN)Installing in development mode...$(NC)"
	pip install -e .

# Show configuration
config: ## Show current configuration
	@echo "$(GREEN)Current Configuration:$(NC)"
	@echo "  Local Image: $(LOCAL_IMAGE)"
	@echo "  API Base URL: $(API_BASE_URL)"

# Default target
.DEFAULT_GOAL := help