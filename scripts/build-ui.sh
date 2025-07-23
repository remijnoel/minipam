#!/bin/bash
# Build and package external UI for MiniPAM

# Use the root path version
exec "$(dirname "$0")/build-ui-root.sh" "$@"