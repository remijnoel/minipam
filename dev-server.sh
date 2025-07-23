#!/bin/bash
# Development server script for MiniPAM

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    error "Virtual environment not found. Run 'python3 -m venv .venv' first."
    exit 1
fi

# Activate virtual environment
log "Activating virtual environment..."
source .venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    log "Installing dependencies..."
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    pip install -e .
fi

# Set development environment variables
export MINIPAM_SERVER_DEBUG=true
export MINIPAM_SERVER_HOST=127.0.0.1
export MINIPAM_SERVER_PORT=8000
export MINIPAM_STORAGE_TYPE=memory
export MINIPAM_AUTH_BACKEND=none
export ENABLE_NOAUTH=true
export MINIPAM_UI_ENABLED=true

# Check if config file exists
CONFIG_FILE="config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    warn "No config file found. Using environment variables."
    CONFIG_FILE=""
fi

# Start the development server
log "Starting MiniPAM development server..."
log "Server will be available at: http://127.0.0.1:8000"
log "Web UI will be available at: http://127.0.0.1:8000/"
log "API documentation at: http://127.0.0.1:8000/api/docs"
log "Press Ctrl+C to stop the server"

if [ -n "$CONFIG_FILE" ]; then
    python -m minipam.main "$CONFIG_FILE"
else
    python -m minipam.main
fi