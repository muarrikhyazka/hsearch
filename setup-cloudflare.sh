#!/bin/bash

# Cloudflare Tunnel Setup Script for HSearch
# This script helps you set up Cloudflare Tunnel for external access

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "🌐 HSearch Cloudflare Tunnel Setup"
echo "=================================="

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    print_error "cloudflared is not installed"
    print_status "Installing cloudflared..."
    
    # Install cloudflared based on OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux installation
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
        sudo dpkg -i cloudflared-linux-amd64.deb
        rm cloudflared-linux-amd64.deb
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS installation
        brew install cloudflared
    else
        print_error "Unsupported OS. Please install cloudflared manually from:"
        print_error "https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
        exit 1
    fi
fi

print_success "cloudflared is available"

# Check if user is logged in to Cloudflare
print_status "Checking Cloudflare authentication..."
if ! cloudflared tunnel list &> /dev/null; then
    print_warning "Not authenticated with Cloudflare"
    print_status "Please log in to Cloudflare:"
    cloudflared tunnel login
fi

# Create tunnel
print_status "Creating Cloudflare tunnel..."
TUNNEL_NAME="hsearch-$(date +%s)"

if cloudflared tunnel create $TUNNEL_NAME; then
    print_success "Tunnel '$TUNNEL_NAME' created successfully"
else
    print_error "Failed to create tunnel"
    exit 1
fi

# Get tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep $TUNNEL_NAME | awk '{print $1}')
print_status "Tunnel ID: $TUNNEL_ID"

# Create credentials directory
mkdir -p cloudflare/credentials

# Copy credentials file
CREDENTIALS_FILE="$HOME/.cloudflared/$TUNNEL_ID.json"
if [ -f "$CREDENTIALS_FILE" ]; then
    cp "$CREDENTIALS_FILE" cloudflare/credentials/credentials.json
    print_success "Credentials copied to cloudflare/credentials/"
else
    print_error "Credentials file not found at $CREDENTIALS_FILE"
    exit 1
fi

# Update config.yml with tunnel ID
sed -i.bak "s/YOUR_TUNNEL_ID/$TUNNEL_ID/g" cloudflare/config.yml
print_success "Updated config.yml with tunnel ID"

# Prompt for domain configuration
echo ""
print_warning "IMPORTANT: Domain Configuration Required"
echo "========================================="
echo "1. Go to your Cloudflare dashboard"
echo "2. Select your domain"
echo "3. Go to DNS settings"
echo "4. Add CNAME records for your tunnel:"
echo ""
echo "   Type: CNAME"
echo "   Name: hsearch"
echo "   Target: $TUNNEL_ID.cfargotunnel.com"
echo ""
echo "   Optional API subdomain:"
echo "   Name: api-hsearch"
echo "   Target: $TUNNEL_ID.cfargotunnel.com"
echo ""

read -p "Enter your domain (e.g., example.com): " DOMAIN

if [ -n "$DOMAIN" ]; then
    # Update config.yml with domain
    sed -i.bak "s/yourdomain.com/$DOMAIN/g" cloudflare/config.yml
    print_success "Updated config.yml with domain: $DOMAIN"
    
    echo ""
    print_success "Setup completed! Your HSearch will be available at:"
    echo "  🌐 Main site: https://hsearch.$DOMAIN"
    echo "  🔧 API: https://api-hsearch.$DOMAIN (optional)"
    echo ""
    print_status "Next steps:"
    echo "1. Add the DNS records in Cloudflare dashboard as shown above"
    echo "2. Run: docker compose up -d"
    echo "3. Your HSearch will be accessible externally!"
else
    print_warning "Domain not provided. Please manually update cloudflare/config.yml"
fi

# Create a route for the tunnel
print_status "Creating DNS route..."
if cloudflared tunnel route dns $TUNNEL_ID hsearch.$DOMAIN; then
    print_success "DNS route created for hsearch.$DOMAIN"
else
    print_warning "Failed to create DNS route automatically. Please add DNS record manually."
fi

print_success "Cloudflare Tunnel setup completed!"
print_status "Tunnel name: $TUNNEL_NAME"
print_status "Tunnel ID: $TUNNEL_ID"
print_status "Config file: cloudflare/config.yml"
print_status "Credentials: cloudflare/credentials/credentials.json"