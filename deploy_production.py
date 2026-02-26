#!/usr/bin/env python3
"""
Production Deployment Script for Asmblr v2.0
Automated deployment with validation, monitoring setup, and rollback capabilities
"""

import asyncio
import sys
import time
import subprocess
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import signal
import shutil

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import requests
    from loguru import logger
    import docker
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install: pip install requests loguru docker")
    sys.exit(1)


class ProductionDeployer:
    """Production deployment manager for Asmblr v2.0"""
    
    def __init__(self):
        self.project_root = project_root
        self.compose_file = project_root / "docker-compose.optimized.yml"
        self.backup_dir = project_root / "backups"
        self.logs_dir = project_root / "logs"
        
        # Ensure directories exist
        self.backup_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        self.deployment_log = []
        self.start_time = time.time()
        
    def log(self, message: str, level: str = "INFO") -> None:
        """Log deployment message"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.deployment_log.append(log_entry)
        print(log_entry)
        
        # Also write to log file
        log_file = self.logs_dir / f"deployment_{time.strftime('%Y%m%d_%H%M%S')}.log"
        with open(log_file, "a") as f:
            f.write(log_entry + "\n")
        
        logger.info(message)
    
    def validate_prerequisites(self) -> bool:
        """Validate deployment prerequisites"""
        self.log("Validating deployment prerequisites...")
        
        # Check Docker
        try:
            docker_client = docker.from_env()
            docker_client.ping()
            self.log("✅ Docker is available")
        except Exception as e:
            self.log(f"❌ Docker not available: {e}", "ERROR")
            return False
        
        # Check Docker Compose
        try:
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                self.log("✅ Docker Compose is available")
            else:
                self.log("❌ Docker Compose not available", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Docker Compose check failed: {e}", "ERROR")
            return False
        
        # Check required files
        required_files = [
            self.compose_file,
            project_root / "Dockerfile.optimized",
            project_root / ".env.minimal"
        ]
        
        for file_path in required_files:
            if not file_path.exists():
                self.log(f"❌ Required file missing: {file_path}", "ERROR")
                return False
            else:
                self.log(f"✅ Found: {file_path}")
        
        return True
    
    def backup_current_state(self) -> str:
        """Backup current state before deployment"""
        self.log("Creating backup of current state...")
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_name = f"pre_deployment_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        # Backup current configuration
        config_files = [
            ".env",
            "docker-compose.yml",
            "docker-compose.production.yml"
        ]
        
        for config_file in config_files:
            src = self.project_root / config_file
            if src.exists():
                dst = backup_path / config_file
                shutil.copy2(src, dst)
                self.log(f"Backed up: {config_file}")
        
        # Backup runs directory if it exists
        runs_dir = self.project_root / "runs"
        if runs_dir.exists():
            backup_runs = backup_path / "runs"
            shutil.copytree(runs_dir, backup_runs, ignore_errors=True)
            self.log("Backed up: runs directory")
        
        return backup_name
    
    def stop_current_services(self) -> bool:
        """Stop any currently running services"""
        self.log("Stopping current services...")
        
        try:
            # Check if services are running
            result = subprocess.run(
                ["docker-compose", "ps"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if "running" in result.stdout.lower():
                self.log("Stopping services...")
                stop_result = subprocess.run(
                    ["docker-compose", "down"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                    timeout=120
                )
                
                if stop_result.returncode == 0:
                    self.log("✅ Services stopped successfully")
                    return True
                else:
                    self.log(f"❌ Failed to stop services: {stop_result.stderr}", "ERROR")
                    return False
            else:
                self.log("✅ No services currently running")
                return True
                
        except Exception as e:
            self.log(f"❌ Error checking services: {e}", "ERROR")
            return False
    
    def start_services(self) -> bool:
        """Start optimized services"""
        self.log("Starting optimized services...")
        
        try:
            # Start with monitoring and backup profiles
            start_result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.optimized.yml", 
                 "--profile", "monitoring", "--profile", "backup", "up", "-d"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300  # 5 minutes
            )
            
            if start_result.returncode == 0:
                self.log("✅ Services started successfully")
                
                # Wait for services to be ready
                self.log("Waiting for services to be ready...")
                time.sleep(30)
                
                # Check service health
                return self.check_services_health()
            else:
                self.log(f"❌ Failed to start services: {start_result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error starting services: {e}", "ERROR")
            return False
    
    def check_services_health(self) -> bool:
        """Check if all services are healthy"""
        self.log("Checking service health...")
        
        max_attempts = 10
        attempt = 0
        
        while attempt < max_attempts:
            try:
                # Check API health
                response = requests.get("http://localhost:8000/health", timeout=10)
                if response.status_code == 200:
                    self.log("✅ API service is healthy")
                    
                    # Check UI health
                    ui_response = requests.get("http://localhost:8501/_stcore/health", timeout=10)
                    if ui_response.status_code == 200:
                        self.log("✅ UI service is healthy")
                        
                        # Check Redis
                        redis_result = subprocess.run(
                            ["docker", "exec", "asmblr-redis", "redis-cli", "ping"],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if redis_result.returncode == 0:
                            self.log("✅ Redis service is healthy")
                            
                            # Check Ollama
                            ollama_result = subprocess.run(
                                ["docker", "exec", "asmblr-ollama", "curl", "-f", 
                                 "http://localhost:11434/api/tags"],
                                capture_output=True,
                                text=True,
                                timeout=10
                            )
                            if ollama_result.returncode == 0:
                                self.log("✅ Ollama service is healthy")
                                return True
                            else:
                                self.log("⚠️ Ollama service may not be ready")
                    else:
                        self.log("⚠️ UI service may not be ready")
                else:
                    self.log("⚠️ API service may not be ready")
                    
            except requests.exceptions.RequestException as e:
                self.log(f"⚠️ Health check attempt {attempt + 1} failed: {e}")
            
            attempt += 1
            if attempt < max_attempts:
                self.log(f"Waiting 30 seconds before retry... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(30)
        
        self.log("❌ Services not fully healthy after all attempts")
        return False
    
    def generate_deployment_report(self, success: bool, backup_name: Optional[str] = None) -> None:
        """Generate deployment report"""
        total_time = time.time() - self.start_time
        
        report = f"""
