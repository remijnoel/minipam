#!/bin/bash

# Quick build script for MiniPAM Web UI
cd /Users/remi/Source/github/remijnoel/minipam/webui

echo "🏗️  Building MiniPAM Web UI..."

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Build the project
echo "🔨 Building production bundle..."
npm run build

echo "✅ Build complete! Files are in dist/"
echo "🌐 Web UI will be served by FastAPI at http://localhost:8000"
