#!/bin/bash

# HSSearch Update Script
# Usage: ./scripts/update.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

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

echo "🔄 HSSearch Update Process"
echo "=========================="

# Step 1: Create backup first
print_status "Creating backup before update..."
if [ -f "scripts/backup.sh" ]; then
    chmod +x scripts/backup.sh
    ./scripts/backup.sh
else
    print_warning "Backup script not found, skipping backup"
fi

# Step 2: Pull latest changes
print_status "Pulling latest changes from repository..."
git stash 2>/dev/null || true  # Stash any local changes
if git pull origin main; then
    print_success "Repository updated successfully"
else
    print_error "Failed to pull latest changes"
    exit 1
fi

# Step 3: Stop services
print_status "Stopping services..."
docker compose down

# Step 4: Rebuild images
print_status "Rebuilding images with latest changes..."
if docker compose build --no-cache; then
    print_success "Images rebuilt successfully"
else
    print_error "Failed to rebuild images"
    exit 1
fi

# Step 5: Start services
print_status "Starting updated services..."
if docker compose up -d; then
    print_success "Services started successfully"
else
    print_error "Failed to start services"
    exit 1
fi

# Step 6: Wait for services
print_status "Waiting for services to be ready..."
sleep 30

# Step 7: Health check
print_status "Performing health check..."
if curl -f -s http://localhost/api/health > /dev/null; then
    print_success "Health check passed - Update completed successfully!"
else
    print_error "Health check failed - Services may not be ready yet"
    print_status "Check logs with: docker compose logs -f"
fi

# Step 8: Display status
print_status "Current service status:"
docker compose ps

print_success "Update completed at $(date)"