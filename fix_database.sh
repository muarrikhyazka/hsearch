#!/bin/bash

echo "🔧 Fixing database transaction issue..."
echo "===================================="

# Restart PostgreSQL to clear transaction locks
echo "1. Restarting PostgreSQL container..."
docker compose restart postgres

echo "2. Waiting for PostgreSQL to be ready..."
sleep 10

echo "3. Testing database connection..."
docker exec hs_postgres psql -U hsearch_user -d hsearch_db -c "SELECT version();" || echo "Still not ready, waiting more..."
sleep 5

echo "4. Checking record count..."
docker exec hs_postgres psql -U hsearch_user -d hsearch_db -c "SELECT COUNT(*) FROM hs_codes;"

echo "5. Restarting backend to reconnect..."
docker compose restart backend

echo "6. Waiting for backend..."
sleep 15

echo "7. Testing API health..."
curl -s http://localhost:5000/api/health | grep -o '"database":"[^"]*"'

echo -e "\n8. Testing search..."
curl -s "http://localhost:5000/api/search?q=horse&limit=1" | head -3

echo -e "\n✅ Database fix complete!"