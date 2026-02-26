#!/bin/bash

# Rollback script for failed deployments
# Automatically rolls back to previous working state

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="/var/backups/asmblr"
ROLLBACK_LOG="/var/log/asmblr-rollback.log"
MAX_ROLLBACKS=5

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$ROLLBACK_LOG"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$ROLLBACK_LOG"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$ROLLBACK_LOG"
}

log_error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$ROLLBACK_LOG"
}

# Create backup directory if it doesn't exist
ensure_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        sudo mkdir -p "$BACKUP_DIR"
        sudo chown $USER:$USER "$BACKUP_DIR"
        log "Created backup directory: $BACKUP_DIR"
    fi
}

# Get current deployment state
get_current_state() {
    log "Capturing current deployment state..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local current_backup="$BACKUP_DIR/current-$timestamp"
    
    mkdir -p "$current_backup"
    
    # Save Docker compose state
    docker-compose -f docker-compose.production.yml ps > "$current_backup/docker-compose-status.txt"
    
    # Save container images
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}" > "$current_backup/images.txt"
    
    # Save configuration
    if [ -f ".env.production" ]; then
        cp .env.production "$current_backup/"
    fi
    
    # Save database schema
    if docker exec postgres-primary pg_dump -U asmblr --schema-only asmblr > "$current_backup/schema.sql" 2>/dev/null; then
        log_success "Database schema backed up"
    else
        log_warning "Could not backup database schema"
    fi
    
    log "Current state saved to: $current_backup"
    echo "$current_backup"
}

# Find latest successful backup
find_latest_backup() {
    local latest_backup=$(ls -1t "$BACKUP_DIR" | grep "^successful-" | head -1)
    if [ -n "$latest_backup" ]; then
        echo "$BACKUP_DIR/$latest_backup"
    else
        echo ""
    fi
}

# Stop current services
stop_services() {
    log "Stopping current services..."
    
    if docker-compose -f docker-compose.production.yml down; then
        log_success "Services stopped successfully"
    else
        log_error "Failed to stop services"
        return 1
    fi
}

# Clean up failed deployment
cleanup_failed_deployment() {
    log "Cleaning up failed deployment..."
    
    # Remove failed containers
    docker-compose -f docker-compose.production.yml rm -f
    
    # Remove dangling images
    docker image prune -f
    
    # Clean up unused volumes (be careful with this)
    docker volume prune -f
    
    log_success "Cleanup completed"
}

# Restore from backup
restore_from_backup() {
    local backup_path="$1"
    
    log "Restoring from backup: $backup_path"
    
    # Restore configuration
    if [ -f "$backup_path/.env.production" ]; then
        cp "$backup_path/.env.production" .env.production
        log_success "Configuration restored"
    fi
    
    # Start services with backup configuration
    if docker-compose -f docker-compose.production.yml --env-file .env.production up -d; then
        log_success "Services started with backup configuration"
    else
        log_error "Failed to start services from backup"
        return 1
    fi
}

# Verify rollback success
verify_rollback() {
    log "Verifying rollback success..."
    
    local retry_count=0
    local max_retries=30
    local retry_delay=10
    
    while [ $retry_count -lt $max_retries ]; do
        log "Health check attempt $((retry_count + 1))/$max_retries..."
        
        if ./scripts/health-check.sh > /dev/null 2>&1; then
            log_success "Rollback verification successful"
            return 0
        else
            log_warning "Health check failed, retrying in ${retry_delay}s..."
            sleep $retry_delay
            ((retry_count++))
        fi
    done
    
    log_error "Rollback verification failed after $max_retries attempts"
    return 1
}

