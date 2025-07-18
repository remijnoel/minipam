#!/bin/bash
# Docker entrypoint script for MiniPAM

set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Initialize configuration if needed
if [ ! -f /etc/minipam/config.yaml ] && [ "$MINIPAM_INIT_CONFIG" = "true" ]; then
    log "Initializing default configuration..."
    minipam init --path /app/data --type file
    mv config.yaml /etc/minipam/config.yaml
fi

# Set default command if none provided
if [ $# -eq 0 ]; then
    set -- minipam serve
fi

# Handle different commands
case "$1" in
    "minipam")
        log "Starting MiniPAM with command: $*"
        
        # Add config file if it exists
        if [ -f /etc/minipam/config.yaml ]; then
            set -- "$@" --config /etc/minipam/config.yaml
        fi
        
        exec "$@"
        ;;
    "init")
        log "Initializing MiniPAM..."
        exec minipam init --path /app/data --type file
        ;;
    "health")
        log "Running health check..."
        exec minipam health
        ;;
    "bash"|"sh")
        log "Starting shell..."
        exec "$@"
        ;;
    *)
        log "Executing command: $*"
        exec "$@"
        ;;
esac