# MiniPAM Development Makefile

# Configuration
AWS_REGION ?= us-west-2
AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "unknown")
ECR_REPO_NAME := minipam-dev
STACK_NAME := minipam-dev-fargate
SERVICE_NAME := minipam-dev-service
CLUSTER_NAME := minipam-dev-cluster
API_BASE_URL := https://minipam-dev.infra.rnoel.net/api/v1

# Docker configuration
IMAGE_TAG := latest
LOCAL_IMAGE := $(ECR_REPO_NAME):$(IMAGE_TAG)
ECR_IMAGE := $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(ECR_REPO_NAME):$(IMAGE_TAG)

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help setup build push deploy redeploy logs status clean destroy test local

help: ## Show this help message
	@echo "$(GREEN)MiniPAM Development Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(YELLOW)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker image for development
	@echo "$(GREEN)Building development Docker image for AMD64 (x86_64)...$(NC)"
	@if docker buildx version >/dev/null 2>&1; then \
		docker buildx build --platform linux/amd64 -f Dockerfile.dev -t $(LOCAL_IMAGE) --load .; \
	else \
		echo "$(YELLOW)Docker buildx not available, using regular build (may not work on ARM Mac)$(NC)"; \
		DOCKER_DEFAULT_PLATFORM=linux/amd64 docker build -f Dockerfile.dev -t $(LOCAL_IMAGE) .; \
	fi
	@echo "$(GREEN)Built image: $(LOCAL_IMAGE) for AMD64$(NC)"

build-local: ## Build Docker image for local testing (native architecture)
	@echo "$(GREEN)Building development Docker image for local testing...$(NC)"
	docker build -f Dockerfile.dev -t $(LOCAL_IMAGE)-local .
	@echo "$(GREEN)Built image: $(LOCAL_IMAGE)-local$(NC)"

push: build ## Build and push image to ECR
	@echo "$(GREEN)Logging into ECR...$(NC)"
	@aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	@echo "$(GREEN)Tagging image for ECR...$(NC)"
	docker tag $(LOCAL_IMAGE) $(ECR_IMAGE)
	@echo "$(GREEN)Pushing to ECR...$(NC)"
	docker push $(ECR_IMAGE)
	@echo "$(GREEN)Image pushed: $(ECR_IMAGE)$(NC)"

redeploy: push ## Force redeploy ECS service with latest image
	@echo "$(GREEN)Forcing ECS service redeployment with latest image...$(NC)"
	@echo "$(YELLOW)Cluster: $(CLUSTER_NAME)$(NC)"
	@echo "$(YELLOW)Service: $(SERVICE_NAME)$(NC)"
	@echo "$(YELLOW)Image: $(ECR_IMAGE)$(NC)"
	@echo ""
	@aws ecs update-service \
		--cluster $(CLUSTER_NAME) \
		--service $(SERVICE_NAME) \
		--force-new-deployment \
		--region $(AWS_REGION) \
		--output table
	@echo ""
	@echo "$(GREEN)✅ Redeployment initiated!$(NC)"
	@echo "$(YELLOW)⏳ Waiting for deployment to complete...$(NC)"
	@$(MAKE) wait-stable
	@echo "$(GREEN)🚀 Deployment complete!$(NC)"

deploy: redeploy ## Alias for redeploy

wait-stable: ## Wait for service to become stable
	@echo "$(YELLOW)Waiting for service to stabilize...$(NC)"
	@aws ecs wait services-stable --cluster $(CLUSTER_NAME) --services $(SERVICE_NAME) --region $(AWS_REGION)
	@echo "$(GREEN)Service is stable!$(NC)"

