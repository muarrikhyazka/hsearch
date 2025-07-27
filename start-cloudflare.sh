#!/bin/bash

# Quick start script for Cloudflare Tunnel
# Use this after running setup-cloudflare.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "🌐 Starting HSearch with Cloudflare Tunnel"
echo "========================================="

# Check if Cloudflare config exists
if [ ! -f "cloudflare/config.yml" ]; then
    print_error "Cloudflare configuration not found!"
    print_status "Please run ./setup-cloudflare.sh first"
    exit 1
fi

if [ ! -f "cloudflare/credentials/credentials.json" ]; then
    print_error "Cloudflare credentials not found!"
    print_status "Please run ./setup-cloudflare.sh first"
    exit 1
fi

# Start all services including Cloudflare tunnel
print_status "Starting HSearch with Cloudflare Tunnel..."
docker compose --profile cloudflare up -d

print_status "Waiting for services to be ready..."
sleep 15

# Check service status
print_status "Checking service status..."
docker compose ps

# Get domain from config
DOMAIN=$(grep "hostname:" cloudflare/config.yml | head -1 | awk '{print $3}')

if [ -n "$DOMAIN" ]; then
    echo ""
    print_success "🎉 HSearch is now running with Cloudflare Tunnel!"
    echo "  🌐 External URL: https://$DOMAIN"
    echo "  🏠 Local URL: http://localhost"
    echo ""
    print_status "Services:"
    echo "  ✅ PostgreSQL Database"
    echo "  ✅ Redis Cache"
    echo "  ✅ Python Backend API"
    echo "  ✅ Nginx Web Server"
    echo "  ✅ Cloudflare Tunnel"
    echo ""
    print_status "Your HSearch is now accessible from anywhere!"
else
    print_error "Could not determine domain from config"
fi