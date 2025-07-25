#!/bin/bash

# HSSearch Auto Deployment Script for Mini PC Home Server
# Usage: ./deploy.sh

set -e  # Exit on any error

echo "🚀 Starting HSSearch Deployment..."
echo "=================================="

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
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_success "Docker and Docker Compose are installed"

# Step 3: Create Required Directories
print_status "Creating required directories..."

# Create directories with proper error handling
if ! mkdir -p logs 2>/dev/null; then
    print_warning "Could not create logs directory, trying with sudo..."
    sudo mkdir -p logs || print_error "Failed to create logs directory"
fi

if ! mkdir -p nginx/ssl 2>/dev/null; then
    print_warning "Could not create nginx/ssl directory, trying with sudo..."
    sudo mkdir -p nginx/ssl || print_error "Failed to create nginx/ssl directory"
fi

# Set permissions with error handling
if ! chmod 755 logs 2>/dev/null; then
    print_warning "Could not set logs permissions, trying with sudo..."
    sudo chmod 755 logs 2>/dev/null || print_warning "Could not set logs permissions"
fi

if ! chmod 755 nginx/ssl 2>/dev/null; then
    print_warning "Could not set nginx/ssl permissions, trying with sudo..."
    sudo chmod 755 nginx/ssl 2>/dev/null || print_warning "Could not set nginx/ssl permissions"
fi

# Ensure current user owns the directories
if command -v chown &> /dev/null; then
    sudo chown -R $USER:$USER logs nginx 2>/dev/null || print_warning "Could not set directory ownership"
fi

print_success "Directories created and configured"

# Step 4: Check Required Files
print_status "Checking required files..."
required_files=("docker-compose.yml" "data/final-dataset.csv" "backend/app.py" "frontend/index.html")

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file missing: $file"
        exit 1
    fi
done

print_success "All required files present"

# Step 5: Clean Up Existing Deployment
print_status "Cleaning up existing deployment..."

# Stop and remove all containers, networks, and volumes
print_status "Stopping existing services..."
docker compose down --remove-orphans 2>/dev/null || true

# Remove existing volumes to ensure fresh data
print_status "Removing existing volumes (including database data)..."
docker compose down -v 2>/dev/null || true

# Clean up any existing containers with same names
print_status "Removing existing containers..."
containers=("hs_postgres" "hs_redis" "hs_backend" "hs_nginx")
for container in "${containers[@]}"; do
    if docker ps -a --format "table {{.Names}}" | grep -q "^$container$"; then
        print_status "Removing existing container: $container"
        docker rm -f $container 2>/dev/null || true
    fi
done

# Clean up existing images to force rebuild
print_status "Cleaning up existing images..."
docker image prune -f 2>/dev/null || true

# Remove project-specific volumes if they exist
volumes=("hsearch_postgres_data" "hsearch_redis_data")
for volume in "${volumes[@]}"; do
    if docker volume ls --format "table {{.Name}}" | grep -q "^$volume$"; then
        print_status "Removing existing volume: $volume"
        docker volume rm $volume 2>/dev/null || true
    fi
done

print_success "Existing deployment cleaned up"

# Step 6: Build and Start Services
print_status "Building and starting services..."
print_status "This may take a few minutes on first run..."

if docker compose build --no-cache; then
    print_success "Services built successfully"
else
    print_error "Failed to build services"
    exit 1
fi

if docker compose up -d; then
    print_success "Services started successfully"
else
    print_error "Failed to start services"
    exit 1
fi

# Step 7: Wait for Services to be Ready
print_status "Waiting for services to be ready..."
sleep 30

# Check if containers are running
containers=("hs_postgres" "hs_redis" "hs_backend" "hs_nginx")
for container in "${containers[@]}"; do
    if docker compose ps | grep -q "$container.*Up"; then
        print_success "$container is running"
    else
        print_error "$container is not running"
        print_status "Container logs:"
        docker compose logs "$container" | tail -10
        exit 1
    fi
done

# Step 8: Import Fresh Data to Database
print_status "Importing fresh HS Code data to database..."
print_status "This will replace any existing data with the latest dataset..."

# Wait a bit more for database to be fully ready
sleep 10

# Try data import with retry mechanism
max_retries=3
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if docker compose exec -T backend python import_data.py; then
        print_success "Fresh data imported successfully"
        break
    else
        retry_count=$((retry_count + 1))
        if [ $retry_count -lt $max_retries ]; then
            print_warning "Data import attempt $retry_count failed, retrying in 10 seconds..."
            sleep 10
        else
            print_error "Data import failed after $max_retries attempts"
            print_status "Check backend logs: docker compose logs backend"
            exit 1
        fi
    fi
done

# Step 9: Health Checks
print_status "Performing health checks..."

# Check API health
if curl -f -s http://localhost/api/health > /dev/null; then
    print_success "API health check passed"
else
    print_warning "API health check failed, but service may still be starting"
fi

# Check web interface
if curl -f -s http://localhost > /dev/null; then
    print_success "Web interface is accessible"
else
    print_warning "Web interface check failed"
fi

# Step 10: Display Status
print_status "Getting service status..."
docker compose ps

# Step 11: Display Access Information
echo ""
echo "🎉 HSSearch Deployment Complete!"
echo "================================"
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
print_success "Useful Commands:"
echo "  • View logs: docker compose logs -f"
echo "  • Restart services: docker compose restart"
echo "  • Stop services: docker compose down"
echo "  • Update deployment: ./deploy.sh"

echo ""
print_status "Deployment completed at $(date)"

# Optional: Test search functionality
echo ""
read -p "Would you like to test search functionality? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Testing search functionality..."
    
    # Test search
    if curl -s -X POST http://localhost/api/search \
        -H "Content-Type: application/json" \
        -d '{"query": "computer", "ai_enabled": true}' | grep -q "results"; then
        print_success "Search functionality test passed"
    else
        print_warning "Search functionality test failed"
    fi
fi

print_success "All done! HSSearch is ready to use."