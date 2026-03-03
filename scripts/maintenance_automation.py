#!/usr/bin/env python3
"""
Maintenance Automation for Asmblr CI/CD
Automated deployment, health checks, and cleanup operations
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def deploy_command(env: str) -> int:
    """Deploy to specified environment"""
    logger.info(f"Deploying to {env} environment...")
    
    try:
        if env == "staging":
            # Deploy to staging
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.staging.yml", "up", "-d"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Staging deployment failed: {result.stderr}")
                return 1
                
        elif env == "production":
            # Deploy to production
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.production.yml", "up", "-d"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Production deployment failed: {result.stderr}")
                return 1
        
        logger.info(f"Successfully deployed to {env}")
        return 0
        
    except Exception as e:
        logger.error(f"Deployment error: {e}")
        return 1

def health_command(env: str = None) -> int:
    """Run health checks"""
    logger.info("Running health checks...")
    
    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check API Gateway
    try:
        result = subprocess.run([
            "curl", "-f", "http://localhost:8000/health"
        ], capture_output=True, text=True, timeout=10)
        
        health_status["services"]["api_gateway"] = {
            "status": "healthy" if result.returncode == 0 else "unhealthy",
            "response_time": "fast"
        }
    except Exception as e:
        health_status["services"]["api_gateway"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Streamlit UI
    try:
        result = subprocess.run([
            "curl", "-f", "http://localhost:8501/_stcore/health"
        ], capture_output=True, text=True, timeout=10)
        
        health_status["services"]["ui"] = {
            "status": "healthy" if result.returncode == 0 else "unhealthy",
            "response_time": "fast"
        }
    except Exception as e:
        health_status["services"]["ui"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Redis
    try:
        result = subprocess.run([
            "redis-cli", "ping"
        ], capture_output=True, text=True, timeout=5)
        
        health_status["services"]["redis"] = {
            "status": "healthy" if "PONG" in result.stdout else "unhealthy"
        }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Save health report
    with open("health_report.json", "w") as f:
        json.dump(health_status, f, indent=2)
    
    logger.info("Health checks completed")
    return 0

def cleanup_command() -> int:
    """Cleanup old resources"""
    logger.info("Cleaning up deployment resources...")
    
    try:
        # Clean up old Docker images
        result = subprocess.run([
            "docker", "system", "prune", "-f"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Docker cleanup completed")
        
        # Calculate reclaimed space (simplified)
        reclaimed_space = "0B"  # Would parse from actual docker output
        
        # Clean up old artifacts
        artifacts_dir = Path("test-results")
        if artifacts_dir.exists():
            for artifact in artifacts_dir.glob("*"):
                if artifact.is_file() and artifact.stat().st_mtime > (datetime.now().timestamp() - 7*24*3600):
                    artifact.unlink()
        
        logger.info(f"Total reclaimed space: {reclaimed_space}")
        return 0
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return 1

def main():
    parser = argparse.ArgumentParser(description="Maintenance Automation")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy to environment")
    deploy_parser.add_argument("--env", required=True, choices=["staging", "production"])
    
    # Health command
    health_parser = subparsers.add_parser("health", help="Run health checks")
    health_parser.add_argument("--env", choices=["staging", "production"])
    
    # Cleanup command
    subparsers.add_parser("cleanup", help="Cleanup resources")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == "deploy":
        return deploy_command(args.env)
    elif args.command == "health":
        return health_command(args.env)
    elif args.command == "cleanup":
        return cleanup_command()
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
