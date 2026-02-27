#!/bin/bash

# Asmblr Rollback Script
# Automated rollback to previous deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR=${1:-""}
HEALTH_CHECK_URL="http://localhost:8000/health"

echo -e "${BLUE}🔄 Asmblr Rollback Script${NC}"
echo -e "${BLUE}========================${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if backup directory is provided
if [ -z "$BACKUP_DIR" ]; then
    print_error "Backup directory not provided"
    echo "Usage: $0 <backup_directory>"
    echo ""
    echo "Available backups:"
    ls -la ./backups/ 2>/dev/null | tail -5 || echo "No backups found"
    exit 1
fi

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    print_error "Backup directory not found: $BACKUP_DIR"
    exit 1
fi

print_info "Rolling back to backup: $BACKUP_DIR"

# Stop current services
print_info "Stopping current services..."
docker-compose -f docker-compose.production.yml down

# Restore database
if [ -f "$BACKUP_DIR/database.sql" ]; then
    print_info "Restoring database..."
    
    # Start database only
    docker-compose -f docker-compose.production.yml up -d postgres
    
    # Wait for database to be ready
    sleep 10
    
    # Drop and recreate database
    docker-compose -f docker-compose.production.yml exec -T postgres psql -U asmblr -c "DROP DATABASE IF EXISTS asmblr;" || true
    docker-compose -f docker-compose.production.yml exec -T postgres psql -U asmblr -c "CREATE DATABASE asmblr;" || true
    
    # Restore data
    docker-compose -f docker-compose.production.yml exec -T postgres psql -U asmblr asmblr < "$BACKUP_DIR/database.sql"
    
    print_status "Database restored"
else
    print_warning "No database backup found"
fi

# Restore configuration
if [ -f "$BACKUP_DIR/.env.production" ]; then
    print_info "Restoring configuration..."
    cp "$BACKUP_DIR/.env.production" .env.production
    print_status "Configuration restored"
else
    print_warning "No configuration backup found"
fi

# Restore runs directory
if [ -d "$BACKUP_DIR/runs" ]; then
    print_info "Restoring runs directory..."
    rm -rf runs
    cp -r "$BACKUP_DIR/runs" .
    print_status "Runs directory restored"
else
    print_warning "No runs directory backup found"
fi

# Start all services
print_info "Starting services..."
docker-compose -f docker-compose.production.yml up -d

# Health check
print_info "Performing health check..."
sleep 20

if curl -f -s "$HEALTH_CHECK_URL" >/dev/null 2>&1; then
    print_status "Rollback completed successfully"
    echo ""
    echo -e "${GREEN}🎉 Application is running at: http://localhost:8000${NC}"
    echo -e "${GREEN}🌐 UI available at: http://localhost:8501${NC}"
else
    print_error "Health check failed after rollback"
    exit 1
fi

print_info "Rollback to $BACKUP_DIR completed"
