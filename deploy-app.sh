#!/bin/bash

# HSSearch Application Deployment Script (No Data Import)
# Deploys only the application stack without importing data
# Usage: ./deploy-app.sh

set -e  # Exit on any error

echo "🚀 Deploying HSSearch Application Stack..."
echo "========================================"

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

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please don't run this script as root"
    exit 1
fi

# Step 1: Git Pull Latest Changes
print_status "Pulling latest changes from repository..."
if git pull origin main; then
    print_success "Repository updated successfully"
else
    print_error "Failed to pull latest changes"
    exit 1
fi

# Step 2: Check Docker Installation
print_status "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    print_status "Please install Docker first: https://docs.docker.com/engine/install/"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    print_error "Docker Compose is not installed"
    print_status "Please install Docker Compose first"
    exit 1
fi

print_success "Docker and Docker Compose are available"

# Step 3: Create Required Directories
print_status "Creating required directories..."
mkdir -p logs data nginx/ssl cloudflare/credentials
chmod 755 logs data
print_success "Directories created and configured"

# Step 4: Check Required Files
print_status "Checking required files..."
required_files=("docker-compose.yml" "backend/app.py" "frontend/index.html")

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file missing: $file"
        exit 1
    fi
done

print_success "All required files are present"

# Step 5: Stop Existing Services (if any)
print_status "Stopping any existing services..."
docker compose down --volumes 2>/dev/null || true
print_success "Cleaned up existing services"

# Step 6: Remove Old Images (optional cleanup)
print_status "Cleaning up old Docker images..."
docker system prune -f
print_success "Docker cleanup completed"

# Step 7: Build and Start Services
print_status "Building and starting services..."
print_warning "This may take several minutes on first run..."

if docker compose up -d --build; then
    print_success "Services started successfully"
else
    print_error "Failed to start services"
    print_status "Checking service logs..."
    docker compose logs
    exit 1
fi

# Step 8: Wait for Services to Initialize
print_status "Waiting for services to initialize..."
sleep 30

# Step 9: Health Checks
print_status "Performing health checks..."

# Check PostgreSQL
print_status "Checking PostgreSQL..."
for i in {1..12}; do
    if docker compose exec -T postgres pg_isready -U hsearch_user -d hsearch_db; then
        print_success "PostgreSQL is ready"
        break
    else
        if [ $i -eq 12 ]; then
            print_error "PostgreSQL failed to start"
            docker compose logs postgres
            exit 1
        fi
        print_status "Waiting for PostgreSQL... ($i/12)"
        sleep 10
    fi
done

# Check Redis
print_status "Checking Redis..."
if docker compose exec -T redis redis-cli ping | grep -q PONG; then
    print_success "Redis is ready"
else
    print_error "Redis is not responding"
    docker compose logs redis
    exit 1
fi

# Check Backend API
print_status "Checking Backend API..."
for i in {1..12}; do
    if curl -s http://localhost:5000/api/health > /dev/null; then
        print_success "Backend API is ready"
        break
    else
        if [ $i -eq 12 ]; then
            print_error "Backend API failed to start"
            docker compose logs backend
            exit 1
        fi
        print_status "Waiting for Backend API... ($i/12)"
        sleep 10
    fi
done

# Check Nginx
print_status "Checking Nginx..."
if curl -s http://localhost > /dev/null; then
    print_success "Nginx is ready"
else
    print_error "Nginx is not responding"
    docker compose logs nginx
    exit 1
fi

# Step 10: Database Table Check
print_status "Checking database tables..."
if docker compose exec -T postgres psql -U hsearch_user -d hsearch_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'hs_codes';" | grep -q 1; then
    print_success "Database tables exist"
    
    # Check if data exists
    record_count=$(docker compose exec -T postgres psql -U hsearch_user -d hsearch_db -t -c "SELECT COUNT(*) FROM hs_codes;" 2>/dev/null | tr -d ' \n' || echo "0")
    if [ "$record_count" -gt 0 ]; then
        print_success "Database contains $record_count records"
    else
        print_warning "Database tables exist but no data found"
        print_status "Run ./import-data.sh to import HS codes data"
    fi
else
    print_warning "HS codes table not found"
    print_status "Run ./import-data.sh to create tables and import data"
fi

# Step 11: Display Service Status
print_status "Getting service status..."
docker compose ps

# Step 12: Display Access Information
echo ""
echo "🎉 HSSearch Application Deployment Complete!"
echo "==========================================="
echo ""
print_success "Services Status:"
docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"

echo ""
print_success "Access Information:"
echo "  • Local Access: http://localhost"
echo "  • API Endpoint: http://localhost/api/"
echo "  • Health Check: http://localhost/api/health"

# Get local IP for network access
LOCAL_IP=$(hostname -I | awk '{print $1}')
if [ ! -z "$LOCAL_IP" ]; then
    echo "  • Network Access: http://$LOCAL_IP"
fi

echo ""
print_success "🌐 External Access (Optional):"
echo "  • Setup Cloudflare Tunnel: ./setup-cloudflare.sh"
echo "  • Start with tunnel: ./start-cloudflare.sh"
echo "  • Documentation: CLOUDFLARE_SETUP.md"

echo ""
print_success "📊 Data Management:"
echo "  • Import data: ./import-data.sh"
echo "  • Check data status: ./import-data.sh --status"

echo ""
print_success "Useful Commands:"
echo "  • View logs: docker compose logs -f"
echo "  • Restart services: docker compose restart"
echo "  • Stop services: docker compose down"
echo "  • Update app: ./deploy-app.sh"
echo "  • Import data: ./import-data.sh"

# Check if we need to remind about data import
if [ "$record_count" -eq 0 ]; then
    echo ""
    print_warning "⚠️  NEXT STEP REQUIRED:"
    print_warning "No data found in database. Run the following command to import HS codes:"
    echo ""
    echo "    ./import-data.sh"
    echo ""
fi

print_success "HSSearch application stack is now running!"