#!/bin/bash
# Test Docker builds for MiniPAM

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"
}

# Cleanup function
cleanup() {
    log "Cleaning up test containers and images..."
    docker-compose -f docker-compose.yml down --volumes --remove-orphans 2>/dev/null || true
    docker rmi minipam-test 2>/dev/null || true
    docker rmi minipam_minipam 2>/dev/null || true
}

# Set trap for cleanup
trap cleanup EXIT

echo "MiniPAM Docker Build Test"
echo "========================="

# Test 1: Build production image
echo ""
info "Test 1: Building production Docker image..."
if docker build -t minipam-test . --target production; then
    log "✓ Production Docker build successful"
else
    error "✗ Production Docker build failed"
    exit 1
fi

# Test 2: Build development image
echo ""
info "Test 2: Building development Docker image..."
if docker build -t minipam-test-dev . --target development; then
    log "✓ Development Docker build successful"
else
    error "✗ Development Docker build failed"
    exit 1
fi

# Test 3: Test production container startup
echo ""
info "Test 3: Testing production container startup..."
export ENABLE_NOAUTH=true
if docker run -d --name minipam-test-container \
    -p 8001:8000 \
    -e ENABLE_NOAUTH=true \
    -e MINIPAM_AUTH_BACKEND=none \
    -e MINIPAM_STORAGE_TYPE=memory \
    minipam-test; then
    log "✓ Production container started successfully"
    
    # Wait for container to be ready
    info "Waiting for container to be ready..."
    sleep 10
    
    # Test health endpoint
    if curl -f http://localhost:8001/api/v1/health/live >/dev/null 2>&1; then
        log "✓ Health endpoint responding"
    else
        error "✗ Health endpoint not responding"
        docker logs minipam-test-container
        exit 1
    fi
    
    # Stop test container
    docker stop minipam-test-container >/dev/null 2>&1
    docker rm minipam-test-container >/dev/null 2>&1
else
    error "✗ Production container failed to start"
    exit 1
fi

# Test 4: Test docker-compose
echo ""
info "Test 4: Testing docker-compose configuration..."
if docker-compose -f docker-compose.yml up -d; then
    log "✓ Docker Compose started successfully"
    
    # Wait for services to be ready
    info "Waiting for services to be ready..."
    sleep 15
    
    # Test health endpoint
    if curl -f http://localhost:8000/api/v1/health/live >/dev/null 2>&1; then
        log "✓ Docker Compose health endpoint responding"
    else
        error "✗ Docker Compose health endpoint not responding"
        docker-compose logs
        exit 1
    fi
    
    # Stop docker-compose
    docker-compose -f docker-compose.yml down --volumes >/dev/null 2>&1
else
    error "✗ Docker Compose failed to start"
    exit 1
fi

# Test 5: Test multi-stage build layers
echo ""
info "Test 5: Testing multi-stage build efficiency..."
PRODUCTION_SIZE=$(docker image inspect minipam-test --format='{{.Size}}')
DEV_SIZE=$(docker image inspect minipam-test-dev --format='{{.Size}}')

info "Production image size: $(($PRODUCTION_SIZE / 1024 / 1024)) MB"
info "Development image size: $(($DEV_SIZE / 1024 / 1024)) MB"

if [ "$PRODUCTION_SIZE" -lt "$DEV_SIZE" ]; then
    log "✓ Production image is smaller than development image"
else
    warn "⚠ Production image is not smaller than development image"
fi

# Test 6: Test container security
echo ""
info "Test 6: Testing container security..."
USER_ID=$(docker run --rm minipam-test id -u)
if [ "$USER_ID" != "0" ]; then
    log "✓ Container runs as non-root user (UID: $USER_ID)"
else
    error "✗ Container runs as root user"
    exit 1
fi

# Test 7: Test volume mounts
echo ""
info "Test 7: Testing volume mounts..."
if docker run --rm -v /tmp:/app/data minipam-test ls /app/data >/dev/null 2>&1; then
    log "✓ Volume mounts work correctly"
else
    error "✗ Volume mounts failed"
    exit 1
fi

# Cleanup
cleanup

echo ""
log "All Docker tests passed successfully!"
echo ""
info "Available Docker commands:"
info "  docker build -t minipam .                    # Build production image"
info "  docker-compose up -d                         # Start with compose"
info "  docker run -p 8000:8000 minipam              # Run production container"
info "  docker build -t minipam-dev . --target dev   # Build development image"