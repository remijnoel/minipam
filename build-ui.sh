#!/bin/bash
# Build script for MiniPAM UI

set -e

echo "Building MiniPAM UI..."

# Create dist directory if it doesn't exist
mkdir -p webui/dist

# Copy files to dist
echo "Copying UI files..."
cp webui/public/index.html webui/dist/
cp webui/public/vue.global.prod.js webui/dist/
cp webui/src/app.js webui/dist/

echo "✓ UI build complete!"
echo "Files available in webui/dist/"
echo ""
echo "To test the UI:"
echo "1. Run: python -m minipam.main --config config.yaml.example"
echo "2. Open: http://localhost:8000/ui/"