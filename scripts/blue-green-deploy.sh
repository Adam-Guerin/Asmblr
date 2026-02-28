#!/bin/bash

set -e

# Blue-Green Deployment Script for Asmblr
# Usage: ./blue-green-deploy.sh <environment> <git-sha>

ENVIRONMENT=${1:-"staging"}
GIT_SHA=${2:-"latest"}
BLUE_PORT=8000
GREEN_PORT=8001
HEALTH_CHECK_TIMEOUT=300
COMPOSE_FILE="docker-compose.${ENVIRONMENT}.yml"

echo "🚀 Starting Blue-Green deployment for ${ENVIRONMENT} environment"
echo "📦 Deploying SHA: ${GIT_SHA}"

# Function to check service health
check_health() {
    local port=$1
    local service_name=$2
    echo "🔍 Checking health of ${service_name} on port ${port}..."
    
    local timeout=0
    while [ $timeout -lt $HEALTH_CHECK_TIMEOUT ]; do
        if curl -f -s "http://localhost:${port}/health" > /dev/null; then
            echo "✅ ${service_name} is healthy on port ${port}"
            return 0
        fi
        echo "⏳ Waiting for ${service_name} to be healthy... (${timeout}s/${HEALTH_CHECK_TIMEOUT}s)"
        sleep 5
        timeout=$((timeout + 5))
    done
    
    echo "❌ ${service_name} health check failed on port ${port}"
    return 1
}

# Function to switch traffic
switch_traffic() {
    local active_port=$1
    local inactive_port=$2
    local active_color=$3
    local inactive_color=$4
    
    echo "🔄 Switching traffic from ${active_color} (port ${active_port}) to ${inactive_color} (port ${inactive_port})"
    
    # Update nginx/reverse proxy configuration
    if command -v nginx &> /dev/null; then
        sed -i "s/proxy_pass http://localhost:${active_port}/proxy_pass http://localhost:${inactive_port}/g" /etc/nginx/sites-available/asmblr
        nginx -s reload
        echo "✅ Nginx reloaded, traffic switched to ${inactive_color}"
    else
        echo "⚠️  Nginx not found, manual traffic switch required"
        echo "   Update your load balancer to point to port ${inactive_port}"
    fi
}

# Determine current active environment
echo "🔍 Determining current active environment..."
if curl -f -s "http://localhost:${BLUE_PORT}/health" > /dev/null; then
    ACTIVE="blue"
    INACTIVE="green"
    ACTIVE_PORT=$BLUE_PORT
    INACTIVE_PORT=$GREEN_PORT
    echo "🔵 Blue environment is currently active"
elif curl -f -s "http://localhost:${GREEN_PORT}/health" > /dev/null; then
    ACTIVE="green"
    INACTIVE="blue"
    ACTIVE_PORT=$GREEN_PORT
    INACTIVE_PORT=$BLUE_PORT
    echo "🟢 Green environment is currently active"
else
    echo "🆕 No active environment found, starting with blue"
    ACTIVE="none"
    INACTIVE="blue"
    ACTIVE_PORT=""
    INACTIVE_PORT=$BLUE_PORT
fi

# Update docker-compose file with new image tags
echo "📝 Updating docker-compose configuration..."
sed -i "s|:latest|:${GIT_SHA}|g" $COMPOSE_FILE

# Deploy to inactive environment
echo "🚀 Deploying to ${INACTIVE} environment..."
if [ "$INACTIVE" = "blue" ]; then
    docker-compose -f $COMPOSE_FILE -p asmblr-blue up -d
else
    # Modify ports for green deployment
    cp $COMPOSE_FILE docker-compose-green.yml
    sed -i "s/127.0.0.1:8000:8000/127.0.0.1:${GREEN_PORT}:8000/g" docker-compose-green.yml
    sed -i "s/127.0.0.1:8501:8501/127.0.0.1:8502:8501/g" docker-compose-green.yml
    docker-compose -f docker-compose-green.yml -p asmblr-green up -d
fi

# Wait for inactive environment to be healthy
echo "⏳ Waiting for ${INACTIVE} environment to be healthy..."
if [ "$INACTIVE" = "blue" ]; then
    check_health $BLUE_PORT "Blue"
else
    check_health $GREEN_PORT "Green"
fi

# Run smoke tests on new environment
echo "🧪 Running smoke tests on ${INACTIVE} environment..."
if [ "$INACTIVE" = "blue" ]; then
    TEST_URL="http://localhost:${BLUE_PORT}"
else
    TEST_URL="http://localhost:${GREEN_PORT}"
fi

# Set environment for tests
export ASMblr_API_URL=$TEST_URL
python -m pytest tests/smoke/ -v --tb=short

if [ $? -ne 0 ]; then
    echo "❌ Smoke tests failed on ${INACTIVE} environment"
    echo "🔄 Rolling back deployment..."
    
    # Stop failed deployment
    if [ "$INACTIVE" = "blue" ]; then
        docker-compose -f $COMPOSE_FILE -p asmblr-blue down
    else
        docker-compose -f docker-compose-green.yml -p asmblr-green down
        rm -f docker-compose-green.yml
    fi
    
    exit 1
fi

echo "✅ Smoke tests passed on ${INACTIVE} environment"

# Switch traffic to new environment
if [ "$ACTIVE" != "none" ]; then
    switch_traffic $ACTIVE_PORT $INACTIVE_PORT $ACTIVE $INACTIVE
    
    # Wait for traffic switch to take effect
    echo "⏳ Waiting for traffic switch to take effect..."
    sleep 10
    
    # Verify new environment is serving traffic
    echo "🔍 Verifying traffic switch..."
    if curl -f -s "http://localhost:80/health" > /dev/null; then
        echo "✅ Traffic successfully switched to ${INACTIVE} environment"
    else
        echo "❌ Traffic switch verification failed"
        echo "🔄 Rolling back to ${ACTIVE} environment..."
        switch_traffic $INACTIVE_PORT $ACTIVE_PORT $INACTIVE $ACTIVE
        exit 1
    fi
else
    echo "🆕 First deployment, no traffic switch needed"
    # Configure load balancer to point to blue environment
    echo "📝 Configure your load balancer to point to port ${BLUE_PORT}"
fi

# Clean up old environment if it exists
if [ "$ACTIVE" != "none" ]; then
    echo "🧹 Cleaning up old ${ACTIVE} environment..."
    if [ "$ACTIVE" = "blue" ]; then
        docker-compose -f $COMPOSE_FILE -p asmblr-blue down
    else
        docker-compose -f docker-compose-green.yml -p asmblr-green down
        rm -f docker-compose-green.yml
    fi
fi

echo "🎉 Blue-Green deployment completed successfully!"
echo "📍 ${INACTIVE} environment is now active"
echo "🔗 Health endpoint: http://localhost:${INACTIVE_PORT}/health"

# Create deployment marker
echo "${GIT_SHA}" > "deployment-${ENVIRONMENT}-${INACTIVE}.txt"
echo "$(date)" >> "deployment-${ENVIRONMENT}-${INACTIVE}.txt"

echo "📊 Deployment summary:"
echo "   Environment: ${ENVIRONMENT}"
echo "   Active color: ${INACTIVE}"
echo "   Git SHA: ${GIT_SHA}"
echo "   Deployed at: $(date)"
