#!/bin/bash

# Comprehensive health check script for Asmblr production deployment
# Checks all services and provides detailed status reporting

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HEALTH_CHECK_TIMEOUT=30
RETRY_COUNT=3
RETRY_DELAY=5

# Service endpoints to check
declare -A SERVICES=(
    ["API Gateway"]="http://localhost:8000/health"
    ["UI"]="http://localhost:8501/_stcore/health"
    ["Core Service 1"]="http://localhost:8001/health"
    ["Core Service 2"]="http://localhost:8002/health"
    ["Agents Service 1"]="http://localhost:8003/health"
    ["Agents Service 2"]="http://localhost:8004/health"
    ["Media Service 1"]="http://localhost:8005/health"
    ["Media Service 2"]="http://localhost:8006/health"
    ["Redis"]="http://localhost:6379"
    ["PostgreSQL"]="postgresql://asmblr:${ASMblr_PASSWORD}@localhost:5432/asmblr"
    ["Ollama"]="http://localhost:11434/api/tags"
    ["Prometheus"]="http://localhost:9090/-/healthy"
    ["Grafana"]="http://localhost:3001/api/health"
)

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check individual service
check_service() {
    local service_name="$1"
    local endpoint="$2"
    local attempt=1
    
    while [ $attempt -le $RETRY_COUNT ]; do
        log "Checking $service_name (attempt $attempt/$RETRY_COUNT)..."
        
        if curl -f -s --max-time $HEALTH_CHECK_TIMEOUT "$endpoint" > /dev/null 2>&1; then
            log_success "$service_name is healthy"
            return 0
        else
            if [ $attempt -eq $RETRY_COUNT ]; then
                log_error "$service_name health check failed after $RETRY_COUNT attempts"
                return 1
            else
                log_warning "$service_name check failed, retrying in ${RETRY_DELAY}s..."
                sleep $RETRY_DELAY
            fi
        fi
        ((attempt++))
    done
}

