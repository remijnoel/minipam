#!/bin/bash

# Test script to verify CIDR validation error handling

echo "Testing MiniPAM CIDR validation error handling..."
echo ""

# Test 1: Duplicate CIDR
echo "1. Testing duplicate CIDR creation..."
response=$(curl -s -w "%{http_code}" -X POST "http://localhost:8000/api/cidrs" \
  -H "Content-Type: application/json" \
  -d '{"cidr": "0.0.0.0/0", "name": "Duplicate Root", "description": "Should fail"}')

http_code="${response: -3}"
if [ "$http_code" = "422" ]; then
    echo "✅ Duplicate CIDR validation working (HTTP 422)"
    body="${response%???}"
    echo "   Error message: $body"
else
    echo "❌ Unexpected response: HTTP $http_code"
fi

echo ""

# Test 2: Wrong parent hierarchy
echo "2. Testing wrong parent hierarchy..."
response=$(curl -s -w "%{http_code}" -X POST "http://localhost:8000/api/cidrs" \
  -H "Content-Type: application/json" \
  -d '{"cidr": "10.0.5.0/24", "name": "Wrong Parent", "description": "Should fail", "parent": "0.0.0.0/0"}')

http_code="${response: -3}"
if [ "$http_code" = "422" ]; then
    echo "✅ Smallest parent rule working (HTTP 422)"
    body="${response%???}"
    echo "   Error message: $body"
else
    echo "❌ Unexpected response: HTTP $http_code"
fi

echo ""
echo "Testing complete. You can now test the UI at http://localhost:8000"
echo "Try creating:"
echo "- A duplicate CIDR (e.g., 0.0.0.0/0)"
echo "- A CIDR with wrong parent (e.g., 192.168.1.0/24 under 0.0.0.0/0)"
echo ""
echo "You should see detailed error messages in the form modal."
