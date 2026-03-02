#!/usr/bin/env python3
"""
Production Monitoring System for Asmblr
Comprehensive monitoring, alerting, and health checks
"""

import time
import json
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import requests
from dataclasses import dataclass

@dataclass
class HealthCheck:
    name: str
    url: str
    expected_status: int = 200
    timeout: int = 10
    critical: bool = True

@dataclass
class MetricThreshold:
    name: str
    warning_threshold: float
    critical_threshold: float
    unit: str = ""

class ProductionMonitor:
    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or Path("monitoring/config.json")
        self.metrics_history = []
        self.alerts_sent = []
        self.logger = self._setup_logger()
        
        # Health checks
        self.health_checks = [
            HealthCheck("Main API", "http://localhost:8000/health", 200, 10, True),
            HealthCheck("Streamlit UI", "http://localhost:8501", 200, 10, True),
            HealthCheck("API Status", "http://localhost:8000/api/status", 200, 10, True),
            HealthCheck("Ollama", "http://localhost:11434/api/tags", 200, 10, True),
            HealthCheck("Grafana", "http://localhost:3001/api/health", 200, 10, False),
            HealthCheck("Prometheus", "http://localhost:9090/-/healthy", 200, 10, False),
        ]
        
        # Metric thresholds
        self.thresholds = [
            MetricThreshold("CPU Usage", 70.0, 90.0, "%"),
            MetricThreshold("Memory Usage", 80.0, 95.0, "%"),
            MetricThreshold("Disk Usage", 80.0, 95.0, "%"),
            MetricThreshold("Response Time", 1.0, 3.0, "s"),
            MetricThreshold("Error Rate", 5.0, 15.0, "%"),
        ]
    
    def _setup_logger(self) -> logging.Logger:
        """Setup monitoring logger"""
        logger = logging.getLogger("production_monitor")
        logger.setLevel(logging.INFO)
        
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(log_dir / "monitoring.log")
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def collect_system_metrics(self) -> dict:
        """Collect system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)
            
            # Network metrics
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv
            
            # Process metrics
            process_count = len(psutil.pids())
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "percent": memory_percent,
                    "available_gb": memory_available_gb,
                    "total_gb": memory.total / (1024**3)
                },
                "disk": {
                    "percent": disk_percent,
                    "free_gb": disk_free_gb,
                    "total_gb": disk.total / (1024**3)
                },
                "network": {
                    "bytes_sent": network_bytes_sent,
                    "bytes_recv": network_bytes_recv
                },
                "processes": {
                    "count": process_count
                }
            }
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def perform_health_checks(self) -> dict:
        """Perform health checks on all services"""
        results = {}
        
        for check in self.health_checks:
            try:
                start_time = time.time()
                response = requests.get(
                    check.url, 
                    timeout=check.timeout,
                    allow_redirects=True
                )
                response_time = time.time() - start_time
                
                results[check.name] = {
                    "status": "healthy" if response.status_code == check.expected_status else "unhealthy",
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "url": check.url,
                    "critical": check.critical,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                if response.status_code != check.expected_status:
                    self.logger.warning(
                        f"Health check failed for {check.name}: "
                        f"Expected {check.expected_status}, got {response.status_code}"
                    )
                
            except requests.exceptions.Timeout:
                results[check.name] = {
                    "status": "timeout",
                    "response_time": check.timeout,
                    "url": check.url,
                    "critical": check.critical,
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.logger.error(f"Health check timeout for {check.name}")
                
            except requests.exceptions.ConnectionError:
                results[check.name] = {
                    "status": "connection_error",
                    "url": check.url,
                    "critical": check.critical,
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.logger.error(f"Health check connection error for {check.name}")
                
            except Exception as e:
                results[check.name] = {
                    "status": "error",
                    "error": str(e),
                    "url": check.url,
                    "critical": check.critical,
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.logger.error(f"Health check error for {check.name}: {e}")
        
        return results
    
    def check_application_metrics(self) -> dict:
        """Check application-specific metrics"""
        metrics = {}
        
        try:
            # Check API response time
            start_time = time.time()
            response = requests.get("http://localhost:8000/health", timeout=10)
            api_response_time = time.time() - start_time
            metrics["api_response_time"] = api_response_time
            
            # Check error rate (simplified - in production, this would come from logs/metrics)
            metrics["error_rate"] = 0.0  # Placeholder
            
            # Check active runs
            try:
                runs_response = requests.get("http://localhost:8000/api/runs", timeout=10)
                if runs_response.status_code == 200:
                    runs_data = runs_response.json()
                    metrics["active_runs"] = len([r for r in runs_data if r.get("status") == "running"])
                    metrics["total_runs"] = len(runs_data)
            except:
                metrics["active_runs"] = 0
                metrics["total_runs"] = 0
            
            metrics["timestamp"] = datetime.utcnow().isoformat()
            
        except Exception as e:
            self.logger.error(f"Error checking application metrics: {e}")
        
        return metrics
    
    def evaluate_thresholds(self, metrics: dict) -> list[dict]:
        """Evaluate metrics against thresholds and generate alerts"""
        alerts = []
        
        # System metrics
        system_metrics = metrics.get("system", {})
        
        # CPU check
        cpu_percent = system_metrics.get("cpu", {}).get("percent", 0)
        if cpu_percent > 90:
            alerts.append({
                "type": "critical",
                "metric": "CPU Usage",
                "value": cpu_percent,
                "threshold": 90,
                "message": f"Critical CPU usage: {cpu_percent:.1f}%",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif cpu_percent > 70:
            alerts.append({
                "type": "warning",
                "metric": "CPU Usage",
                "value": cpu_percent,
                "threshold": 70,
                "message": f"High CPU usage: {cpu_percent:.1f}%",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Memory check
        memory_percent = system_metrics.get("memory", {}).get("percent", 0)
        if memory_percent > 95:
            alerts.append({
                "type": "critical",
                "metric": "Memory Usage",
                "value": memory_percent,
                "threshold": 95,
                "message": f"Critical memory usage: {memory_percent:.1f}%",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif memory_percent > 80:
            alerts.append({
                "type": "warning",
                "metric": "Memory Usage",
                "value": memory_percent,
                "threshold": 80,
                "message": f"High memory usage: {memory_percent:.1f}%",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Disk check
        disk_percent = system_metrics.get("disk", {}).get("percent", 0)
        if disk_percent > 95:
            alerts.append({
                "type": "critical",
                "metric": "Disk Usage",
                "value": disk_percent,
                "threshold": 95,
                "message": f"Critical disk usage: {disk_percent:.1f}%",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif disk_percent > 80:
            alerts.append({
                "type": "warning",
                "metric": "Disk Usage",
                "value": disk_percent,
                "threshold": 80,
                "message": f"High disk usage: {disk_percent:.1f}%",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Health check failures
        health_checks = metrics.get("health_checks", {})
        critical_failures = [
            name for name, result in health_checks.items() 
            if result.get("critical") and result.get("status") != "healthy"
        ]
        
        if critical_failures:
            alerts.append({
                "type": "critical",
                "metric": "Health Checks",
                "value": len(critical_failures),
                "threshold": 0,
                "message": f"Critical services down: {', '.join(critical_failures)}",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return alerts
    
    def generate_dashboard_data(self) -> dict:
        """Generate data for monitoring dashboard"""
        current_metrics = {
            "system": self.collect_system_metrics(),
            "health_checks": self.perform_health_checks(),
            "application": self.check_application_metrics()
        }
        
        # Store in history
        self.metrics_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            **current_metrics
        })
        
        # Keep only last 100 entries
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]
        
        # Evaluate alerts
        alerts = self.evaluate_thresholds(current_metrics)
        
        # Calculate overall status
        critical_alerts = [a for a in alerts if a["type"] == "critical"]
        warning_alerts = [a for a in alerts if a["type"] == "warning"]
        
        if critical_alerts:
            overall_status = "critical"
        elif warning_alerts:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": current_metrics,
            "alerts": alerts,
            "summary": {
                "critical_alerts": len(critical_alerts),
                "warning_alerts": len(warning_alerts),
                "total_alerts": len(alerts),
                "healthy_services": len([
                    r for r in current_metrics.get("health_checks", {}).values()
                    if r.get("status") == "healthy"
                ]),
                "total_services": len(current_metrics.get("health_checks", {}))
            }
        }
    
    def save_metrics(self, data: dict):
        """Save metrics to file"""
        metrics_dir = Path("monitoring/metrics")
        metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Save current metrics
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_file = metrics_dir / f"metrics_{timestamp}.json"
        with open(current_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Save latest metrics
        latest_file = metrics_dir / "latest.json"
        with open(latest_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Clean old files (keep last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        for file in metrics_dir.glob("metrics_*.json"):
            if file != latest_file:
                try:
                    file_time = datetime.strptime(
                        file.stem.split("_")[1], "%Y%m%d_%H%M%S"
                    )
                    if file_time < cutoff_time:
                        file.unlink()
                except:
                    pass
    
    async def start_monitoring(self, interval: int = 60):
        """Start continuous monitoring"""
        self.logger.info("Starting production monitoring...")
        
        while True:
            try:
                # Generate dashboard data
                data = self.generate_dashboard_data()
                
                # Save metrics
                self.save_metrics(data)
                
                # Log summary
                self.logger.info(
                    f"Status: {data['status']} | "
                    f"Alerts: {data['summary']['total_alerts']} | "
                    f"Services: {data['summary']['healthy_services']}/{data['summary']['total_services']}"
                )
                
                # Handle critical alerts
                critical_alerts = [a for a in data["alerts"] if a["type"] == "critical"]
                if critical_alerts:
                    self.logger.error(f"CRITICAL ALERTS: {len(critical_alerts)}")
                    for alert in critical_alerts:
                        self.logger.error(f"  - {alert['message']}")
                
                # Wait for next interval
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)

def main():
    """Main monitoring function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Asmblr Production Monitor")
    parser.add_argument("--interval", type=int, default=60, help="Monitoring interval in seconds")
    parser.add_argument("--oneshot", action="store_true", help="Run once and exit")
    args = parser.parse_args()
    
    monitor = ProductionMonitor()
    
    if args.oneshot:
        # Run once
        data = monitor.generate_dashboard_data()
        monitor.save_metrics(data)
        print(json.dumps(data, indent=2))
    else:
        # Start continuous monitoring
        asyncio.run(monitor.start_monitoring(args.interval))

if __name__ == "__main__":
    main()