# Check Docker containers
check_containers() {
    log "Checking Docker containers status..."
    
    local required_containers=(
        "nginx"
        "api-gateway-1"
        "api-gateway-2"
        "asmblr-core-1"
        "asmblr-core-2"
        "asmblr-agents-1"
        "asmblr-agents-2"
        "asmblr-media-1"
        "asmblr-media-2"
        "postgres-primary"
        "postgres-replica"
        "redis-cluster"
        "ollama-cluster"
        "prometheus"
        "grafana"
    )
    
    local failed_containers=()
    
    for container in "${required_containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "^${container}$"; then
            local status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-healthcheck")
            if [[ "$status" == "healthy" || "$status" == "no-healthcheck" ]]; then
                log_success "Container $container is running"
            else
                log_error "Container $container is unhealthy (status: $status)"
                failed_containers+=("$container")
            fi
        else
            log_error "Container $container is not running"
            failed_containers+=("$container")
        fi
    done
    
    if [ ${#failed_containers[@]} -eq 0 ]; then
        log_success "All required containers are running"
        return 0
    else
        log_error "Failed containers: ${failed_containers[*]}"
        return 1
    fi
}

# Check database connectivity
check_database() {
    log "Checking database connectivity..."
    
    if docker exec postgres-primary pg_isready -U asmblr > /dev/null 2>&1; then
        log_success "Primary database is ready"
    else
        log_error "Primary database is not ready"
        return 1
    fi
    
    if docker exec postgres-replica pg_isready -U asmblr > /dev/null 2>&1; then
        log_success "Replica database is ready"
    else
        log_warning "Replica database is not ready (may be starting)"
    fi
    
    # Test replication
    local replication_status=$(docker exec postgres-primary psql -U asmblr -d asmblr -t -c "SELECT count(*) FROM pg_stat_replication;" 2>/dev/null | tr -d ' ')
    if [[ "$replication_status" -gt 0 ]]; then
        log_success "Database replication is active ($replication_status replicas)"
    else
        log_warning "No active database replicas found"
    fi
}

# Check Redis cluster
check_redis() {
    log "Checking Redis cluster..."
    
    if docker exec redis-cluster redis-cli ping > /dev/null 2>&1; then
        log_success "Redis cluster is responding"
        
        # Check Redis info
        local redis_info=$(docker exec redis-cluster redis-cli info server 2>/dev/null | head -5)
        log "Redis info: $(echo "$redis_info" | tr '\n' ' ')"
    else
        log_error "Redis cluster is not responding"
        return 1
    fi
}

# Check Ollama models
check_ollama() {
    log "Checking Ollama service and models..."
    
    if curl -f -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        log_success "Ollama service is responding"
        
        # Check if required models are available
        local models=$(curl -s http://localhost:11434/api/tags | jq -r '.models[].name' 2>/dev/null || echo "")
        local required_models=("llama3.1:8b" "qwen2.5-coder:7b")
        
        for model in "${required_models[@]}"; do
            if echo "$models" | grep -q "$model"; then
                log_success "Model $model is available"
            else
                log_warning "Model $model is not available"
            fi
        done
    else
        log_error "Ollama service is not responding"
        return 1
    fi
}

# Check disk space
check_disk_space() {
    log "Checking disk space..."
    
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -lt 80 ]; then
        log_success "Disk usage is at ${disk_usage}%"
    elif [ "$disk_usage" -lt 90 ]; then
        log_warning "Disk usage is high at ${disk_usage}%"
    else
        log_error "Disk usage is critical at ${disk_usage}%"
        return 1
    fi
}

# Check memory usage
check_memory() {
    log "Checking memory usage..."
    
    local memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$memory_usage" -lt 80 ]; then
        log_success "Memory usage is at ${memory_usage}%"
    elif [ "$memory_usage" -lt 90 ]; then
        log_warning "Memory usage is high at ${memory_usage}%"
    else
        log_error "Memory usage is critical at ${memory_usage}%"
        return 1
    fi
}

# Generate health report
generate_report() {
    local overall_status=$1
    local report_file="health-check-report-$(date +%Y%m%d_%H%M%S).json"
    
    log "Generating health report: $report_file"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "overall_status": "$overall_status",
    "services": {
        "api_gateway": "$(curl -s http://localhost:8000/health 2>/dev/null || echo 'unhealthy')",
        "ui": "$(curl -s http://localhost:8501/_stcore/health 2>/dev/null || echo 'unhealthy')",
        "database": "$(docker exec postgres-primary pg_isready -U asmblr 2>/dev/null || echo 'unhealthy')",
        "redis": "$(docker exec redis-cluster redis-cli ping 2>/dev/null || echo 'unhealthy')",
        "ollama": "$(curl -s http://localhost:11434/api/tags 2>/dev/null || echo 'unhealthy')",
        "prometheus": "$(curl -s http://localhost:9090/-/healthy 2>/dev/null || echo 'unhealthy')",
        "grafana": "$(curl -s http://localhost:3001/api/health 2>/dev/null || echo 'unhealthy')"
    },
    "system": {
        "disk_usage": "$(df / | awk 'NR==2 {print $5}')",
        "memory_usage": "$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')%",
        "container_count": "$(docker ps --format '{{.Names}}' | wc -l)"
    }
}
EOF
    
    log_success "Health report saved to $report_file"
}

# Main execution
main() {
    log "🏥 Starting comprehensive health check..."
    
    local failed_checks=0
    
    # Check containers first
    if ! check_containers; then
        ((failed_checks++))
    fi
    
    # Check system resources
    if ! check_disk_space; then
        ((failed_checks++))
    fi
    
    if ! check_memory; then
        ((failed_checks++))
    fi
    
    # Check services
    for service in "${!SERVICES[@]}"; do
        if ! check_service "$service" "${SERVICES[$service]}"; then
            ((failed_checks++))
        fi
    done
    
    # Specialized checks
    if ! check_database; then
        ((failed_checks++))
    fi
    
    if ! check_redis; then
        ((failed_checks++))
    fi
    
    if ! check_ollama; then
        ((failed_checks++))
    fi
    
    # Generate report
    if [ $failed_checks -eq 0 ]; then
        generate_report "healthy"
        log_success "🎉 All health checks passed! System is healthy."
        exit 0
    else
        generate_report "unhealthy"
        log_error "💥 $failed_checks health check(s) failed. System needs attention."
        exit 1
    fi
}

# Run main function
main "$@"
