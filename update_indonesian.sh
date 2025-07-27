#!/bin/bash

# Indonesian Translation Update Script
# Run this to update existing deployment with Indonesian translation support

set -e

echo "🇮🇩 Starting Indonesian Translation Update..."
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if containers are running
print_status "Checking existing deployment..."
if ! docker compose ps | grep -q "Up"; then
    print_error "No running containers found. Please run ./deploy.sh first for initial deployment."
    exit 1
fi

print_success "Existing deployment found"

# Pull latest changes
print_status "Pulling latest changes with Indonesian translations..."
if git pull origin main; then
    print_success "Repository updated successfully"
else
    print_error "Failed to pull latest changes"
    exit 1
fi

# Check if translated dataset exists
print_status "Checking for Indonesian translation dataset..."
if [ ! -f "data/final-dataset-translated.csv" ]; then
    print_error "Indonesian translation dataset not found: data/final-dataset-translated.csv"
    print_error "Please ensure the translated dataset is available"
    exit 1
fi

# Check dataset size
data_size=$(du -h data/final-dataset-translated.csv | cut -f1)
print_status "Indonesian dataset size: $data_size"

# Count records
record_count=$(wc -l < data/final-dataset-translated.csv)
print_status "Total records in Indonesian dataset: $((record_count-1))"

# Stop backend to rebuild with new data
print_status "Stopping backend container for update..."
docker compose stop backend

# Rebuild backend container with new dataset
print_status "Rebuilding backend container with Indonesian dataset..."
print_status "This may take a few minutes..."
if docker compose build --no-cache backend; then
    print_success "Backend rebuilt successfully"
else
    print_error "Failed to rebuild backend"
    exit 1
fi

# Start backend
print_status "Starting updated backend container..."
if docker compose start backend; then
    print_success "Backend started successfully"
else
    print_error "Failed to start backend"
    exit 1
fi

# Wait for backend to be ready
print_status "Waiting for backend to be ready..."
sleep 20

# Check if backend can access the translated dataset
print_status "Verifying access to Indonesian dataset..."
if docker compose exec -T backend ls -la /app/data/final-dataset-translated.csv > /dev/null 2>&1; then
    print_success "Indonesian dataset accessible from container"
else
    print_error "Indonesian dataset not accessible from container"
    print_status "Available files in data directory:"
    docker compose exec -T backend ls -la /app/data/
    exit 1
fi

# Import Indonesian translation data
print_status "Importing HS Code data with Indonesian translations..."
print_status "This will update the database with bilingual support..."

# Try import with retry mechanism
max_retries=3
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    print_status "Import attempt $((retry_count + 1))/$max_retries..."
    
    if docker compose exec -T backend python /app/backend/import_data.py; then
        print_success "Indonesian translation data imported successfully"
        break
    else
        retry_count=$((retry_count + 1))
        if [ $retry_count -lt $max_retries ]; then
            print_warning "Import attempt $retry_count failed, retrying in 10 seconds..."
            print_status "Backend logs:"
            docker compose logs --tail=10 backend
            sleep 10
        else
            print_error "Import failed after $max_retries attempts"
            print_status "Backend logs:"
            docker compose logs --tail=20 backend
            print_status "Database logs:"
            docker compose logs --tail=10 postgres
            exit 1
        fi
    fi
done

# Verify import success
print_status "Verifying Indonesian translation import..."

# Check total record count
total_records=$(docker compose exec -T postgres psql -U hsearch_user -d hsearch_db -t -c "SELECT COUNT(*) FROM hs_codes;" 2>/dev/null | tr -d ' \n' || echo "0")

# Check Indonesian translation count
indonesian_records=$(docker compose exec -T postgres psql -U hsearch_user -d hsearch_db -t -c "SELECT COUNT(*) FROM hs_codes WHERE description_id IS NOT NULL AND description_id != '';" 2>/dev/null | tr -d ' \n' || echo "0")

print_status "Import verification results:"
echo "  • Total HS codes: $total_records"
echo "  • Indonesian translations: $indonesian_records"

if [ "$total_records" -gt "10000" ]; then
    print_success "Database verification passed: $total_records records"
else
    print_error "Database verification failed: only $total_records records found"
    exit 1
fi

if [ "$indonesian_records" -gt "0" ]; then
    print_success "Indonesian translations verified: $indonesian_records records"
else
    print_warning "No Indonesian translations found in database"
fi

# Test API endpoints
print_status "Testing updated API endpoints..."

# Test health endpoint
if curl -f -s http://localhost:5000/api/health > /dev/null; then
    print_success "API health check passed"
else
    print_warning "API health check failed"
fi

# Test search endpoint
if curl -f -s "http://localhost:5000/api/search?q=horse" > /dev/null; then
    print_success "Search endpoint responding"
else
    print_warning "Search endpoint test failed"
fi

# Show sample bilingual data
print_status "Sample bilingual HS code data:"
docker compose exec -T postgres psql -U hsearch_user -d hsearch_db -c "
SELECT 
    hs_code, 
    LEFT(description_en, 40) AS english_desc,
    LEFT(description_id, 40) AS indonesian_desc,
    category 
FROM hs_codes 
WHERE description_id IS NOT NULL AND description_id != ''
ORDER BY hs_code
LIMIT 5;
" 2>/dev/null || print_warning "Could not retrieve sample data"

# Final status
echo ""
print_success "🎉 Indonesian Translation Update Complete!"
echo "=========================================="
echo ""
print_status "Update Summary:"
echo "  • Total HS codes: $total_records"
echo "  • Indonesian translations: $indonesian_records" 
echo "  • Frontend: http://localhost"
echo "  • Backend API: http://localhost:5000"
echo ""
print_status "New Features Available:"
echo "  • Bilingual HS code descriptions (English + Indonesian)"
echo "  • Enhanced search with Indonesian language support"
echo "  • Multilingual vector embeddings for better search accuracy"
echo ""
print_status "Useful Commands:"
echo "  • View logs: docker compose logs -f"
echo "  • Restart services: docker compose restart"
echo "  • Check database: docker exec -it hs_postgres psql -U hsearch_user -d hsearch_db"
echo ""
print_success "Your HS Search system now supports Indonesian translations!"