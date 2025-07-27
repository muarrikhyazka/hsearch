#!/bin/bash

echo "🔍 Testing HS Search functionality..."
echo "=================================="

# Test 1: Check if API is responding
echo "1. Testing API health..."
curl -s http://localhost:5000/api/health | head -3

echo -e "\n2. Testing database record count..."
curl -s "http://localhost:5000/api/search?q=test&limit=1" | grep -o '"total":[0-9]*'

echo -e "\n3. Testing simple search..."
curl -s -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "horse", "limit": 3}' | head -5

echo -e "\n4. Testing GET search..."
curl -s "http://localhost:5000/api/search?q=horse&limit=3" | head -5

echo -e "\n5. Direct database test..."
docker exec hs_postgres psql -U hsearch_user -d hsearch_db -c "SELECT COUNT(*) FROM hs_codes;"

echo -e "\n6. Sample data from database..."
docker exec hs_postgres psql -U hsearch_user -d hsearch_db -c "SELECT hs_code, LEFT(description_en, 30) as desc FROM hs_codes LIMIT 3;"

echo -e "\n7. Search test in database..."
docker exec hs_postgres psql -U hsearch_user -d hsearch_db -c "SELECT hs_code, LEFT(description_en, 30) as desc FROM hs_codes WHERE description_en ILIKE '%horse%' LIMIT 3;"