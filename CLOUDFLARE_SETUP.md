# 🌐 Cloudflare Tunnel Setup for HSearch

This guide helps you set up Cloudflare Tunnel to make your HSearch system accessible from anywhere on the internet.

## Prerequisites

1. **Cloudflare Account** - Free account at [cloudflare.com](https://cloudflare.com)
2. **Domain** - A domain added to your Cloudflare account
3. **HSearch Deployed** - Your HSearch system should be running locally first

## Quick Setup

### Step 1: Run Setup Script
```bash
./setup-cloudflare.sh
```

This script will:
- Install `cloudflared` if needed
- Authenticate with Cloudflare
- Create a new tunnel
- Generate configuration files
- Guide you through DNS setup

### Step 2: Configure DNS (Manual)
After running the setup script, go to your Cloudflare dashboard:

1. Select your domain
2. Go to **DNS** > **Records**
3. Add a CNAME record:
   - **Type**: CNAME
   - **Name**: hsearch
   - **Target**: `[tunnel-id].cfargotunnel.com`
   - **Proxy status**: Proxied (orange cloud)

### Step 3: Start with Tunnel
```bash
./start-cloudflare.sh
```

Or manually:
```bash
docker compose --profile cloudflare up -d
```

## Configuration Files

### `cloudflare/config.yml`
Main tunnel configuration with ingress rules:
```yaml
tunnel: your-tunnel-id
credentials-file: /etc/cloudflared/credentials.json

ingress:
  - hostname: hsearch.yourdomain.com
    service: http://nginx:80
  - service: http_status:404
```

### `cloudflare/credentials/credentials.json`
Tunnel authentication credentials (auto-generated, keep secure)

## Manual Setup (Alternative)

If you prefer manual setup:

### 1. Install cloudflared
```bash
# Linux
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# macOS
brew install cloudflared
```

### 2. Login to Cloudflare
```bash
cloudflared tunnel login
```

### 3. Create Tunnel
```bash
cloudflared tunnel create hsearch
```

### 4. Configure DNS
Add CNAME record in Cloudflare dashboard pointing to your tunnel.

### 5. Start Tunnel
```bash
docker compose --profile cloudflare up -d
```

## Accessing Your HSearch

Once setup is complete, your HSearch will be available at:
- **External**: `https://hsearch.yourdomain.com`
- **Local**: `http://localhost` (still works)

## Features with Cloudflare

### Security
- **DDoS Protection** - Automatic protection against attacks
- **SSL/TLS** - Automatic HTTPS encryption
- **Access Control** - Optional IP whitelisting and authentication
- **Rate Limiting** - Protect against abuse

### Performance
- **Global CDN** - Fast access from anywhere
- **Caching** - Static assets cached globally
- **Compression** - Automatic content compression
- **HTTP/2** - Modern protocol support

### Reliability
- **Uptime Monitoring** - Health checks and alerts
- **Load Balancing** - Multiple origin support
- **Failover** - Automatic failover capabilities

## Troubleshooting

### Tunnel Not Connecting
```bash
# Check tunnel status
docker logs hs_cloudflared

# Restart tunnel
docker compose restart cloudflared
```

### DNS Not Resolving
1. Verify CNAME record in Cloudflare dashboard
2. Wait for DNS propagation (up to 24 hours)
3. Check with: `nslookup hsearch.yourdomain.com`

### Authentication Issues
```bash
# Re-authenticate
cloudflared tunnel login

# Recreate credentials
./setup-cloudflare.sh
```

### Service Not Accessible
1. Check local services are running: `docker compose ps`
2. Verify nginx is accessible locally: `curl http://localhost`
3. Check Cloudflare tunnel logs: `docker logs hs_cloudflared`

## Security Best Practices

1. **Keep Credentials Secure**
   - Don't commit `credentials.json` to git
   - Restrict file permissions: `chmod 600 cloudflare/credentials/credentials.json`

2. **Use Cloudflare Access** (Optional)
   - Add authentication layer
   - Restrict access by email/domain
   - Enable audit logging

3. **Monitor Access**
   - Enable Cloudflare Analytics
   - Set up security alerts
   - Review access logs regularly

## Commands Reference

```bash
# Setup (one-time)
./setup-cloudflare.sh

# Start with tunnel
./start-cloudflare.sh

# Start without tunnel
docker compose up -d

# Stop all services
docker compose down

# View tunnel logs
docker logs hs_cloudflared

# Check tunnel status
cloudflared tunnel list

# Update tunnel config
docker compose restart cloudflared
```

## Support

For issues with:
- **HSearch**: Check main README.md
- **Cloudflare Tunnel**: [Cloudflare Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- **Docker**: [Docker Documentation](https://docs.docker.com/)

Your HSearch is now accessible globally while running securely from your mini PC! 🚀