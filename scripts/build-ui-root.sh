#!/bin/bash
# Build and package external UI for MiniPAM to serve from root

set -e

UI_REPO="https://github.com/remijnoel/ipam-visual-nexus"
UI_TEMP_DIR="temp-ui-build"
UI_TARGET_DIR="src/minipam/ui"

echo "🎨 Building and packaging external UI for MiniPAM (root path)"
echo "📦 UI Repository: $UI_REPO"
echo "🎯 Target Directory: $UI_TARGET_DIR"
echo ""

# Clean up any existing UI directory
if [ -d "$UI_TARGET_DIR" ]; then
    echo "🧹 Cleaning existing UI directory..."
    rm -rf "$UI_TARGET_DIR"
fi

# Clean up temp directory if it exists
if [ -d "$UI_TEMP_DIR" ]; then
    echo "🧹 Cleaning temporary build directory..."
    rm -rf "$UI_TEMP_DIR"
fi

# Clone the UI repository
echo "📥 Cloning UI repository..."
git clone --depth 1 "$UI_REPO" "$UI_TEMP_DIR"

cd "$UI_TEMP_DIR"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ No package.json found in UI repository"
    exit 1
fi

# Install dependencies and build
echo "📦 Installing UI dependencies..."
if command -v npm &> /dev/null; then
    npm install --legacy-peer-deps
    echo "🔨 Building UI..."
    npm run build
elif command -v yarn &> /dev/null; then
    yarn install
    echo "🔨 Building UI..."
    yarn build
else
    echo "❌ Neither npm nor yarn found. Please install Node.js and npm."
    exit 1
fi

# Find the dist directory
DIST_DIR=""
if [ -d "dist" ]; then
    DIST_DIR="dist"
elif [ -d "build" ]; then
    DIST_DIR="build"
elif [ -d "public" ]; then
    DIST_DIR="public"
else
    echo "❌ Could not find built UI files (looked for dist/, build/, public/)"
    exit 1
fi

echo "✅ Found built UI in: $DIST_DIR"

# Go back to project root
cd ..

# Create target directory structure
echo "📁 Creating UI package structure..."
mkdir -p "$UI_TARGET_DIR"

# Copy built files
echo "📋 Copying built UI files..."
cp -r "$UI_TEMP_DIR/$DIST_DIR" "$UI_TARGET_DIR/"

# Create a simple __init__.py to make it a Python package
echo "# UI package" > "$UI_TARGET_DIR/__init__.py"

# Remove the injected config.js if it exists
rm -f "$UI_TARGET_DIR/dist/config.js"

# Clean up temporary directory
echo "🧹 Cleaning up temporary files..."
rm -rf "$UI_TEMP_DIR"

# Verify the build
if [ -d "$UI_TARGET_DIR/dist" ] && [ -f "$UI_TARGET_DIR/dist/index.html" ]; then
    echo ""
    echo "✅ UI successfully packaged for root path!"
    echo "📁 UI files available at: $UI_TARGET_DIR/dist/"
    echo "🌐 Will be served at / when the app runs"
    
    # Show some stats
    echo ""
    echo "📊 Package contents:"
    find "$UI_TARGET_DIR" -type f | wc -l | awk '{print "   Files: " $1}'
    du -sh "$UI_TARGET_DIR" | awk '{print "   Size: " $1}'
else
    echo "❌ UI packaging failed - dist/index.html not found"
    exit 1
fi