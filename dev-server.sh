#!/bin/bash

# MiniPAM Development Server Launcher
# Starts both the FastAPI backend and Vue.js frontend

# Default settings
DEBUG_MODE=0
BACKEND_PORT=8000
FRONTEND_PORT=3000
LOG_LEVEL="debug"
CONFIG_FILE=""

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --debug) DEBUG_MODE=1; LOG_LEVEL="debug"; shift ;;
        --backend-port) BACKEND_PORT="$2"; shift 2 ;;
        --frontend-port) FRONTEND_PORT="$2"; shift 2 ;;
        --config) CONFIG_FILE="$2"; shift 2 ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
done

echo "🚀 Starting MiniPAM Development Environment"
if [ $DEBUG_MODE -eq 1 ]; then
    echo "📊 Running in DEBUG MODE - Verbose logging enabled"
fi
echo "=========================================="

# Help function
show_help() {
    echo "Usage: ./dev-server.sh [options]"
    echo ""
    echo "Options:"
    echo "  --debug             Enable debug mode with verbose logging and detailed error messages"
    echo "                      Debug features include:"
    echo "                      • Detailed FastAPI error traces and exception handling"
    echo "                      • API request/response logging"
    echo "                      • HTTP request body logging"
    echo "                      • Vue.js/Vite debugging with inspector"
    echo "  --config FILE       Use a specific configuration file (YAML or JSON)"
    echo "  --backend-port N    Run backend on port N (default: 8000)"
    echo "  --frontend-port N   Run frontend on port N (default: 3000)"
    echo ""
    echo "Examples:"
    echo "  ./dev-server.sh --debug                     Start with debug mode"
    echo "  ./dev-server.sh --config config.yaml        Start with custom config"
    echo "  ./dev-server.sh --debug --backend-port 8080 Start with debug mode on port 8080"
    echo ""
    exit 0
}

# Show help if requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
fi

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the MiniPAM root directory"
    exit 1
fi

# Check if Python virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Python virtual environment not found. Please run 'python -m venv .venv && source .venv/bin/activate && pip install -e .'"
    exit 1
fi

# Check if Node.js dependencies are installed
if [ ! -d "webui/node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    cd webui && npm install && cd ..
fi

echo "🔧 Starting services..."

# Function to cleanup background processes
cleanup() {
    echo "🛑 Shutting down services..."
    kill "$(jobs -p)" 2>/dev/null
    exit
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Start FastAPI backend
echo "🐍 Starting FastAPI backend on http://localhost:${BACKEND_PORT}"

if [ $DEBUG_MODE -eq 1 ]; then
    # Debug mode with more verbose logging - set FastAPI log level and enable traceback printing
    echo "🔍 Debug mode: Running backend with verbose logging and detailed error traces"
    source .venv/bin/activate && \
    PYTHONPATH="$PWD" \
    MINIPAM_DEBUG=1 \
    PYTHONFAULTHANDLER=1 \
    python -m minipam.main \
    --host localhost --port "${BACKEND_PORT}" \
    --debug \
    ${CONFIG_FILE:+--config "$CONFIG_FILE"} 2>&1 | tee backend_debug.log &
else
    # Normal mode
    source .venv/bin/activate && python -m minipam.main \
    --host localhost --port "${BACKEND_PORT}" \
    ${CONFIG_FILE:+--config "$CONFIG_FILE"} 2>&1 | tee backend.log &
fi

# Store PID for potential future use
BACKEND_PID=$!

# Give backend time to start
sleep 3

# Start Vue.js frontend
echo "🌐 Starting Vue.js frontend on http://localhost:${FRONTEND_PORT}"

if [ $DEBUG_MODE -eq 1 ]; then
    # Debug mode for frontend with enhanced logging
    echo "🔍 Debug mode: Running frontend with verbose logging"
    cd webui && VITE_DEBUG=true NODE_ENV=development DEBUG="vite:*,vue:*,axios:*" VITE_API_LOG_LEVEL=debug npm run dev -- \
      --port "${FRONTEND_PORT}" \
      --debug \
      --force 2>&1 | tee ../frontend_debug.log &
else
    # Normal mode
    cd webui && npm run dev -- --port "${FRONTEND_PORT}" 2>&1 | tee ../frontend.log &
fi

# Store PID for potential future use
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Services started successfully!"
echo "📝 FastAPI Backend: http://localhost:${BACKEND_PORT}"
echo "🌐 Vue.js Frontend: http://localhost:${FRONTEND_PORT}"
echo "📚 API Documentation: http://localhost:${BACKEND_PORT}/docs"

if [ $DEBUG_MODE -eq 1 ]; then
    echo "📊 DEBUG MODE ACTIVE"
    echo "💡 Backend log level: ${LOG_LEVEL}"
    echo "🔍 API debugging features enabled:"
    echo "   • Request/response logging"
    echo "   • Detailed error traces"
    echo "   • Exception handling with full context"
    echo "   • Vue.js dev tools available"
    echo "   • Try PUT requests to '/cidrs/' to see detailed debug output"
    # Save PIDs to file for debugging
    echo "Backend PID: ${BACKEND_PID}" > .dev_server_pids.txt
    echo "Frontend PID: ${FRONTEND_PID}" >> .dev_server_pids.txt
fi

echo ""
echo "Press Ctrl+C to stop all services"

# Wait for background processes
wait
