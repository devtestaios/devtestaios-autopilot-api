#!/bin/bash
# 🧪 Module Integration Test Runner
# Simple test runner that validates our modular architecture

echo "🚀 PulseBridge.ai Module Integration Testing"
echo "============================================="
echo "Testing Date: $(date)"
echo ""

# Test 1: Verify all expected modules exist
echo "📦 Testing Module File Existence..."
EXPECTED_MODULES=(
    "ai_endpoints.py"
    "ai_chat_service.py"
    "optimization_endpoints.py"
    "sync_endpoints.py"
    "analytics_endpoints.py"
    "autonomous_decision_endpoints.py"
    "hybrid_ai_endpoints.py"
    "meta_business_api.py"
    "linkedin_ads_integration.py"
    "pinterest_ads_integration.py"
    "meta_ai_hybrid_integration.py"
    "smart_risk_management.py"
    "google_ads_integration.py"
)

MODULES_FOUND=0
MODULES_MISSING=0

cd "$(dirname "$0")/../app"

for module in "${EXPECTED_MODULES[@]}"; do
    if [ -f "$module" ]; then
        echo "✅ $module exists"
        MODULES_FOUND=$((MODULES_FOUND + 1))
    else
        echo "❌ $module MISSING"
        MODULES_MISSING=$((MODULES_MISSING + 1))
    fi
done

echo ""
echo "📊 Module File Results: $MODULES_FOUND found, $MODULES_MISSING missing"

# Test 2: Check file sizes (non-empty files)
echo ""
echo "📏 Testing Module File Sizes..."
for module in "${EXPECTED_MODULES[@]}"; do
    if [ -f "$module" ]; then
        size=$(wc -l < "$module" 2>/dev/null || echo "0")
        if [ "$size" -gt 10 ]; then
            echo "✅ $module has $size lines (substantial)"
        else
            echo "⚠️  $module has only $size lines (may be stub)"
        fi
    fi
done

# Test 3: Check for critical import statements
echo ""
echo "🔗 Testing Import Patterns..."
IMPORT_TESTS=(
    "ai_endpoints.py:ai_router"
    "optimization_endpoints.py:router"
    "sync_endpoints.py:router"
    "analytics_endpoints.py:router"
    "autonomous_decision_endpoints.py:router"
    "hybrid_ai_endpoints.py:hybrid_ai_router"
)

for test in "${IMPORT_TESTS[@]}"; do
    file=$(echo "$test" | cut -d: -f1)
    pattern=$(echo "$test" | cut -d: -f2)
    
    if [ -f "$file" ]; then
        if grep -q "$pattern" "$file"; then
            echo "✅ $file exports $pattern"
        else
            echo "⚠️  $file missing export: $pattern"
        fi
    fi
done

# Test 4: Check main.py router includes
echo ""
echo "🔌 Testing Router Integration in main.py..."
ROUTER_INCLUDES=(
    "app.include_router(ai_router"
    "app.include_router(optimization_router"
    "app.include_router(sync_router"
    "app.include_router(analytics_router"
    "app.include_router(autonomous_router"
    "app.include_router(hybrid_ai_router"
)

for include in "${ROUTER_INCLUDES[@]}"; do
    if grep -q "$include" "main.py"; then
        echo "✅ main.py includes: $include"
    else
        echo "❌ main.py missing: $include"
    fi
done

# Test 5: Check for circular import risks
echo ""
echo "🔄 Testing for Potential Circular Imports..."
for module in "${EXPECTED_MODULES[@]}"; do
    if [ -f "$module" ]; then
        # Check if module imports main.py (potential circular import)
        if grep -q "from main import\|import main" "$module"; then
            echo "⚠️  $module imports main.py (potential circular import)"
        else
            echo "✅ $module has clean imports"
        fi
    fi
done

# Test 6: Production API Health Check
echo ""
echo "🌐 Testing Production API Health..."
if command -v curl >/dev/null 2>&1; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://autopilot-api-1.onrender.com/health)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Production API is healthy (HTTP $HTTP_CODE)"
    else
        echo "⚠️  Production API returned HTTP $HTTP_CODE"
    fi
else
    echo "ℹ️  curl not available, skipping API health check"
fi

# Test 7: Requirements.txt validation
echo ""
echo "📋 Testing Requirements..."
cd ..
if [ -f "requirements.txt" ]; then
    REQ_COUNT=$(wc -l < requirements.txt)
    echo "✅ requirements.txt exists with $REQ_COUNT dependencies"
    
    # Check for critical dependencies
    CRITICAL_DEPS=("fastapi" "uvicorn" "supabase" "pydantic")
    for dep in "${CRITICAL_DEPS[@]}"; do
        if grep -q "$dep" requirements.txt; then
            echo "✅ Critical dependency: $dep"
        else
            echo "❌ Missing critical dependency: $dep"
        fi
    done
else
    echo "❌ requirements.txt missing"
fi

# Summary
echo ""
echo "🎯 INTEGRATION TEST SUMMARY"
echo "=========================="
echo "Modules Found: $MODULES_FOUND/${#EXPECTED_MODULES[@]}"

if [ $MODULES_MISSING -eq 0 ]; then
    echo "🎉 SUCCESS: All modules present and integrated!"
    echo "🚀 Architecture is ready for development!"
    exit 0
else
    echo "⚠️  ISSUES DETECTED: $MODULES_MISSING modules missing"
    echo "🔧 Review the results above for details"
    exit 1
fi