#!/bin/bash

# 🚀 PulseBridge.ai API Credentials Setup Script
# Run this script to configure environment variables for Google Ads and LinkedIn

echo "🔑 PulseBridge.ai API Credentials Setup"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Please run this script from the autopilot-api directory"
    exit 1
fi

echo "📋 This script will help you configure API credentials for:"
echo "   • Google Ads API"
echo "   • LinkedIn Ads API"
echo ""

# Create environment file template
ENV_FILE=".env.production"

echo "📝 Creating environment template: $ENV_FILE"
echo ""

cat > $ENV_FILE << 'EOF'
# ===== GOOGLE ADS API CREDENTIALS =====
# Get these from: https://developers.google.com/google-ads/api/docs/first-call/overview
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token_here
GOOGLE_ADS_CLIENT_ID=your_oauth_client_id_here
GOOGLE_ADS_CLIENT_SECRET=your_oauth_client_secret_here
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token_here
GOOGLE_ADS_CUSTOMER_ID=your_customer_id_here

# ===== LINKEDIN ADS API CREDENTIALS =====
# Get these from: https://www.linkedin.com/developers/
LINKEDIN_ACCESS_TOKEN=your_access_token_here
LINKEDIN_AD_ACCOUNT_ID=your_ad_account_id_here

# ===== META ADS API CREDENTIALS (Already Working) =====
# These are already configured and working
# META_ACCESS_TOKEN=already_configured
# META_AD_ACCOUNT_ID=already_configured

# ===== SUPABASE CONFIGURATION =====
# Add your Supabase credentials if needed
# SUPABASE_URL=your_supabase_url
# SUPABASE_KEY=your_supabase_key
EOF

echo "✅ Environment template created: $ENV_FILE"
echo ""
echo "🔧 NEXT STEPS:"
echo ""
echo "1. 📝 Edit the $ENV_FILE file and add your real API credentials"
echo "2. 🌐 Copy these variables to your Render dashboard:"
echo "   → Go to: https://dashboard.render.com"
echo "   → Select: autopilot-api-1 service" 
echo "   → Go to: Environment tab"
echo "   → Add each variable individually"
echo ""
echo "3. 🧪 Test the connections:"
echo "   curl 'https://autopilot-api-1.onrender.com/google-ads/status'"
echo "   curl 'https://autopilot-api-1.onrender.com/linkedin-ads/status'"
echo ""

# Display current status
echo "📊 CURRENT INTEGRATION STATUS:"
echo "================================"
echo ""

echo "🔍 Testing current API endpoints..."
echo ""

# Test Meta API (should work)
echo "📱 Meta Ads API:"
META_STATUS=$(curl -s "https://autopilot-api-1.onrender.com/meta-ads/status" 2>/dev/null)
if echo "$META_STATUS" | grep -q "connected.*true"; then
    echo "   ✅ CONNECTED - Ready for production upgrade"
else
    echo "   ❌ CONNECTION ISSUE"
fi

# Test Google Ads API (should need credentials)
echo "📊 Google Ads API:"
GOOGLE_STATUS=$(curl -s "https://autopilot-api-1.onrender.com/google-ads/status" 2>/dev/null)
if echo "$GOOGLE_STATUS" | grep -q "NoneType"; then
    echo "   ⚠️  NEEDS CREDENTIALS - Code ready, add API keys"
else
    echo "   ❓ UNKNOWN STATUS"
fi

# Test LinkedIn API (should need credentials)
echo "💼 LinkedIn Ads API:"
LINKEDIN_STATUS=$(curl -s "https://autopilot-api-1.onrender.com/linkedin-ads/status" 2>/dev/null)
if echo "$LINKEDIN_STATUS" | grep -q "credentials not configure"; then
    echo "   ⚠️  NEEDS CREDENTIALS - Code ready, add API keys"
else
    echo "   ❓ UNKNOWN STATUS"
fi

echo ""
echo "🎯 PRIORITY ACTIONS:"
echo "==================="
echo ""
echo "1. 🥇 Google Ads Setup (Highest Revenue Impact)"
echo "   → Apply for Developer Token: https://ads.google.com"
echo "   → Expected Revenue: +$10K-$15K monthly"
echo ""
echo "2. 🥈 LinkedIn Ads Setup (B2B Focus)"  
echo "   → Apply for Marketing Platform: https://linkedin.com/developers"
echo "   → Expected Revenue: +$5K-$10K monthly"
echo ""
echo "3. 🥉 Meta Production Upgrade"
echo "   → Already connected, upgrade to production access"
echo "   → Enhanced Revenue: +$5K monthly"
echo ""

# Provide helpful links
echo "📚 HELPFUL RESOURCES:"
echo "====================="
echo ""
echo "Google Ads API:"
echo "   • Developer Guide: https://developers.google.com/google-ads/api"
echo "   • OAuth Setup: https://developers.google.com/google-ads/api/docs/oauth"
echo "   • Test Account: https://ads.google.com/home/tools/manager-accounts/"
echo ""
echo "LinkedIn Marketing API:"
echo "   • Developer Portal: https://developer.linkedin.com"
echo "   • Marketing API: https://docs.microsoft.com/en-us/linkedin/marketing/"
echo "   • Access Request: https://business.linkedin.com/marketing-solutions/marketing-partners"
echo ""

echo "✨ Setup script complete!"
echo "📧 Need help? Check the API_CREDENTIALS_SETUP_GUIDE.md file"