# Create rollback notification
send_notification() {
    local status="$1"
    local message="$2"
    
    log "Sending rollback notification: $status"
    
    # Log to system
    logger -t asmblr-rollback "Rollback $status: $message"
    
    # Send to monitoring system if available
    if command -v curl > /dev/null; then
        curl -X POST "http://localhost:9090/api/v1/alerts" \
            -H "Content-Type: application/json" \
            -d "[{
                \"labels\": {
                    \"alertname\": \"AsmblrRollback\",
                    \"severity\": \"$status\",
                    \"instance\": \"$(hostname)\"
                },
                \"annotations\": {
                    \"description\": \"$message\"
                }
            }]" > /dev/null 2>&1 || true
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups (keeping last $MAX_ROLLBACKS)..."
    
    # Remove old current backups
    ls -1t "$BACKUP_DIR" | grep "^current-" | tail -n +$((MAX_ROLLBACKS + 1)) | while read backup; do
        rm -rf "$BACKUP_DIR/$backup"
        log "Removed old backup: $backup"
    done
    
    # Remove old successful backups
    ls -1t "$BACKUP_DIR" | grep "^successful-" | tail -n +$((MAX_ROLLBACKS + 1)) | while read backup; do
        rm -rf "$BACKUP_DIR/$backup"
        log "Removed old backup: $backup"
    done
}

# Save successful state
save_successful_state() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local successful_backup="$BACKUP_DIR/successful-$timestamp"
    
    mkdir -p "$successful_backup"
    
    # Save current successful state
    docker-compose -f docker-compose.production.yml ps > "$successful_backup/docker-compose-status.txt"
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}" > "$successful_backup/images.txt"
    
    if [ -f ".env.production" ]; then
        cp .env.production "$successful_backup/"
    fi
    
    # Save database
    if docker exec postgres-primary pg_dump -U asmblr asmblr > "$successful_backup/database.sql" 2>/dev/null; then
        log_success "Database backed up successfully"
    fi
    
    log "Successful state saved to: $successful_backup"
}

# Main rollback function
perform_rollback() {
    log "🔄 Starting rollback procedure..."
    
    # Ensure backup directory exists
    ensure_backup_dir
    
    # Save current state (for debugging)
    local current_backup=$(get_current_state)
    
    # Find latest successful backup
    local latest_backup=$(find_latest_backup)
    
    if [ -z "$latest_backup" ]; then
        log_error "No successful backup found for rollback"
        log_warning "Attempting to stop services only..."
        stop_services
        cleanup_failed_deployment
        send_notification "critical" "Rollback failed - no backup available"
        return 1
    fi
    
    log "Found latest backup: $latest_backup"
    
    # Stop current services
    if ! stop_services; then
        log_error "Failed to stop current services"
        send_notification "critical" "Rollback failed - could not stop services"
        return 1
    fi
    
    # Clean up failed deployment
    cleanup_failed_deployment
    
    # Restore from backup
    if ! restore_from_backup "$latest_backup"; then
        log_error "Failed to restore from backup"
        send_notification "critical" "Rollback failed - restore error"
        return 1
    fi
    
    # Verify rollback success
    if verify_rollback; then
        log_success "🎉 Rollback completed successfully!"
        send_notification "info" "Rollback completed successfully"
        
        # Clean up old backups
        cleanup_old_backups
        
        return 0
    else
        log_error "💥 Rollback verification failed"
        send_notification "critical" "Rollback verification failed"
        return 1
    fi
}

# Check if this is a new deployment (for backup)
check_and_backup() {
    if [ "${1:-}" = "--backup-if-success" ]; then
        log "💾 Saving successful deployment state..."
        save_successful_state
        cleanup_old_backups
    fi
}

# Main execution
main() {
    log "🚨 Asmblr Rollback Script Activated"
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.production.yml" ]; then
        log_error "docker-compose.production.yml not found. Run from project root."
        exit 1
    fi
    
    # Check Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Perform rollback
    if perform_rollback; then
        log_success "Rollback procedure completed"
        exit 0
    else
        log_error "Rollback procedure failed"
        exit 1
    fi
}

# Handle backup flag
if [ "${1:-}" = "--backup-if-success" ]; then
    check_and_backup "$1"
else
    main "$@"
fi
