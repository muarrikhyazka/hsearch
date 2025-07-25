#!/bin/bash

# HSSearch Database Backup Script
# Usage: ./scripts/backup.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory
BACKUP_DIR="backups"
mkdir -p $BACKUP_DIR

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/hsearch_backup_$TIMESTAMP.sql"

print_status "Creating database backup..."

# Check if postgres container is running
if ! docker compose ps | grep -q "hs_postgres.*Up"; then
    print_error "PostgreSQL container is not running"
    exit 1
fi

# Create database backup
if docker compose exec -T postgres pg_dump -U hsearch_user hsearch_db > $BACKUP_FILE; then
    print_success "Backup created: $BACKUP_FILE"
    
    # Get file size
    SIZE=$(du -h $BACKUP_FILE | cut -f1)
    print_status "Backup size: $SIZE"
    
    # Keep only last 7 backups
    print_status "Cleaning old backups (keeping last 7)..."
    cd $BACKUP_DIR
    ls -t hsearch_backup_*.sql | tail -n +8 | xargs -r rm
    cd ..
    
    REMAINING=$(ls -1 $BACKUP_DIR/hsearch_backup_*.sql | wc -l)
    print_success "Backup cleanup complete. $REMAINING backup(s) remaining."
    
else
    print_error "Failed to create backup"
    exit 1
fi