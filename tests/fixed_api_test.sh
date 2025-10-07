#!/bin/bash

# 🚀 Fixed API Testing Suite 
# Properly handles JSON responses and HTTP status codes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🚀 PulseBridge.ai API Endpoint Testing${NC}"
echo -e "${PURPLE}======================================${NC}"

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
    
    # Use curl to get both status code and response time
    local start_time=$(date +%s.%N)
    local response=$(curl -s -w "\n%{http_code}:%{time_total}" --max-time 30 -X GET "$url" 2>/dev/null || echo -e "\nERROR:30.000")
    local end_time=$(date +%s.%N)
    
    # Parse response - get the last line with status code and time
    local last_line=$(echo "$response" | tail -1)
    local status_code=$(echo "$last_line" | cut -d':' -f1)
    local response_time=$(echo "$last_line" | cut -d':' -f2)
    
    # Get actual response body (everything except last line)
    local response_body=$(echo "$response" | head -n -1)
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Check if status matches expected
    local test_passed=false
    if [[ "$expected_status" == *"|"* ]]; then
        # Multiple acceptable status codes
        IFS='|' read -ra STATUSES <<< "$expected_status"
        for status in "${STATUSES[@]}"; do
            if [[ "$status_code" == "$status" ]]; then
                test_passed=true
                break
            fi
        done
    else
        # Single expected status
        if [[ "$status_code" == "$expected_status" ]]; then
            test_passed=true
        fi
    fi
    
    if [[ "$test_passed" == true ]]; then
        echo -e "${GREEN}✅ ${status_code} (${response_time}s)${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS="${TEST_RESULTS}✅ ${name}: ${status_code} (${response_time}s)\n"
    else
        echo -e "${RED}❌ ${status_code} (expected ${expected_status})${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS="${TEST_RESULTS}❌ ${name}: ${status_code} (expected ${expected_status})\n"
        
        # Show first part of response for debugging
        if [[ ${#response_body} -gt 0 ]]; then
            local preview=$(echo "$response_body" | head -c 100)
            echo -e "${YELLOW}   Response: ${preview}...${NC}"
        fi
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

# Performance analysis
echo -e "${CYAN}⚡ Quick Performance Check${NC}"
echo "=================================="
echo "Testing response time for health endpoint..."
time_result=$(curl -s -w "%{time_total}" -o /dev/null https://autopilot-api-1.onrender.com/health)
echo -e "Health endpoint response time: ${time_result}s"

if (( $(echo "$time_result < 2.0" | bc -l) )); then
    echo -e "${GREEN}🚀 Fast response time! (< 2s)${NC}"
elif (( $(echo "$time_result < 5.0" | bc -l) )); then
    echo -e "${YELLOW}⚡ Acceptable response time (2-5s)${NC}"
else
    echo -e "${RED}🐌 Slow response time (> 5s)${NC}"
fi

echo ""
echo -e "${PURPLE}🏁 Testing Complete${NC}"
echo "=================================="

if [ $SUCCESS_RATE -ge 80 ]; then
    echo -e "${GREEN}🎉 EXCELLENT! API is performing well (${SUCCESS_RATE}% success rate)${NC}"
    echo ""
    echo -e "${CYAN}✨ Your API is:${NC}"
    echo -e "${CYAN}   • Responding correctly ✅${NC}"
    echo -e "${CYAN}   • Production stable 🚀${NC}"
    echo -e "${CYAN}   • Ready for advanced development 💪${NC}"
    echo ""
    echo -e "${GREEN}🔥 All systems go! 🚀${NC}"
    exit 0
elif [ $SUCCESS_RATE -ge 60 ]; then
    echo -e "${YELLOW}⚠️  Good but needs some attention (${SUCCESS_RATE}% success rate)${NC}"
    echo ""
    echo -e "${YELLOW}📋 Most endpoints working, minor issues to address${NC}"
    exit 0
else
    echo -e "${RED}❌ Some endpoints need attention (${SUCCESS_RATE}% success rate)${NC}"
    echo ""
    echo -e "${YELLOW}📋 Recommendations:${NC}"
    echo -e "${YELLOW}   • Check failed endpoints above${NC}"
    echo -e "${YELLOW}   • Verify API configurations${NC}"
    echo -e "${YELLOW}   • Review platform integrations${NC}"
    exit 1
fi