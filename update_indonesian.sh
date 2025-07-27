#!/bin/bash

# Indonesian Translation Update Script
# Quick update for existing deployments

set -e

echo "🇮🇩 Updating with Indonesian Translations..."
echo "=========================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if containers are running
if ! docker compose ps | grep -q "Up"; then
    print_error "No running deployment found. Run ./deploy.sh first."
    exit 1
fi

# Quick update process
print_status "Pulling latest changes..."
git pull origin main

print_status "Checking Indonesian dataset..."
if [ ! -f "data/final-dataset-translated.csv" ]; then
    print_error "Indonesian dataset not found"
    exit 1
fi

print_status "Rebuilding backend with new data..."
docker compose stop backend
docker compose build --no-cache backend
docker compose start backend

print_status "Waiting for backend..."
sleep 15

print_status "Checking container file structure..."
docker compose exec -T backend ls -la /app/

# Find the correct path for import_data.py
if docker compose exec -T backend test -f /app/import_data.py; then
    IMPORT_PATH="/app/import_data.py"
elif docker compose exec -T backend test -f /app/backend/import_data.py; then
    IMPORT_PATH="/app/backend/import_data.py"
else
    print_error "import_data.py not found in container"
    exit 1
fi

print_status "Found import script at: $IMPORT_PATH"
print_status "Importing Indonesian translations..."
if docker compose exec -T backend python "$IMPORT_PATH"; then
    print_success "Import completed"
else
    print_error "Import failed"
    exit 1
fi

# Quick verification
total=$(docker compose exec -T postgres psql -U hsearch_user -d hsearch_db -t -c "SELECT COUNT(*) FROM hs_codes;" 2>/dev/null | tr -d ' \n' || echo "0")
indonesian=$(docker compose exec -T postgres psql -U hsearch_user -d hsearch_db -t -c "SELECT COUNT(*) FROM hs_codes WHERE description_id IS NOT NULL AND description_id != '';" 2>/dev/null | tr -d ' \n' || echo "0")

echo ""
print_success "🎉 Update Complete!"
echo "  • Total records: $total"
echo "  • Indonesian translations: $indonesian"
echo "  • Access: http://localhost"