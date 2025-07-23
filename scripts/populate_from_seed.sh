#!/bin/bash
# Populate MiniPAM with data from seed file

if [ -z "$1" ]; then
    echo "Usage: $0 <API_URL> [SEED_FILE]"
    echo "Example: $0 http://localhost:8000/api/v1 seed-data.json"
    exit 1
fi

API_URL="$1"
SEED_FILE="${2:-seed-data.json}"

if [ ! -f "$SEED_FILE" ]; then
    echo "Error: Seed file '$SEED_FILE' not found"
    exit 1
fi

echo "🌱 Populating MiniPAM with data from $SEED_FILE"
echo "📡 API URL: $API_URL"
echo ""

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed"
    exit 1
fi

# Read and process each CIDR block from the seed file
jq -c '.[]' "$SEED_FILE" | while read -r cidr_data; do
    name=$(echo "$cidr_data" | jq -r '.name')
    cidr=$(echo "$cidr_data" | jq -r '.cidr')
    
    echo "Creating: $cidr - $name"
    
    response=$(curl -s -X POST "$API_URL/cidrs" \
        -H "Content-Type: application/json" \
        -d "$cidr_data")
    
    # Check if creation was successful
    if echo "$response" | jq -e '.cidr' > /dev/null 2>&1; then
        echo "  ✅ Success"
    else
        echo "  ❌ Failed: $response"
    fi
    
    # Small delay to avoid overwhelming the API
    sleep 0.1
done

echo ""
echo "✅ Population complete!"
echo "🌳 View the tree: curl $API_URL/cidrs/tree"