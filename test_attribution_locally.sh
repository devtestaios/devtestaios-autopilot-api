#!/bin/bash

# Local Attribution Engine Test Script
# Tests all attribution functionality locally before production deployment

echo "🚀 Attribution Engine Local Test Suite"
echo "======================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URL (change if running on different port)
BASE_URL="http://localhost:8000"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

# Function to test endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_status=$5

    echo ""
    echo "Testing: $name"
    echo "Endpoint: $method $endpoint"

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "$expected_status" ]; then
        print_result 0 "$name"
        echo "Response: $(echo $body | jq -r '.' 2>/dev/null || echo $body | head -c 100)"
    else
        print_result 1 "$name (Expected $expected_status, got $http_code)"
        echo "Response: $(echo $body | jq -r '.' 2>/dev/null || echo $body)"
    fi

    # Return body for use in subsequent tests
    echo "$body"
}

# Check if server is running
echo "Checking if server is running at $BASE_URL..."
if ! curl -s "$BASE_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}✗ Server not running at $BASE_URL${NC}"
    echo ""
    echo "To start the server:"
    echo "  cd /path/to/autopilot-api"
    echo "  uvicorn app.main:app --reload"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ Server is running${NC}"
echo ""

# Test 1: Health Check
test_endpoint "Health Check" "GET" "/api/v1/attribution/health" "" "200" > /tmp/health.json

# Test 2: Models Status
test_endpoint "Models Status" "GET" "/api/v1/attribution/models/status" "" "200" > /tmp/models.json

# Generate unique user ID for this test run
USER_ID="test_user_$(date +%s)"
echo ""
echo -e "${YELLOW}Using test user: $USER_ID${NC}"

# Test 3: Track First Touchpoint (Meta)
echo ""
TOUCHPOINT1='{
  "user_id": "'$USER_ID'",
  "event_type": "click",
  "platform": "meta",
  "campaign_id": "meta_campaign_001",
  "campaign_name": "Meta Brand Awareness",
  "utm_source": "meta",
  "utm_medium": "cpc",
  "country": "US",
  "device_type": "mobile"
}'
response=$(test_endpoint "Track Meta Touchpoint" "POST" "/api/v1/attribution/track/event" "$TOUCHPOINT1" "200")
JOURNEY_ID=$(echo $response | jq -r '.journey_id' 2>/dev/null)
echo "Journey ID: $JOURNEY_ID"

# Test 4: Track Second Touchpoint (Google)
echo ""
TOUCHPOINT2='{
  "user_id": "'$USER_ID'",
  "event_type": "click",
  "platform": "google_search",
  "campaign_id": "google_campaign_001",
  "campaign_name": "Google Search Brand",
  "utm_source": "google",
  "utm_medium": "cpc",
  "country": "US",
  "device_type": "desktop"
}'
response=$(test_endpoint "Track Google Touchpoint" "POST" "/api/v1/attribution/track/event" "$TOUCHPOINT2" "200")
JOURNEY_ID2=$(echo $response | jq -r '.journey_id' 2>/dev/null)

# Verify same journey
if [ "$JOURNEY_ID" = "$JOURNEY_ID2" ]; then
    print_result 0 "Touchpoints in same journey"
else
    print_result 1 "Touchpoints should be in same journey (got $JOURNEY_ID vs $JOURNEY_ID2)"
fi

# Test 5: Track Third Touchpoint (LinkedIn)
echo ""
TOUCHPOINT3='{
  "user_id": "'$USER_ID'",
  "event_type": "click",
  "platform": "linkedin",
  "campaign_id": "linkedin_campaign_001",
  "campaign_name": "LinkedIn Retargeting"
}'
test_endpoint "Track LinkedIn Touchpoint" "POST" "/api/v1/attribution/track/event" "$TOUCHPOINT3" "200" > /dev/null

# Test 6: Track Conversion
echo ""
CONVERSION='{
  "user_id": "'$USER_ID'",
  "conversion_type": "purchase",
  "revenue": 199.99,
  "order_id": "order_test_'$(date +%s)'",
  "product_ids": ["prod_test_001", "prod_test_002"]
}'
test_endpoint "Track Conversion" "POST" "/api/v1/attribution/track/conversion" "$CONVERSION" "200" > /dev/null

# Wait for background attribution to complete
echo ""
echo "Waiting 3 seconds for background attribution analysis..."
sleep 3

# Test 7: Analyze Journey with Shapley
echo ""
ANALYZE_SHAPLEY='{
  "user_id": "'$USER_ID'",
  "model_type": "shapley"
}'
response=$(test_endpoint "Analyze Journey (Shapley)" "POST" "/api/v1/attribution/analyze/journey" "$ANALYZE_SHAPLEY" "200")

# Validate Shapley response
echo ""
echo "Validating Shapley Attribution Results..."
converted=$(echo $response | jq -r '.converted' 2>/dev/null)
conversion_value=$(echo $response | jq -r '.conversion_value' 2>/dev/null)
total_touchpoints=$(echo $response | jq -r '.total_touchpoints' 2>/dev/null)
unique_platforms=$(echo $response | jq -r '.unique_platforms' 2>/dev/null)

