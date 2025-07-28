#!/bin/bash

# Stop Cloudflare Tunnel Script

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "🛑 Stopping Cloudflare Tunnel"
echo "============================="

# Check if container exists
if docker ps -a --format "{{.Names}}" | grep -q "hs_cloudflared"; then
    print_status "Stopping Cloudflare tunnel container..."
    docker stop hs_cloudflared 2>/dev/null || true
    docker rm hs_cloudflared 2>/dev/null || true
    print_success "✅ Cloudflare tunnel stopped and removed"
else
    print_status "No Cloudflare tunnel container found"
fi

# Show remaining services
print_status "Remaining services:"
docker compose ps

print_success "Cloudflare tunnel shutdown complete!"