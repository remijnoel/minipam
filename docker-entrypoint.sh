#!/bin/bash

# MiniPAM Docker Startup Script
# This script handles initialization and startup of MiniPAM in Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting MiniPAM...${NC}"

# Check if data directory exists and is writable
if [ ! -d "/app/data" ]; then
    echo -e "${YELLOW}📁 Creating data directory...${NC}"
    mkdir -p /app/data
fi

if [ ! -w "/app/data" ]; then
    echo -e "${RED}❌ Data directory is not writable${NC}"
    exit 1
fi

# Check if config file exists
CONFIG_FILE="${MINIPAM_CONFIG_FILE:-/app/config.yaml}"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}📝 Generating default configuration...${NC}"
    python -m minipam.main --generate-config "$CONFIG_FILE"
fi

# Print startup information
echo -e "${GREEN}📊 MiniPAM Configuration:${NC}"
echo -e "  Config file: $CONFIG_FILE"
echo -e "  Data directory: /app/data"
echo -e "  Storage type: ${MINIPAM_STORAGE_TYPE:-file}"
echo -e "  Storage path: ${MINIPAM_STORAGE_FILE_PATH:-/app/data/cidrs.json}"
echo -e "  Server host: ${MINIPAM_SERVER_HOST:-0.0.0.0}"
echo -e "  Server port: ${MINIPAM_SERVER_PORT:-8000}"
echo -e "  Log level: ${MINIPAM_SERVER_LOG_LEVEL:-info}"
echo -e "  Debug mode: ${MINIPAM_DEBUG:-false}"

# Health check function
health_check() {
    local max_attempts=30
    local attempt=0
    
    echo -e "${YELLOW}🔍 Waiting for server to be ready...${NC}"
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "http://localhost:${MINIPAM_SERVER_PORT:-8000}/health" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Server is ready!${NC}"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts...${NC}"
        sleep 1
    done
    
    echo -e "${RED}❌ Server failed to start within timeout${NC}"
    return 1
}

# Start the server
echo -e "${GREEN}🌐 Starting MiniPAM server...${NC}"
echo -e "${GREEN}Web UI: http://localhost:${MINIPAM_SERVER_PORT:-8000}${NC}"
echo -e "${GREEN}API Docs: http://localhost:${MINIPAM_SERVER_PORT:-8000}/docs${NC}"
echo ""

# Execute the command passed to the script, or default to starting the server
if [ $# -eq 0 ]; then
    exec python -m minipam.main --config "$CONFIG_FILE" --host "${MINIPAM_SERVER_HOST:-0.0.0.0}" --port "${MINIPAM_SERVER_PORT:-8000}"
else
    exec "$@"
fi
