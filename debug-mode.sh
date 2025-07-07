#!/bin/bash

# Helper script to toggle debug mode for MiniPAM

# Function to show help
show_help() {
    echo "MiniPAM Debug Mode Helper"
    echo "Usage: ./debug-mode.sh [enable|disable|status]"
    echo ""
    echo "Commands:"
    echo "  enable   Enable debug mode"
    echo "  disable  Disable debug mode"
    echo "  status   Check if debug mode is enabled"
    echo ""
    echo "Debug mode enables detailed logging for:"
    echo "  • API requests and responses"
    echo "  • Storage operations (CRUD)"
    echo "  • Error traces and exception details"
    echo "  • CLI operations"
    echo ""
    echo "Debug logs will be written to the console and to log files."
    echo ""
}

# Check for help flag
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
    exit 0
fi

# Check if MINIPAM_DEBUG is set
check_status() {
    if [ -f .debug_mode ]; then
        echo "✅ Debug mode is ENABLED"
        return 0
    else
        echo "❌ Debug mode is DISABLED"
        return 1
    fi
}

# Enable debug mode
enable_debug() {
    echo "🐞 Enabling debug mode..."
    echo "export MINIPAM_DEBUG=1" > .debug_mode
    chmod +x .debug_mode
    
    echo "✅ Debug mode enabled! Use the following to activate it in your shell:"
    echo ""
    echo "  source .debug_mode"
    echo ""
    echo "Debug mode will be automatically used by ./dev-server.sh --debug"
}

# Disable debug mode
disable_debug() {
    echo "🚫 Disabling debug mode..."
    if [ -f .debug_mode ]; then
        rm .debug_mode
        echo "✅ Debug mode disabled"
        echo "Run 'unset MINIPAM_DEBUG' to disable debug mode in your current shell"
    else
        echo "Debug mode was not enabled"
    fi
}

# Process command
case "$1" in
    enable)
        enable_debug
        ;;
    disable)
        disable_debug
        ;;
    status)
        check_status
        ;;
    *)
        echo "⚠️  Unknown command: $1"
        show_help
        exit 1
        ;;
esac
