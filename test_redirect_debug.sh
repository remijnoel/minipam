#!/bin/bash

echo "OIDC Redirect Loop Debug Test"
echo "============================="

BASE_URL="http://localhost:8000"

echo ""
echo "1. Testing auth configuration..."
curl -s "$BASE_URL/auth/config" | jq . 2>/dev/null || curl -s "$BASE_URL/auth/config"

echo ""
echo "2. Testing auth health..."
curl -s "$BASE_URL/auth/health" | jq . 2>/dev/null || curl -s "$BASE_URL/auth/health"

echo ""
echo "3. Testing middleware behavior on different paths..."

paths=("/" "/ui" "/ui/" "/api/cidrs" "/auth/config" "/auth/health" "/auth/login/oidc" "/auth/callback/oidc" "/health")

for path in "${paths[@]}"; do
    echo ""
    echo "Testing path: $path"
    # Use -I to get headers only and don't follow redirects
    response=$(curl -s -I -w "Status: %{http_code}\nRedirect: %{redirect_url}\n" "$BASE_URL$path")
    echo "$response"
done

echo ""
echo "4. Testing OIDC login flow with redirect tracking..."

echo "Step 1: Initial OIDC login request"
response=$(curl -s -I -w "Status: %{http_code}\nRedirect: %{redirect_url}\n" "$BASE_URL/auth/login/oidc")
echo "$response"

# Extract redirect URL if any
redirect_url=$(echo "$response" | grep "^location:" | cut -d' ' -f2- | tr -d '\r\n')
if [ -n "$redirect_url" ]; then
    echo ""
    echo "Step 2: Following redirect to: $redirect_url"
    response2=$(curl -s -I -w "Status: %{http_code}\nRedirect: %{redirect_url}\n" "$redirect_url")
    echo "$response2"
    
    # Check for another redirect
    redirect_url2=$(echo "$response2" | grep "^location:" | cut -d' ' -f2- | tr -d '\r\n')
    if [ -n "$redirect_url2" ]; then
        echo ""
        echo "Step 3: Following second redirect to: $redirect_url2"
        response3=$(curl -s -I -w "Status: %{http_code}\nRedirect: %{redirect_url}\n" "$redirect_url2")
        echo "$response3"
    fi
fi

echo ""
echo "5. Testing specific browser-like request to root..."
curl -s -I -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
     -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
     -w "Status: %{http_code}\nRedirect: %{redirect_url}\n" \
     "$BASE_URL/"

echo ""
echo "6. Testing specific browser-like request to UI..."
curl -s -I -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
     -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
     -w "Status: %{http_code}\nRedirect: %{redirect_url}\n" \
     "$BASE_URL/ui"

echo ""
echo "Debug test complete!"