#!/bin/bash
# Build and package UI from local development directory

set -e

# CHANGE THIS TO YOUR LOCAL FRONTEND PATH
LOCAL_UI_DIR="${LOCAL_UI_DIR:-../ipam-visual-nexus}"
UI_TARGET_DIR="src/minipam/ui"

echo "🎨 Building UI from local development directory"
echo "📁 Local UI Directory: $LOCAL_UI_DIR"
echo "🎯 Target Directory: $UI_TARGET_DIR"
echo ""

# Check if local UI directory exists
if [ ! -d "$LOCAL_UI_DIR" ]; then
    echo "❌ Local UI directory not found: $LOCAL_UI_DIR"
    echo "💡 Set LOCAL_UI_DIR environment variable or edit this script"
    exit 1
fi

# Clean up any existing UI directory
if [ -d "$UI_TARGET_DIR" ]; then
    echo "🧹 Cleaning existing UI directory..."
    rm -rf "$UI_TARGET_DIR"
fi

# Build in the local directory
cd "$LOCAL_UI_DIR"

# Build the UI
echo "🔨 Building UI..."
if command -v npm &> /dev/null; then
    npm run build
elif command -v yarn &> /dev/null; then
    yarn build
else
    echo "❌ Neither npm nor yarn found. Please install Node.js and npm."
    exit 1
fi

# Go back to minipam directory
cd -

# Create target directory structure
echo "📁 Creating UI package structure..."
mkdir -p "$UI_TARGET_DIR"

# Copy built files
echo "📋 Copying built UI files..."
cp -r "$LOCAL_UI_DIR/dist" "$UI_TARGET_DIR/"

# Create a simple __init__.py to make it a Python package
echo "# UI package" > "$UI_TARGET_DIR/__init__.py"

# Verify the build
if [ -d "$UI_TARGET_DIR/dist" ] && [ -f "$UI_TARGET_DIR/dist/index.html" ]; then
    echo ""
    echo "✅ UI successfully packaged from local directory!"
    echo "📁 UI files available at: $UI_TARGET_DIR/dist/"
    echo "🌐 Will be served at / when the app runs"
else
    echo "❌ UI packaging failed - dist/index.html not found"
    exit 1
fi