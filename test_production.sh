#!/bin/bash

# Production API Testing Script
# Tests all critical endpoints to find 404 errors

echo "======================================"
echo "PulseBridge API Production Test"
echo "======================================"
echo ""

# Set your Render URL here
API_URL="${1:-https://your-app.onrender.com}"

echo "Testing API at: $API_URL"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_endpoint() {
    local name=$1
    local endpoint=$2
    local method=${3:-GET}

    echo -n "Testing $name... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL$endpoint")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d '{}')
    fi

    if [ "$response" = "404" ]; then
        echo -e "${RED}404 NOT FOUND${NC}"
        return 1
    elif [ "$response" = "200" ] || [ "$response" = "201" ]; then
        echo -e "${GREEN}$response OK${NC}"
        return 0
    elif [ "$response" = "401" ] || [ "$response" = "422" ]; then
        echo -e "${YELLOW}$response (Expected - endpoint exists)${NC}"
        return 0
    else
        echo -e "${YELLOW}$response${NC}"
        return 0
    fi
}

# Track failures
failures=0

# Test root endpoints
echo "=== Root Endpoints ==="
test_endpoint "Root" "/" || ((failures++))
test_endpoint "Health" "/health" || ((failures++))
test_endpoint "Docs" "/docs" || ((failures++))
test_endpoint "OpenAPI" "/openapi.json" || ((failures++))
echo ""

# Test onboarding endpoints
echo "=== Onboarding Endpoints ==="
test_endpoint "Suite Catalog" "/api/v1/onboarding/suite-catalog" || ((failures++))
test_endpoint "Company Profile" "/api/v1/onboarding/company-profile" POST || ((failures++))
test_endpoint "Calculate Pricing" "/api/v1/onboarding/calculate-pricing" POST || ((failures++))
echo ""

# Test admin endpoints (should return 401, not 404)
echo "=== Admin Endpoints (should return 401 Unauthorized) ==="
test_endpoint "Admin Login" "/api/v1/auth/admin/login" POST || ((failures++))
test_endpoint "Admin Users List" "/api/v1/admin/users/internal" || ((failures++))
test_endpoint "Admin Test Token" "/api/v1/auth/admin/test-token" || ((failures++))
echo ""

# Test billing endpoints
echo "=== Billing Endpoints ==="
test_endpoint "Billing Status" "/api/v1/billing/status/test@example.com" || ((failures++))
test_endpoint "Bypass Users" "/api/v1/billing/bypass/all-users" || ((failures++))
echo ""

# Summary
echo "======================================"
if [ $failures -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ $failures endpoint(s) returned 404${NC}"
    echo ""
    echo "Common fixes:"
    echo "1. Check Render deployment logs for errors"
    echo "2. Verify all routers are registered in main.py"
    echo "3. Check environment variables are set"
    echo "4. Ensure PyJWT is in requirements.txt"
fi
echo "======================================"
