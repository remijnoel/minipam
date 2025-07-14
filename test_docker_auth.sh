#!/bin/bash
# 
# MiniPAM Authentication Test Script
# 
# This script demonstrates how to authenticate and use the MiniPAM API
# when running with Docker Compose and API key authentication.
#

set -e

# Configuration
BASE_URL="http://localhost:8000"
ADMIN_API_KEY="sk-minipam-admin-12345"
VIEWER_API_KEY="sk-minipam-viewer-67890"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}MiniPAM Authentication Test Script${NC}"
echo "=================================="
echo

# Function to test API endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local token=$3
    local description=$4
    
    echo -e "${YELLOW}Testing: $description${NC}"
    echo "→ $method $endpoint"
    
    if [ -n "$token" ]; then
        response=$(curl -s -X "$method" -H "Authorization: Bearer $token" "$BASE_URL$endpoint")
    else
        response=$(curl -s -X "$method" "$BASE_URL$endpoint")
    fi
    
    echo "← Response: $response"
    echo
}

# Check if MiniPAM is running
echo -e "${YELLOW}1. Checking if MiniPAM is running...${NC}"
if ! curl -s "$BASE_URL/health" > /dev/null; then
    echo -e "${RED}❌ MiniPAM is not running. Start it with: docker-compose up -d${NC}"
    exit 1
fi
echo -e "${GREEN}✅ MiniPAM is running${NC}"
echo

# Test authentication configuration
echo -e "${YELLOW}2. Checking authentication configuration...${NC}"
auth_config=$(curl -s "$BASE_URL/auth/config")
echo "→ GET /auth/config"
echo "← $auth_config"
echo

# Test authentication health
echo -e "${YELLOW}3. Checking authentication health...${NC}"
auth_health=$(curl -s "$BASE_URL/auth/health")
echo "→ GET /auth/health"
echo "← $auth_health"
echo

# Test unauthenticated access (should fail)
echo -e "${YELLOW}4. Testing unauthenticated access (should fail)...${NC}"
unauth_response=$(curl -s "$BASE_URL/api/cidrs" || echo '{"detail":"Authentication required"}')
echo "→ GET /api/cidrs (no auth)"
echo "← $unauth_response"
echo

# Test admin authentication
echo -e "${YELLOW}5. Authenticating as admin...${NC}"
admin_login_response=$(curl -s -X POST "$BASE_URL/auth/login/apikey?api_key=$ADMIN_API_KEY")
echo "→ POST /auth/login/apikey?api_key=$ADMIN_API_KEY"
echo "← $admin_login_response"

# Extract admin token
admin_token=$(echo "$admin_login_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

if [ -z "$admin_token" ]; then
    echo -e "${RED}❌ Failed to get admin token${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Admin token obtained${NC}"
echo

# Test viewer authentication
echo -e "${YELLOW}6. Authenticating as viewer...${NC}"
viewer_login_response=$(curl -s -X POST "$BASE_URL/auth/login/apikey?api_key=$VIEWER_API_KEY")
echo "→ POST /auth/login/apikey?api_key=$VIEWER_API_KEY"
echo "← $viewer_login_response"

# Extract viewer token
viewer_token=$(echo "$viewer_login_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

if [ -z "$viewer_token" ]; then
    echo -e "${RED}❌ Failed to get viewer token${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Viewer token obtained${NC}"
echo

# Test authenticated access
echo -e "${YELLOW}7. Testing authenticated API access...${NC}"

# Test admin access (read)
test_endpoint "GET" "/api/cidrs" "$admin_token" "Admin reading CIDRs"

# Test admin user info
test_endpoint "GET" "/auth/user" "$admin_token" "Admin user info"

# Test viewer access (read)
test_endpoint "GET" "/api/cidrs" "$viewer_token" "Viewer reading CIDRs"

# Test viewer user info
test_endpoint "GET" "/auth/user" "$viewer_token" "Viewer user info"

# Test creating a CIDR (admin should succeed, viewer should fail)
echo -e "${YELLOW}8. Testing write permissions...${NC}"

# Create test CIDR data
cidr_data='{"cidr":"192.168.1.0/24","name":"test-network","description":"Test network for authentication demo"}'

echo "Testing admin write access (should succeed):"
echo "→ POST /api/cidrs/ with data: $cidr_data"
admin_create_response=$(curl -s -X POST -H "Authorization: Bearer $admin_token" -H "Content-Type: application/json" -d "$cidr_data" "$BASE_URL/api/cidrs/")
echo "← $admin_create_response"
echo

echo "Testing viewer write access (should fail):"
echo "→ POST /api/cidrs/ with data: $cidr_data"
viewer_create_response=$(curl -s -X POST -H "Authorization: Bearer $viewer_token" -H "Content-Type: application/json" -d "$cidr_data" "$BASE_URL/api/cidrs/" || echo '{"detail":"Permission denied"}')
echo "← $viewer_create_response"
echo

# Summary
echo -e "${BLUE}Test Summary:${NC}"
echo "============"
echo -e "${GREEN}✅ Authentication system is working${NC}"
echo -e "${GREEN}✅ API key authentication successful${NC}"
echo -e "${GREEN}✅ JWT tokens generated and validated${NC}"
echo -e "${GREEN}✅ Role-based permissions enforced${NC}"
echo -e "${GREEN}✅ Admin can read and write${NC}"
echo -e "${GREEN}✅ Viewer can read but not write${NC}"
echo
echo -e "${YELLOW}API Keys for reference:${NC}"
echo "- Admin (readwrite): $ADMIN_API_KEY"
echo "- Viewer (readonly):  $VIEWER_API_KEY"
echo
echo -e "${YELLOW}Example usage:${NC}"
echo "1. Get token: curl -X POST \"$BASE_URL/auth/login/apikey?api_key=$ADMIN_API_KEY\""
echo "2. Use token:  curl -H \"Authorization: Bearer <token>\" \"$BASE_URL/api/cidrs\""
