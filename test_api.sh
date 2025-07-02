#!/bin/bash

# API Testing Script
# This script demonstrates how to test the OAuth flow

BASE_URL="http://localhost:8000"

echo "🚀 Testing FastAPI OAuth Application"
echo "======================================"

# Test public endpoint
echo "📍 Testing public endpoint..."
curl -s "$BASE_URL/api/" | jq '.'

echo -e "\n📍 Getting login URL..."
LOGIN_RESPONSE=$(curl -s "$BASE_URL/auth/login")
echo "$LOGIN_RESPONSE" | jq '.'

# Extract the auth URL
AUTH_URL=$(echo "$LOGIN_RESPONSE" | jq -r '.auth_url')

echo -e "\n🔗 OAuth Login URL:"
echo "$AUTH_URL"

echo -e "\n📋 Next Steps:"
echo "1. Copy the auth URL above"
echo "2. Open it in your browser"
echo "3. Complete the OAuth login"
echo "4. Copy the access_token from the callback response"
echo "5. Use the token to test protected endpoints:"
echo ""
echo "   curl -H \"Authorization: Bearer YOUR_TOKEN\" $BASE_URL/auth/me"
echo "   curl -H \"Authorization: Bearer YOUR_TOKEN\" $BASE_URL/api/protected"
echo "   curl -H \"Authorization: Bearer YOUR_TOKEN\" $BASE_URL/api/profile"

echo -e "\n🔍 You can also visit the interactive docs at:"
echo "   $BASE_URL/docs"
