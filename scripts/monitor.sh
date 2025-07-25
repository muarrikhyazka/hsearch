#!/bin/bash

# HSSearch Monitoring Script
# Usage: ./scripts/monitor.sh

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}$1${NC}"
    echo "$(printf '=%.0s' {1..50})"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

clear
echo "📊 HSSearch System Monitor"
echo "=========================="
echo "Last updated: $(date)"
echo ""

# Service Status
print_header "SERVICE STATUS"
docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"
echo ""

# Container Resource Usage
print_header "RESOURCE USAGE"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
echo ""

# Health Checks
print_header "HEALTH CHECKS"

# API Health
if curl -f -s http://localhost/api/health > /dev/null; then
    print_success "API Health Check"
else
    print_error "API Health Check"
fi

# Database Connection
if curl -f -s http://localhost/api/status > /dev/null; then
    print_success "Database Connection"
else
    print_error "Database Connection"
fi

# Web Interface
if curl -f -s http://localhost > /dev/null; then
    print_success "Web Interface"
else
    print_error "Web Interface"
fi

echo ""

# Database Status
print_header "DATABASE STATUS"
if docker compose exec -T postgres psql -U hsearch_user -d hsearch_db -c "SELECT COUNT(*) as total_records FROM hs_codes;" 2>/dev/null; then
    echo ""
else
    print_error "Could not connect to database"
fi

# Disk Usage
print_header "DISK USAGE"
echo "Project Directory:"
du -sh . 2>/dev/null || echo "Unable to calculate"
echo ""
echo "Docker System:"
docker system df
echo ""

# System Resources
print_header "SYSTEM RESOURCES"
echo "Memory Usage:"
free -h
echo ""
echo "Disk Space:"
df -h / | tail -1
echo ""

# Recent Logs (Last 10 lines from each service)
print_header "RECENT LOGS"
services=("backend" "nginx" "postgres" "redis")

for service in "${services[@]}"; do
    echo -e "${BLUE}--- $service ---${NC}"
    docker compose logs --tail=3 $service 2>/dev/null || echo "No logs available"
    echo ""
done

# Network Information
print_header "NETWORK ACCESS"
LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "Unable to detect")
echo "Local Access: http://localhost"
echo "Network Access: http://$LOCAL_IP"
echo ""

# Quick Actions Menu
print_header "QUICK ACTIONS"
echo "1. View live logs: docker compose logs -f"
echo "2. Restart services: docker compose restart"
echo "3. Update application: ./scripts/update.sh"
echo "4. Create backup: ./scripts/backup.sh"
echo "5. Stop services: docker compose down"
echo ""

# Auto-refresh option
read -t 5 -p "Press Enter to refresh monitor (auto-refresh in 5s) or Ctrl+C to exit: "
if [ $? -eq 0 ]; then
    exec $0  # Restart script
else
    exec $0  # Auto-refresh
fi