status: ## Show ECS service status
	@echo "$(GREEN)Getting ECS service status...$(NC)"
	@echo ""
	@echo "$(YELLOW)Service Details:$(NC)"
	@aws ecs describe-services \
		--cluster $(CLUSTER_NAME) \
		--services $(SERVICE_NAME) \
		--region $(AWS_REGION) \
		--query 'services[0].{Status:status,DesiredCount:desiredCount,RunningCount:runningCount,PendingCount:pendingCount,Deployments:deployments[*].{Status:status,DesiredCount:desiredCount,RunningCount:runningCount,CreatedAt:createdAt}}' \
		--output table 2>/dev/null || echo "$(RED)Service not found$(NC)"
	@echo ""
	@echo "$(YELLOW)Recent Events:$(NC)"
	@aws ecs describe-services \
		--cluster $(CLUSTER_NAME) \
		--services $(SERVICE_NAME) \
		--region $(AWS_REGION) \
		--query 'services[0].events[0:5].{Time:createdAt,Message:message}' \
		--output table 2>/dev/null || echo "$(RED)No events found$(NC)"
	@echo ""
	@echo "$(GREEN)💡 Note: To get the API URL, check your ALB in AWS Console$(NC)"

logs: ## Show recent application logs
	@echo "$(GREEN)Fetching recent logs...$(NC)"
	@aws logs tail /ecs/minipam --follow --region $(AWS_REGION) 2>/dev/null || \
	echo "$(YELLOW)Log group not found or no recent logs$(NC)"

local: build-local ## Run locally with Docker
	@echo "$(GREEN)Starting MiniPAM locally...$(NC)"
	@echo "$(YELLOW)Access at: http://localhost:8000$(NC)"
	@echo "$(YELLOW)API at: http://localhost:8000/api/v1$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	@echo ""
	docker run --rm -it -p 8000:8000 $(LOCAL_IMAGE)-local

clean: ## Clean up local Docker images and UI build artifacts
	@echo "$(GREEN)Cleaning up local images and UI artifacts...$(NC)"
	docker rmi $(LOCAL_IMAGE) $(LOCAL_IMAGE)-local 2>/dev/null || true
	docker system prune -f
	rm -rf src/minipam/ui temp-ui-build 2>/dev/null || true

stop-service: ## Stop the ECS service (set desired count to 0)
	@echo "$(YELLOW)Stopping ECS service...$(NC)"
	@aws ecs update-service \
		--cluster $(CLUSTER_NAME) \
		--service $(SERVICE_NAME) \
		--desired-count 0 \
		--region $(AWS_REGION) >/dev/null
	@echo "$(GREEN)Service stopped (desired count set to 0)$(NC)"

start-service: ## Start the ECS service (set desired count to 1)
	@echo "$(YELLOW)Starting ECS service...$(NC)"
	@aws ecs update-service \
		--cluster $(CLUSTER_NAME) \
		--service $(SERVICE_NAME) \
		--desired-count 1 \
		--region $(AWS_REGION) >/dev/null
	@echo "$(GREEN)Service started (desired count set to 1)$(NC)"

# Development shortcuts
dev: local ## Alias for local development

quick: redeploy ## Quick redeploy alias

info: status ## Alias for status

# Advanced targets
shell: build ## Get shell access to built image
	@echo "$(GREEN)Starting shell in development container...$(NC)"
	docker run --rm -it --entrypoint /bin/bash $(LOCAL_IMAGE)

build-prod: ## Build production image
	@echo "$(GREEN)Building production Docker image...$(NC)"
	docker build -f Dockerfile.production -t $(ECR_REPO_NAME):prod .

build-ui: ## Build and package external UI locally
	@echo "$(GREEN)Building external UI...$(NC)"
	@if [ ! -d "src/minipam/ui/dist" ]; then \
		./scripts/build-ui.sh; \
	else \
		echo "$(YELLOW)UI already built. To rebuild, run: make clean build-ui$(NC)"; \
	fi

# Validation targets
validate-aws: ## Validate AWS configuration
	@echo "$(GREEN)Validating AWS configuration...$(NC)"
	@aws sts get-caller-identity --region $(AWS_REGION) >/dev/null 2>&1 && \
	echo "$(GREEN)✅ AWS CLI configured correctly$(NC)" || \
	echo "$(RED)❌ AWS CLI not configured$(NC)"

