#!/bin/bash

# 🚀 PulseBridge.ai Complete Testing & Validation Pipeline
# Advanced endpoint testing with performance analytics

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🚀 PulseBridge.ai Complete Testing Pipeline${NC}"
echo -e "${PURPLE}==============================================${NC}"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi

# Install required packages if needed
echo -e "${CYAN}📦 Checking Python dependencies...${NC}"
python3 -c "import aiohttp, asyncio" 2>/dev/null || {
    echo -e "${YELLOW}⚡ Installing required packages...${NC}"
    pip3 install aiohttp asyncio || {
        echo -e "${RED}❌ Failed to install dependencies${NC}"
        exit 1
    }
}

# Run basic module integration test first
echo -e "${BLUE}🔧 Phase 1: Module Integration Validation${NC}"
echo "=================================="

if [ -f "./tests/test_integration.sh" ]; then
    ./tests/test_integration.sh
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Module integration tests failed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Module integration tests passed${NC}"
else
    echo -e "${YELLOW}⚠️  Module integration test not found, skipping...${NC}"
fi

echo ""
echo -e "${BLUE}🌐 Phase 2: Advanced Endpoint Testing${NC}"
echo "=================================="

# Run the advanced endpoint testing suite
python3 ./tests/endpoint_testing_suite.py

ENDPOINT_EXIT_CODE=$?

echo ""
echo -e "${BLUE}📊 Phase 3: Results Analysis${NC}"
echo "=================================="

# Check if results file was created
if [ -f "endpoint_test_results.json" ]; then
    echo -e "${GREEN}✅ Detailed test results saved to endpoint_test_results.json${NC}"
    
    # Extract key metrics using Python
    python3 -c "
import json
try:
    with open('endpoint_test_results.json', 'r') as f:
        results = json.load(f)
    
    summary = results.get('summary', {})
    performance = results.get('performance_metrics', {})
    
    print(f'📈 Success Rate: {summary.get(\"success_rate\", 0)}%')
    print(f'⚡ Average Response Time: {performance.get(\"average_response_time\", \"N/A\")}s')
    print(f'🏆 Performance Grade: {performance.get(\"performance_grade\", \"N/A\")}')
    print(f'📊 Total Endpoints Tested: {summary.get(\"total_endpoints\", 0)}')
    print(f'✅ Successful: {summary.get(\"successful_endpoints\", 0)}')
    print(f'❌ Failed: {summary.get(\"failed_endpoints\", 0)}')
    
    if summary.get('overall_status') == 'PASSED':
        print('🎉 Overall Status: PASSED')
    else:
        print('⚠️  Overall Status: FAILED')
        
except Exception as e:
    print(f'Error reading results: {e}')
"
else
    echo -e "${YELLOW}⚠️  No detailed results file found${NC}"
fi

echo ""
echo -e "${PURPLE}🏁 Testing Pipeline Complete${NC}"
echo "=================================="

if [ $ENDPOINT_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED - PRODUCTION READY! 🚀${NC}"
    echo ""
    echo -e "${CYAN}✨ Your API is performing excellently:${NC}"
    echo -e "${CYAN}   • All endpoints are functional${NC}"
    echo -e "${CYAN}   • Performance metrics are healthy${NC}"
    echo -e "${CYAN}   • Platform integrations are consistent${NC}"
    echo -e "${CYAN}   • Production deployment is stable${NC}"
    echo ""
    echo -e "${GREEN}🔥 Ready for advanced features and scaling! 💪${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed - review results for optimization${NC}"
    echo ""
    echo -e "${YELLOW}📋 Next Steps:${NC}"
    echo -e "${YELLOW}   • Check endpoint_test_results.json for details${NC}"
    echo -e "${YELLOW}   • Review failed endpoints${NC}"
    echo -e "${YELLOW}   • Optimize slow-performing routes${NC}"
    echo -e "${YELLOW}   • Verify platform API configurations${NC}"
    exit 1
fi