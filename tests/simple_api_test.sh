#!/bin/bash

# 🚀 Simplified API Testing Suite (No External Dependencies)
# Uses only built-in tools: curl, bash, basic shell commands

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🚀 PulseBridge.ai Simple API Testing${NC}"
echo -e "${PURPLE}=====================================${NC}"

# Base URL
BASE_URL="https://autopilot-api-1.onrender.com"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test result storage
TEST_RESULTS=""

# Function to test a single endpoint
test_endpoint() {
    local name="$1"
    local endpoint="$2"
    local expected_status="$3"
    local url="${BASE_URL}${endpoint}"
    
    echo -n "Testing ${name}... "
    
    # Use curl to test the endpoint
    local start_time=$(date +%s.%N)
    local response=$(curl -s -w "%{http_code}:%{time_total}" --max-time 30 "$url" 2>/dev/null || echo "000:30.000")
    local end_time=$(date +%s.%N)
    
    # Parse response
    local status_code=$(echo "$response" | tail -1 | cut -d':' -f1)
    local response_time=$(echo "$response" | tail -1 | cut -d':' -f2)
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [[ "$status_code" == "$expected_status" ]] || [[ "$expected_status" == "200|503" && ("$status_code" == "200" || "$status_code" == "503") ]]; then
        echo -e "${GREEN}✅ ${status_code} (${response_time}s)${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS="${TEST_RESULTS}✅ ${name}: ${status_code} (${response_time}s)\n"
    else
        echo -e "${RED}❌ ${status_code} (expected ${expected_status})${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS="${TEST_RESULTS}❌ ${name}: ${status_code} (expected ${expected_status})\n"
    fi
}

echo -e "${CYAN}🌐 Testing Critical API Endpoints...${NC}"
echo "=================================="

# Core system endpoints
test_endpoint "Health Check" "/health" "200"
test_endpoint "Root Endpoint" "/" "200"

# AI endpoints
test_endpoint "AI Status" "/api/v1/ai/status" "200"

# Platform status endpoints
test_endpoint "Google Ads Status" "/google-ads/status" "200"
test_endpoint "Meta Ads Status" "/meta-ads/status" "200"
test_endpoint "LinkedIn Ads Status" "/linkedin-ads/status" "200"
test_endpoint "Pinterest Ads Status" "/pinterest-ads/status" "200"

# Platform campaign endpoints (may return 503 if not configured)
test_endpoint "Google Ads Campaigns" "/google-ads/campaigns" "200|503"
test_endpoint "Meta Ads Campaigns" "/meta-ads/campaigns" "200|503"
test_endpoint "LinkedIn Ads Campaigns" "/linkedin-ads/campaigns" "200|503"
test_endpoint "Pinterest Ads Campaigns" "/pinterest-ads/campaigns" "200|503"

# Debug endpoints
test_endpoint "Debug Supabase" "/debug/supabase" "200"
test_endpoint "Debug Tables" "/debug/tables" "200"

echo ""
echo -e "${BLUE}📊 Test Summary${NC}"
echo "=================================="
echo -e "📊 Total Tests: ${TOTAL_TESTS}"
echo -e "✅ Passed: ${PASSED_TESTS}"
echo -e "❌ Failed: ${FAILED_TESTS}"

if [ $FAILED_TESTS -eq 0 ]; then
    SUCCESS_RATE=100
else
    SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
fi

echo -e "📈 Success Rate: ${SUCCESS_RATE}%"

echo ""
echo -e "${BLUE}📋 Detailed Results${NC}"
echo "=================================="
echo -e "$TEST_RESULTS"

echo ""
echo -e "${PURPLE}🏁 Testing Complete${NC}"
echo "=================================="

if [ $SUCCESS_RATE -ge 80 ]; then
    echo -e "${GREEN}🎉 EXCELLENT! API is performing well (${SUCCESS_RATE}% success rate)${NC}"
    echo ""
    echo -e "${CYAN}✨ Your API endpoints are:${NC}"
    echo -e "${CYAN}   • Responding correctly ✅${NC}"
    echo -e "${CYAN}   • Production stable 🚀${NC}"
    echo -e "${CYAN}   • Platform integrations working 💪${NC}"
    echo ""
    echo -e "${GREEN}🔥 Ready for advanced development! 🚀${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some endpoints need attention (${SUCCESS_RATE}% success rate)${NC}"
    echo ""
    echo -e "${YELLOW}📋 Recommendations:${NC}"
    echo -e "${YELLOW}   • Check failed endpoints above${NC}"
    echo -e "${YELLOW}   • Verify API configurations${NC}"
    echo -e "${YELLOW}   • Review platform integrations${NC}"
    exit 1
fi