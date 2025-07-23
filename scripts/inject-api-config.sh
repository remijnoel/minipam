#!/bin/bash
# Inject API configuration into the built UI

UI_DIST_DIR="src/minipam/ui/dist"
API_BASE_URL="${1:-https://minipam-dev.infra.rnoel.net/api/v1}"

if [ ! -d "$UI_DIST_DIR" ]; then
    echo "❌ UI dist directory not found at $UI_DIST_DIR"
    exit 1
fi

echo "🔧 Injecting API configuration into UI..."
echo "📡 API Base URL: $API_BASE_URL"

# Create a config.js file that sets the API URL
cat > "$UI_DIST_DIR/config.js" << EOF
window.MINIPAM_CONFIG = {
  API_BASE_URL: "$API_BASE_URL"
};
EOF

# Inject the config script into index.html before other scripts
if [ -f "$UI_DIST_DIR/index.html" ]; then
    # Add config.js script tag before the main app script
    sed -i.bak '/<script type="module"/i\
    <script src="/ui/config.js"></script>' "$UI_DIST_DIR/index.html"
    rm -f "$UI_DIST_DIR/index.html.bak"
    echo "✅ Injected config.js into index.html"
else
    echo "❌ index.html not found"
    exit 1
fi

echo "✅ API configuration injected successfully"