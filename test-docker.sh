#!/bin/bash

# Test Docker Build and Run
# This script tests the Docker setup for MiniPAM

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🐳 Testing MiniPAM Docker Setup${NC}"
echo "=================================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed or not in PATH${NC}"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker Compose is not available, will test with Docker only${NC}"
    USE_COMPOSE=false
else
    USE_COMPOSE=true
fi

# Build the Docker image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker build -t minipam-test .

# Test basic docker run
echo -e "${YELLOW}🚀 Testing basic Docker run...${NC}"
CONTAINER_ID=$(docker run -d -p 8001:8000 --name minipam-test minipam-test)

# Wait for container to be ready
echo -e "${YELLOW}⏳ Waiting for container to be ready...${NC}"
sleep 10

# Test health endpoint
echo -e "${YELLOW}🔍 Testing health endpoint...${NC}"
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health endpoint is responding${NC}"
else
    echo -e "${RED}❌ Health endpoint failed${NC}"
    docker logs minipam-test
    docker stop minipam-test
    docker rm minipam-test
    exit 1
fi

# Test API endpoint
echo -e "${YELLOW}🔍 Testing API endpoint...${NC}"
if curl -f http://localhost:8001/api/cidrs/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API endpoint is responding${NC}"
else
    echo -e "${RED}❌ API endpoint failed${NC}"
    docker logs minipam-test
    docker stop minipam-test
    docker rm minipam-test
    exit 1
fi

# Test web UI
echo -e "${YELLOW}🔍 Testing web UI...${NC}"
if curl -f http://localhost:8001/ui > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Web UI is responding${NC}"
else
    echo -e "${RED}❌ Web UI failed${NC}"
    docker logs minipam-test
    docker stop minipam-test
    docker rm minipam-test
    exit 1
fi

# Cleanup
echo -e "${YELLOW}🧹 Cleaning up...${NC}"
docker stop minipam-test
docker rm minipam-test

# Test with Docker Compose if available
if [ "$USE_COMPOSE" = true ]; then
    echo -e "${YELLOW}🔧 Testing with Docker Compose...${NC}"
    docker-compose up -d
    
    # Wait for service to be ready
    echo -e "${YELLOW}⏳ Waiting for Docker Compose services...${NC}"
    sleep 15
    
    # Test health endpoint
    if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker Compose deployment is working${NC}"
    else
        echo -e "${RED}❌ Docker Compose deployment failed${NC}"
        docker-compose logs
        docker-compose down
        exit 1
    fi
    
    # Cleanup
    docker-compose down
fi

echo -e "${GREEN}🎉 All Docker tests passed!${NC}"
echo ""
echo -e "${GREEN}📋 Summary:${NC}"
echo -e "  ✅ Docker image builds successfully"
echo -e "  ✅ Container starts and runs"
echo -e "  ✅ Health endpoint responds"
echo -e "  ✅ API endpoint responds"
echo -e "  ✅ Web UI responds"
if [ "$USE_COMPOSE" = true ]; then
    echo -e "  ✅ Docker Compose deployment works"
fi
echo ""
echo -e "${GREEN}🚀 Ready to deploy with:${NC}"
echo -e "  docker-compose up -d"
echo -e "  or"
echo -e "  docker run -p 8000:8000 minipam-test"
