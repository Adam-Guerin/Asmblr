#!/bin/bash

# Asmblr Production Deployment Script
# Automated deployment with health checks and rollback

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_ENV=${DEPLOYMENT_ENV:-production}
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
HEALTH_CHECK_URL="http://localhost:8000/health"
MAX_RETRIES=30
RETRY_DELAY=10

echo -e "${BLUE}🚀 Asmblr Production Deployment${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "Environment: ${YELLOW}$DEPLOYMENT_ENV${NC}"
echo -e "Timestamp: $(date)"
echo ""

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Pre-deployment checks
pre_deployment_checks() {
    print_info "Running pre-deployment checks..."
    
    # Check required commands
    local required_commands=("docker" "docker-compose" "curl" "git")
    for cmd in "${required_commands[@]}"; do
        if ! command_exists "$cmd"; then
            print_error "Required command not found: $cmd"
            exit 1
        fi
    done
    
    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check environment file
    if [ ! -f ".env.production" ]; then
        print_warning ".env.production not found, copying from .env.example"
        cp .env.example .env.production
        print_warning "Please update .env.production with production values"
        exit 1
    fi
    
    # Check git status
    if [ -n "$(git status --porcelain)" ]; then
        print_warning "Uncommitted changes detected"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Deployment cancelled"
            exit 0
        fi
    fi
    
    print_status "Pre-deployment checks passed"
}

# Create backup
create_backup() {
    print_info "Creating backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    if docker-compose -f docker-compose.production.yml ps -q postgres >/dev/null 2>&1; then
        print_info "Backing up database..."
        docker-compose -f docker-compose.production.yml exec -T postgres pg_dump -U asmblr asmblr > "$BACKUP_DIR/database.sql"
    fi
    
    # Backup configuration
    cp .env.production "$BACKUP_DIR/"
    cp docker-compose.production.yml "$BACKUP_DIR/"
    
    # Backup runs directory
    if [ -d "runs" ]; then
        cp -r runs "$BACKUP_DIR/"
    fi
    
    print_status "Backup created: $BACKUP_DIR"
}

# Build and deploy
deploy_application() {
    print_info "Building and deploying application..."
    
    # Set production environment
    export DEPLOYMENT_ENV=production
    
    # Pull latest images
    print_info "Pulling latest images..."
    docker-compose -f docker-compose.production.yml pull
    
    # Build application
    print_info "Building application..."
    docker-compose -f docker-compose.production.yml build --no-cache
    
    # Stop existing services
    print_info "Stopping existing services..."
    docker-compose -f docker-compose.production.yml down
    
    # Start services
    print_info "Starting services..."
    docker-compose -f docker-compose.production.yml up -d
    
    print_status "Application deployed"
}

# Health check
health_check() {
    print_info "Performing health checks..."
    
    local retry_count=0
    local healthy=false
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        if curl -f -s "$HEALTH_CHECK_URL" >/dev/null 2>&1; then
            healthy=true
            break
        fi
        
        retry_count=$((retry_count + 1))
        print_info "Health check attempt $retry_count/$MAX_RETRIES..."
        sleep $RETRY_DELAY
    done
    
    if [ "$healthy" = true ]; then
        print_status "Health check passed"
    else
        print_error "Health check failed after $MAX_RETRIES attempts"
        return 1
    fi
}

# Post-deployment verification
post_deployment_verification() {
    print_info "Running post-deployment verification..."
    
    # Check all services are running
    local services=("asmblr" "postgres" "redis" "ollama" "nginx")
    for service in "${services[@]}"; do
        if docker-compose -f docker-compose.production.yml ps -q "$service" >/dev/null 2>&1; then
            print_status "Service $service is running"
        else
            print_error "Service $service is not running"
            return 1
        fi
    done
    
    # Check application endpoints
    local endpoints=(
        "http://localhost:8000/health"
        "http://localhost:8000/api/status"
        "http://localhost:8501"  # Streamlit
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f -s "$endpoint" >/dev/null 2>&1; then
            print_status "Endpoint $endpoint is accessible"
        else
            print_warning "Endpoint $endpoint is not accessible"
        fi
    done
    
    print_status "Post-deployment verification completed"
}

# Rollback function
rollback() {
    print_error "Deployment failed, initiating rollback..."
    
    # Stop current deployment
    docker-compose -f docker-compose.production.yml down
    
    # Restore from backup if available
    if [ -d "$BACKUP_DIR" ]; then
        print_info "Restoring from backup..."
        
        # Restore database
        if [ -f "$BACKUP_DIR/database.sql" ]; then
            docker-compose -f docker-compose.production.yml up -d postgres
            sleep 10
            docker-compose -f docker-compose.production.yml exec -T postgres psql -U asmblr -c "DROP DATABASE IF EXISTS asmblr;"
            docker-compose -f docker-compose.production.yml exec -T postgres psql -U asmblr -c "CREATE DATABASE asmblr;"
            docker-compose -f docker-compose.production.yml exec -T postgres psql -U asmblr asmblr < "$BACKUP_DIR/database.sql"
        fi
        
        # Restore configuration
        cp "$BACKUP_DIR/.env.production" .env.production
        
        # Restart services
        docker-compose -f docker-compose.production.yml up -d
        
        print_status "Rollback completed"
    else
        print_error "No backup available for rollback"
    fi
}

# Cleanup old backups
cleanup_backups() {
    print_info "Cleaning up old backups..."
    
    # Keep only last 7 days of backups
    find ./backups -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    
    print_status "Backup cleanup completed"
}

# Main deployment flow
main() {
    echo -e "${BLUE}Starting deployment process...${NC}"
    
    # Pre-deployment checks
    pre_deployment_checks
    
    # Create backup
    create_backup
    
    # Deploy application
    if ! deploy_application; then
        rollback
        exit 1
    fi
    
    # Health check
    if ! health_check; then
        rollback
        exit 1
    fi
    
    # Post-deployment verification
    if ! post_deployment_verification; then
        rollback
        exit 1
    fi
    
    # Cleanup
    cleanup_backups
    
    echo ""
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo -e "${GREEN}📊 Application is running at: http://localhost:8000${NC}"
    echo -e "${GREEN}🌐 UI available at: http://localhost:8501${NC}"
    echo -e "${GREEN}📈 Monitoring at: http://localhost:3001${NC}"
    echo ""
    echo -e "${BLUE}Backup location: $BACKUP_DIR${NC}"
    echo -e "${BLUE}To rollback: ./rollback.sh $BACKUP_DIR${NC}"
}

# Handle script interruption
trap 'print_error "Deployment interrupted"; rollback; exit 1' INT TERM

# Run main function
main "$@"