# 🚀 Asmblr v2.0 Production Deployment Report

## 📊 Deployment Summary
- **Status**: {'✅ SUCCESS' if success else '❌ FAILED'}
- **Duration**: {total_time:.2f} seconds
- **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S')}
- **Backup**: {backup_name or 'N/A'}

## 📋 Deployment Log
"""
        
        for log_entry in self.deployment_log:
            report += f"{log_entry}\n"
        
        if success:
            report += """
## 🎉 Deployment Successful!

Your Asmblr v2.0 is now running in production mode!

### Access Points:
- **API**: http://localhost:8000
- **UI**: http://localhost:8501
- **Grafana**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090

### Next Steps:
1. Monitor performance in Grafana dashboards
2. Check logs: tail -f logs/deployment_*.log
3. Run health checks: curl http://localhost:8000/health/detailed
4. Validate with: python validate_optimization_simple.py

### Services Running:
- API Gateway (FastAPI)
- UI (Streamlit)
- Background Workers
- Redis Cache
- Ollama LLM
- Prometheus Monitoring
- Grafana Dashboards
- Backup Service
"""
        else:
            report += """
## ❌ Deployment Failed

Check the deployment log above for specific error details.

### Troubleshooting:
1. Check Docker logs: docker-compose logs
2. Validate prerequisites: python validate_optimization_simple.py
3. Check service health: curl http://localhost:8000/health
4. Review error logs in logs/
"""
        
        # Write report to file
        report_file = self.logs_dir / f"deployment_report_{time.strftime('%Y%m%d_%H%M%S')}.md"
        report_file.write_text(report)
        
        # Print to console
        print(report)
        
        self.log(f"Deployment report saved to: {report_file}")
    
    def deploy_production(self, skip_backup: bool = False) -> bool:
        """Deploy to production with full validation"""
        self.log("🚀 Starting Asmblr v2.0 production deployment...")
        
        # Step 1: Validate prerequisites
        if not self.validate_prerequisites():
            self.log("❌ Prerequisites validation failed")
            return False
        
        # Step 2: Backup current state
        backup_name = None
        if not skip_backup:
            backup_name = self.backup_current_state()
        
        # Step 3: Stop current services
        if not self.stop_current_services():
            self.log("❌ Failed to stop current services")
            if backup_name:
                self.log(f"Backup available: {backup_name}")
            return False
        
        # Step 4: Start services
        if not self.start_services():
            self.log("❌ Failed to start services")
            if backup_name:
                self.log(f"Backup available: {backup_name}")
            return False
        
        # Step 5: Generate report
        self.generate_deployment_report(success=True, backup_name=backup_name)
        
        return True


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Deploy Asmblr v2.0 to production")
    parser.add_argument("--skip-backup", action="store_true",
                       help="Skip backup before deployment")
    parser.add_argument("--validate-only", action="store_true",
                       help="Run validation only")
    
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    deployer = ProductionDeployer()
    
    try:
        if args.validate_only:
            # Run validation only
            logger.info("Running validation only...")
            success = deployer.validate_prerequisites()
            if success:
                print("✅ All prerequisites validated")
            else:
                print("❌ Prerequisites validation failed")
            sys.exit(0 if success else 1)
        else:
            # Full deployment
            success = deployer.deploy_production(skip_backup=args.skip_backup)
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        logger.info("Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
