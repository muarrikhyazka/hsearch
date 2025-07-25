# HSSearch Deployment Guide - Mini PC Home Server

Panduan lengkap untuk deploy HSSearch di mini PC home server setelah `git pull`.

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **RAM**: Minimum 4GB (Recommended 8GB+)
- **Storage**: Minimum 20GB free space
- **CPU**: Multi-core processor (2+ cores recommended)

### Software Dependencies
- Docker & Docker Compose
- Git
- Python 3.8+ (optional, untuk maintenance scripts)

## Step 1: Initial Server Setup

### 1.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Install Docker
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

### 1.3 Install Git (if not installed)
```bash
sudo apt install git -y
```

## Step 2: Clone Repository

### 2.1 Clone Project
```bash
cd /home/$USER
git clone https://github.com/muarrikhyazka/hsearch.git
cd hsearch
```

### 2.2 Set Permissions
```bash
chmod +x *.py
sudo chown -R $USER:$USER /home/$USER/hsearch
```

## Step 3: Environment Configuration

### 3.1 Create Required Directories
```bash
# Create log directories
mkdir -p logs
mkdir -p nginx/ssl

# Set permissions
chmod 755 logs
chmod 755 nginx/ssl
```

### 3.2 Check Configuration Files
```bash
# Verify docker-compose.yml exists
ls -la docker-compose.yml

# Verify all required directories
ls -la backend/ frontend/ database/ nginx/
```

## Step 4: Database Setup

### 4.1 Import HS Code Data
```bash
# Make sure data file exists
ls -la data/final-dataset.csv

# Check file size (should be around 3-5MB)
du -h data/final-dataset.csv
```

## Step 5: Deploy Application

### 5.1 Build and Start Services
```bash
# Pull latest images and build
docker compose pull
docker compose build --no-cache

# Start all services
docker compose up -d

# Check service status
docker compose ps
```

### 5.2 Verify Services are Running
```bash
# Check all containers are healthy
docker compose ps

# Expected output should show:
# - hs_postgres (healthy)
# - hs_redis (healthy) 
# - hs_backend (healthy)
# - hs_nginx (running)
```

### 5.3 Import Data to Database
```bash
# Wait for database to be ready (30 seconds)
sleep 30

# Import HS code data
docker compose exec backend python /app/import_data.py

# Expected output: "🎉 Data import completed successfully!"
```

## Step 6: Verification & Testing

### 6.1 Health Checks
```bash
# Check application health
curl http://localhost/api/health
# Expected: {"status": "healthy", ...}

# Check database connection
curl http://localhost/api/status
# Expected: {"database": "connected", ...}
```

### 6.2 Test Search Functionality
```bash
# Test basic search
curl -X POST http://localhost/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "computer", "ai_enabled": true}'

# Should return JSON with search results
```

### 6.3 Access Web Interface
Open browser and go to:
- **Local Access**: `http://localhost`
- **Network Access**: `http://[MINI-PC-IP-ADDRESS]`

To find mini PC IP:
```bash
ip addr show | grep inet
```

## Step 7: Network Configuration (Optional)

### 7.1 Allow External Access
```bash
# Check if firewall is active
sudo ufw status

# If active, allow HTTP traffic
sudo ufw allow 80/tcp
sudo ufw allow 22/tcp  # Keep SSH access

# For router access, configure port forwarding:
# Router Admin Panel → Port Forwarding → 
# External Port: 8080 → Internal IP: [MINI-PC-IP] → Internal Port: 80
```

### 7.2 Set Static IP (Recommended)
```bash
# Edit netplan configuration
sudo nano /etc/netplan/50-cloud-init.yaml

# Add static IP configuration:
# network:
#   version: 2
#   ethernets:
#     eth0:  # or your interface name
#       dhcp4: false
#       addresses: [192.168.1.100/24]  # Your desired static IP
#       gateway4: 192.168.1.1          # Your router IP
#       nameservers:
#         addresses: [8.8.8.8, 8.8.4.4]

# Apply changes
sudo netplan apply
```

## Step 8: Monitoring & Maintenance

### 8.1 View Logs
```bash
# View all service logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f nginx
docker compose logs -f postgres
```

### 8.2 Backup Database
```bash
# Create backup script
cat > backup_db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker compose exec -T postgres pg_dump -U hsearch_user hsearch_db > backup_hsearch_$DATE.sql
echo "Backup created: backup_hsearch_$DATE.sql"
EOF

chmod +x backup_db.sh

# Run backup
./backup_db.sh
```

### 8.3 Update Application
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d

# Verify everything is working
curl http://localhost/api/health
```

## Step 9: Auto-Start on Boot

### 9.1 Create Systemd Service
```bash
# Create service file
sudo tee /etc/systemd/system/hsearch.service > /dev/null << 'EOF'
[Unit]
Description=HSSearch Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/YOUR_USERNAME/hsearch
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0
User=YOUR_USERNAME

[Install]
WantedBy=multi-user.target
EOF

# Replace YOUR_USERNAME with actual username
sudo sed -i "s/YOUR_USERNAME/$USER/g" /etc/systemd/system/hsearch.service

# Enable service
sudo systemctl enable hsearch.service
sudo systemctl start hsearch.service

# Check status
sudo systemctl status hsearch.service
```

## Step 10: Performance Optimization

### 10.1 Docker Resource Limits
```bash
# Edit docker-compose.yml to add resource limits if needed
# Add to each service:
# deploy:
#   resources:
#     limits:
#       memory: 1G
#       cpus: '0.5'
```

### 10.2 Log Rotation
```bash
# Configure Docker log rotation
sudo tee /etc/docker/daemon.json > /dev/null << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "5"
  }
}
EOF

# Restart Docker
sudo systemctl restart docker

# Restart HSSearch
sudo systemctl restart hsearch
```

## Troubleshooting

### Common Issues

1. **Port 80 Already in Use**
   ```bash
   sudo netstat -tulpn | grep :80
   sudo systemctl stop apache2  # if Apache is running
   ```

2. **Database Connection Failed**
   ```bash
   docker compose logs postgres
   docker compose restart postgres
   ```

3. **Out of Memory**
   ```bash
   free -h
   docker system prune -f  # Clean unused containers/images
   ```

4. **Permission Denied**
   ```bash
   sudo chown -R $USER:$USER /home/$USER/hsearch
   chmod +x *.py
   ```

### Useful Commands
```bash
# Restart all services
docker compose restart

# View resource usage
docker stats

# Clean up unused resources
docker system prune -f

# Check disk space
df -h

# Monitor system resources
htop
```

## Success Indicators

✅ **Deployment Successful When:**
- All 4 containers are running (postgres, redis, backend, nginx)
- Health check returns `{"status": "healthy"}`
- Web interface accessible at `http://localhost`
- Search functionality works with Indonesian and English queries
- Database contains 11,554+ HS code records

**Access URLs:**
- **Local**: `http://localhost`
- **Network**: `http://[MINI-PC-IP]`
- **API**: `http://localhost/api/`

**Default Credentials:** None required (public search interface)

---

🎉 **HSSearch is now running on your mini PC home server!**