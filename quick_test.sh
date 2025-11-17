#!/bin/bash
# Quick API Test Script
# This script provides a quick way to test your API endpoints

BASE_URL="${1:-http://localhost:8050}"

echo "🧪 Quick API Test for: $BASE_URL"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test health endpoint
echo "1. Testing Health Endpoint..."
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/health")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✅ Health check passed${NC}"
    echo "   Response: $body"
else
    echo -e "${RED}❌ Health check failed (HTTP $http_code)${NC}"
    exit 1
fi

echo ""

# Test search endpoint
echo "2. Testing Search Endpoint..."
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/search/tests")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    count=$(echo "$body" | grep -o '"count":[0-9]*' | grep -o '[0-9]*' || echo "0")
    echo -e "${GREEN}✅ Search endpoint working${NC}"
    echo "   Found $count tests"
else
    echo -e "${RED}❌ Search endpoint failed (HTTP $http_code)${NC}"
fi

echo ""

# Test invalid endpoint (should return 404)
echo "3. Testing Error Handling (404)..."
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/nonexistent")
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" -eq 404 ]; then
    echo -e "${GREEN}✅ Error handling working (404)${NC}"
else
    echo -e "${YELLOW}⚠️  Expected 404 but got $http_code${NC}"
fi

echo ""
echo "=================================="
echo -e "${GREEN}Quick test completed!${NC}"
echo ""
echo "For comprehensive testing, run:"
echo "  python3 test_api.py $BASE_URL"

