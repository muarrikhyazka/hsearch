#!/bin/bash

# Manual Cloudflare Tunnel Starter
# Use this when the tunnel service is not in docker-compose.yml

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

echo "🌐 Starting Cloudflare Tunnel Manually"
echo "====================================="

# Check if required files exist
print_status "Checking Cloudflare configuration..."

if [ ! -f "cloudflare/config.yml" ]; then
    print_error "Cloudflare config.yml not found!"
    print_status "Please run ./setup-cloudflare.sh first"
    exit 1
fi

if [ ! -f "cloudflare/credentials/credentials.json" ]; then
    print_error "Cloudflare credentials not found at cloudflare/credentials/credentials.json"
    
    # Check if credentials exist in other locations
    if [ -f "cloudflare/credentials.json" ]; then
        print_warning "Found credentials at cloudflare/credentials.json"
        print_status "Creating credentials directory and copying file..."
        mkdir -p cloudflare/credentials
        cp cloudflare/credentials.json cloudflare/credentials/credentials.json
        chmod 600 cloudflare/credentials/credentials.json
        print_success "Credentials copied to expected location"
    else
        print_error "No credentials found. Please run ./setup-cloudflare.sh first"
        exit 1
    fi
fi

# Check if main application is running
print_status "Checking if HSearch application is running..."
if ! docker compose ps | grep -q "hs_nginx.*Up"; then
    print_error "HSearch application is not running!"
    print_status "Please start the application first:"
    echo "  ./deploy.sh"
    echo "  or"
    echo "  docker compose up -d"
    exit 1
fi

print_success "HSearch application is running"

# Stop existing cloudflare container if it exists
print_status "Stopping any existing Cloudflare tunnel..."
docker stop hs_cloudflared 2>/dev/null || true
docker rm hs_cloudflared 2>/dev/null || true

# Get network name
NETWORK_NAME=$(docker network ls --format "table {{.Name}}" | grep hsearch | head -1)
if [ -z "$NETWORK_NAME" ]; then
    NETWORK_NAME="hsearch_default"
    print_warning "Using default network name: $NETWORK_NAME"
else
    print_status "Using network: $NETWORK_NAME"
fi

# Start Cloudflare tunnel
print_status "Starting Cloudflare tunnel container..."
docker run -d \
  --name hs_cloudflared \
  --restart unless-stopped \
  --network "$NETWORK_NAME" \
  -v "$(pwd)/cloudflare/config.yml:/etc/cloudflared/config.yml:ro" \
  -v "$(pwd)/cloudflare/credentials/credentials.json:/etc/cloudflared/credentials.json:ro" \
  cloudflare/cloudflared:latest tunnel run

# Wait for container to start
print_status "Waiting for tunnel to initialize..."
sleep 10

# Check if container is running
if docker ps | grep -q "hs_cloudflared"; then
    print_success "✅ Cloudflare tunnel started successfully!"
    
    # Get domain from config
    DOMAIN=$(grep "hostname:" cloudflare/config.yml | head -1 | awk '{print $3}' | tr -d '"')
    
    if [ -n "$DOMAIN" ]; then
        echo ""
        print_success "🎉 HSearch is now accessible via Cloudflare Tunnel!"
        echo "  🌐 External URL: https://$DOMAIN"
        echo "  🏠 Local URL: http://localhost"
        echo ""
        print_status "Services Status:"
        docker compose ps
        echo ""
        print_status "Cloudflare Tunnel Status:"
        docker ps --filter "name=hs_cloudflared" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        print_warning "Could not determine domain from config"
    fi
    
    echo ""
    print_status "Useful Commands:"
    echo "  • View tunnel logs: docker logs -f hs_cloudflared"
    echo "  • Stop tunnel: docker stop hs_cloudflared"
    echo "  • Restart tunnel: docker restart hs_cloudflared"
    echo "  • Check tunnel status: docker ps | grep cloudflared"
    
else
    print_error "❌ Failed to start Cloudflare tunnel!"
    print_status "Checking container logs..."
    docker logs hs_cloudflared 2>/dev/null || echo "No logs available"
    exit 1
fi

print_success "Cloudflare tunnel setup complete!"