validate-ecs: ## Validate ECS service exists
	@echo "$(GREEN)Validating ECS service...$(NC)"
	@if aws ecs describe-services --cluster $(CLUSTER_NAME) --services $(SERVICE_NAME) --region $(AWS_REGION) >/dev/null 2>&1; then \
		echo "$(GREEN)✅ ECS service found$(NC)"; \
	else \
		echo "$(RED)❌ ECS service not found$(NC)"; \
		echo "$(YELLOW)  Cluster: $(CLUSTER_NAME)$(NC)"; \
		echo "$(YELLOW)  Service: $(SERVICE_NAME)$(NC)"; \
	fi

# Show configuration
config: ## Show current configuration
	@echo "$(GREEN)Current Configuration:$(NC)"
	@echo "  AWS Region: $(AWS_REGION)"
	@echo "  AWS Account: $(AWS_ACCOUNT_ID)"
	@echo "  ECR Repo: $(ECR_REPO_NAME)"
	@echo "  Stack Name: $(STACK_NAME)"
	@echo "  Service Name: $(SERVICE_NAME)"
	@echo "  Cluster Name: $(CLUSTER_NAME)"
	@echo "  Local Image: $(LOCAL_IMAGE)"
	@echo "  ECR Image: $(ECR_IMAGE)"
	@echo "  API Base URL: $(API_BASE_URL)"

populate: ## Populate the service with sample CIDR data from seed file
	@echo "$(GREEN)Populating service with sample CIDR data...$(NC)"
	@echo "$(YELLOW)Using API: $(API_BASE_URL)$(NC)"
	@./scripts/populate_from_seed.sh "$(API_BASE_URL)" seed-data.json

populate-url: ## Populate using a specific URL (usage: make populate-url URL=http://your-api/api/v1)
	@if [ -z "$(URL)" ]; then \
		echo "$(RED)Error: URL parameter required$(NC)"; \
		echo "$(YELLOW)Usage: make populate-url URL=http://your-api/api/v1$(NC)"; \
		exit 1; \
	fi
	@./scripts/populate_from_seed.sh "$(URL)" seed-data.json

clear-data: ## Remove all CIDR data from the deployed service
	@echo "$(YELLOW)⚠️  This will delete ALL CIDR data from $(API_BASE_URL)!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "$(GREEN)Clearing all CIDR data...$(NC)"
	@echo "$(YELLOW)Using API: $(API_BASE_URL)$(NC)"
	@curl -s -X GET "$(API_BASE_URL)/cidrs" | jq -r '.blocks[].cidr' | while read cidr; do \
		echo "Deleting: $$cidr"; \
		curl -s -X DELETE "$(API_BASE_URL)/cidrs/$$cidr" | jq -r '.message // "Deleted"'; \
	done
	@echo "$(GREEN)✅ All CIDR data cleared!$(NC)"



# Convenience targets for common workflows
update: redeploy ## Update the service with latest code (alias for redeploy)
	@echo "$(GREEN)🚀 Update complete!$(NC)"

check: validate-aws validate-ecs status ## Check everything is working

# API testing targets
test-api: ## Test API connectivity and health
	@echo "$(GREEN)Testing API connectivity...$(NC)"
	@echo "$(YELLOW)API URL: $(API_BASE_URL)$(NC)"
	@echo "$(GREEN)Health check:$(NC)"
	@curl -s "$(API_BASE_URL)/health/ready" | jq . || echo "$(RED)Health check failed$(NC)"
	@echo "$(GREEN)List CIDRs:$(NC)"
	@curl -s "$(API_BASE_URL)/cidrs" | jq . || echo "$(RED)CIDR list failed$(NC)"

show-tree: ## Display the current CIDR tree
	@echo "$(GREEN)Current CIDR tree:$(NC)"
	@curl -s "$(API_BASE_URL)/cidrs/tree" | jq . || echo "$(RED)Tree fetch failed$(NC)"

# Default target
.DEFAULT_GOAL := help