if [ "$converted" = "true" ]; then
    print_result 0 "Journey marked as converted"
else
    print_result 1 "Journey should be converted"
fi

if [ "$conversion_value" = "199.99" ]; then
    print_result 0 "Conversion value correct ($199.99)"
else
    print_result 1 "Conversion value incorrect (expected 199.99, got $conversion_value)"
fi

if [ "$total_touchpoints" = "3" ]; then
    print_result 0 "Total touchpoints correct (3)"
else
    print_result 1 "Total touchpoints incorrect (expected 3, got $total_touchpoints)"
fi

if [ "$unique_platforms" = "3" ]; then
    print_result 0 "Unique platforms correct (3)"
else
    print_result 1 "Unique platforms incorrect (expected 3, got $unique_platforms)"
fi

# Validate attribution credits sum to 1.0
credits_sum=$(echo $response | jq '[.platform_attribution[].credit] | add' 2>/dev/null)
if (( $(echo "$credits_sum > 0.99 && $credits_sum < 1.01" | bc -l) )); then
    print_result 0 "Attribution credits sum to ~1.0 ($credits_sum)"
else
    print_result 1 "Attribution credits should sum to 1.0 (got $credits_sum)"
fi

# Validate revenue distribution
revenue_sum=$(echo $response | jq '[.platform_attribution[].revenue_attributed] | add' 2>/dev/null)
if (( $(echo "$revenue_sum > 199.8 && $revenue_sum < 200.1" | bc -l) )); then
    print_result 0 "Revenue correctly distributed ($revenue_sum)"
else
    print_result 1 "Revenue distribution incorrect (expected ~199.99, got $revenue_sum)"
fi

# Check for insights
insights_count=$(echo $response | jq '.insights | length' 2>/dev/null)
if [ "$insights_count" -gt 0 ]; then
    print_result 0 "Insights generated ($insights_count insights)"
    echo "Insights:"
    echo $response | jq -r '.insights[]' 2>/dev/null | sed 's/^/  - /'
else
    print_result 1 "No insights generated"
fi

# Test 8: Analyze Journey with Markov
echo ""
ANALYZE_MARKOV='{
  "user_id": "'$USER_ID'",
  "model_type": "markov"
}'
response=$(test_endpoint "Analyze Journey (Markov)" "POST" "/api/v1/attribution/analyze/journey" "$ANALYZE_MARKOV" "200")
model_type=$(echo $response | jq -r '.model_type' 2>/dev/null)

if [ "$model_type" = "markov" ] || [ "$model_type" = "linear" ]; then
    print_result 0 "Markov attribution completed (model: $model_type)"
else
    print_result 1 "Markov attribution failed"
fi

# Test 9: Batch Analysis
echo ""
# Create 2 more users for batch test
USER2="batch_user_1_$(date +%s)"
USER3="batch_user_2_$(date +%s)"

# Quick journey for user 2
curl -s -X POST "$BASE_URL/api/v1/attribution/track/event" -H "Content-Type: application/json" \
    -d '{"user_id":"'$USER2'","event_type":"click","platform":"meta"}' > /dev/null
curl -s -X POST "$BASE_URL/api/v1/attribution/track/conversion" -H "Content-Type: application/json" \
    -d '{"user_id":"'$USER2'","conversion_type":"purchase","revenue":100.00}' > /dev/null

# Quick journey for user 3
curl -s -X POST "$BASE_URL/api/v1/attribution/track/event" -H "Content-Type: application/json" \
    -d '{"user_id":"'$USER3'","event_type":"click","platform":"google_ads"}' > /dev/null
curl -s -X POST "$BASE_URL/api/v1/attribution/track/conversion" -H "Content-Type: application/json" \
    -d '{"user_id":"'$USER3'","conversion_type":"purchase","revenue":150.00}' > /dev/null

BATCH_ANALYZE='{
  "user_ids": ["'$USER_ID'", "'$USER2'", "'$USER3'"],
  "model_type": "shapley"
}'
response=$(test_endpoint "Batch Analysis (3 journeys)" "POST" "/api/v1/attribution/analyze/batch" "$BATCH_ANALYZE" "200")

total_journeys=$(echo $response | jq -r '.total_journeys' 2>/dev/null)
total_revenue=$(echo $response | jq -r '.total_revenue' 2>/dev/null)

if [ "$total_journeys" = "3" ]; then
    print_result 0 "Batch analysis processed 3 journeys"
else
    print_result 1 "Batch analysis should process 3 journeys (got $total_journeys)"
fi

if (( $(echo "$total_revenue > 449 && $total_revenue < 451" | bc -l) )); then
    print_result 0 "Batch total revenue correct (~$449.99)"
else
    print_result 1 "Batch total revenue incorrect (expected ~449.99, got $total_revenue)"
fi

# Summary
echo ""
echo "======================================="
echo "Test Results Summary"
echo "======================================="
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Attribution engine is working correctly.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Deploy to Render (resume service)"
    echo "2. Run production tests using ATTRIBUTION_ENGINE_PRODUCTION_TEST_PLAN.md"
    echo "3. Proceed to Phase 2: Platform Integrations"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review errors above.${NC}"
    exit 1
fi
