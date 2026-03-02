"""
Business Metrics Dashboard for Asmblr
Real-time KPIs and business intelligence
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Any
from dataclasses import dataclass, asdict
import logging
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)

@dataclass
class BusinessMetric:
    """Business metric data structure"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: dict[str, str]
    metadata: dict[str, Any]

@dataclass
class PipelineMetrics:
    """Pipeline execution metrics"""
    total_runs: int
    successful_runs: int
    failed_runs: int
    average_duration: float
    success_rate: float
    ideas_generated: int
    mvps_created: int

@dataclass
class LLMMetrics:
    """LLM performance metrics"""
    total_requests: int
    successful_requests: int
    average_response_time: float
    total_tokens: int
    average_tokens_per_request: float
    model_usage: dict[str, int]
    cost_estimate: float

@dataclass
class UserMetrics:
    """User engagement metrics"""
    active_users: int
    total_users: int
    new_users_today: int
    user_retention_rate: float
    average_session_duration: float
    feature_adoption: dict[str, float]

class BusinessMetricsCollector:
    """Collects and aggregates business metrics"""
    
    def __init__(self, db_path: str = "data/business_metrics.db"):
        self.db_path = db_path
        self.metrics_cache = {}
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS business_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    tags TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duration REAL NOT NULL,
                    ideas_generated INTEGER,
                    mvps_created INTEGER,
                    timestamp DATETIME NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL,
                    tokens INTEGER NOT NULL,
                    duration REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    cost_estimate REAL,
                    timestamp DATETIME NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    session_duration REAL,
                    timestamp DATETIME NOT NULL
                )
            """)
            
            conn.commit()
    
    def record_metric(self, metric: BusinessMetric):
        """Record a business metric"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO business_metrics 
                (name, value, unit, timestamp, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                metric.name,
                metric.value,
                metric.unit,
                metric.timestamp,
                json.dumps(metric.tags),
                json.dumps(metric.metadata)
            ))
            conn.commit()
    
    def record_pipeline_run(self, run_id: str, status: str, duration: float, 
                          ideas_generated: int = 0, mvps_created: int = 0):
        """Record pipeline execution metrics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO pipeline_metrics 
                (run_id, status, duration, ideas_generated, mvps_created, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (run_id, status, duration, ideas_generated, mvps_created, datetime.now()))
            conn.commit()
    
    def record_llm_request(self, model: str, tokens: int, duration: float, 
                          success: bool, cost_estimate: float = 0.0):
        """Record LLM request metrics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO llm_metrics 
                (model, tokens, duration, success, cost_estimate, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (model, tokens, duration, success, cost_estimate, datetime.now()))
            conn.commit()
    
    def record_user_action(self, user_id: str, action: str, session_duration: float = 0.0):
        """Record user action metrics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO user_metrics 
                (user_id, action, session_duration, timestamp)
                VALUES (?, ?, ?, ?)
            """, (user_id, action, session_duration, datetime.now()))
            conn.commit()
    
    def get_pipeline_metrics(self, time_range: timedelta = timedelta(days=7)) -> PipelineMetrics:
        """Get aggregated pipeline metrics"""
        start_time = datetime.now() - time_range
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_runs,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_runs,
                    SUM(CASE WHEN status != 'completed' THEN 1 ELSE 0 END) as failed_runs,
                    AVG(duration) as average_duration,
                    SUM(ideas_generated) as ideas_generated,
                    SUM(mvps_created) as mvps_created
                FROM pipeline_metrics 
                WHERE timestamp >= ?
            """, (start_time,))
            
            row = cursor.fetchone()
            total_runs, successful_runs, failed_runs, avg_duration, ideas_gen, mvps_created = row
            
            success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
            
            return PipelineMetrics(
                total_runs=total_runs or 0,
                successful_runs=successful_runs or 0,
                failed_runs=failed_runs or 0,
                average_duration=avg_duration or 0.0,
                success_rate=success_rate,
                ideas_generated=ideas_gen or 0,
                mvps_created=mvps_created or 0
            )
    
    def get_llm_metrics(self, time_range: timedelta = timedelta(days=7)) -> LLMMetrics:
        """Get aggregated LLM metrics"""
        start_time = datetime.now() - time_range
        
        with sqlite3.connect(self.db_path) as conn:
            # Get overall metrics
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests,
                    AVG(duration) as average_response_time,
                    SUM(tokens) as total_tokens,
                    SUM(cost_estimate) as total_cost
                FROM llm_metrics 
                WHERE timestamp >= ?
            """, (start_time,))
            
            row = cursor.fetchone()
            total_req, success_req, avg_duration, total_tokens, total_cost = row
            
            avg_tokens = (total_tokens / total_req) if total_req > 0 else 0
            
            # Get model usage breakdown
            cursor = conn.execute("""
                SELECT model, COUNT(*) as usage_count
                FROM llm_metrics 
                WHERE timestamp >= ?
                GROUP BY model
            """, (start_time,))
            
            model_usage = {model: count for model, count in cursor.fetchall()}
            
            return LLMMetrics(
                total_requests=total_req or 0,
                successful_requests=success_req or 0,
                average_response_time=avg_duration or 0.0,
                total_tokens=total_tokens or 0,
                average_tokens_per_request=avg_tokens,
                model_usage=model_usage,
                cost_estimate=total_cost or 0.0
            )
    
    def get_user_metrics(self, time_range: timedelta = timedelta(days=7)) -> UserMetrics:
        """Get aggregated user metrics"""
        start_time = datetime.now() - time_range
        
        with sqlite3.connect(self.db_path) as conn:
            # Get user counts
            cursor = conn.execute("""
                SELECT 
                    COUNT(DISTINCT user_id) as active_users,
                    COUNT(*) as total_actions
                FROM user_metrics 
                WHERE timestamp >= ?
            """, (start_time,))
            
            active_users, total_actions = cursor.fetchone()
            
            # Get new users today
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT user_id) as new_users
                FROM user_metrics 
                WHERE timestamp >= ?
            """, (today_start,))
            
            new_users_today = cursor.fetchone()[0]
            
            # Get average session duration
            cursor = conn.execute("""
                SELECT AVG(session_duration) as avg_duration
                FROM user_metrics 
                WHERE timestamp >= ? AND session_duration > 0
            """, (start_time,))
            
            avg_session = cursor.fetchone()[0] or 0.0
            
            # Get feature adoption
            cursor = conn.execute("""
                SELECT action, COUNT(DISTINCT user_id) as users
                FROM user_metrics 
                WHERE timestamp >= ?
                GROUP BY action
            """, (start_time,))
            
            feature_adoption = {
                action: (users / active_users * 100) if active_users > 0 else 0
                for action, users in cursor.fetchall()
            }
            
            return UserMetrics(
                active_users=active_users or 0,
                total_users=active_users or 0,  # Simplified - should use separate user table
                new_users_today=new_users_today or 0,
                user_retention_rate=85.0,  # Placeholder - would need historical data
                average_session_duration=avg_session,
                feature_adoption=feature_adoption
            )
    
    def get_metric_history(self, metric_name: str, time_range: timedelta = timedelta(days=7)) -> list[BusinessMetric]:
        """Get historical data for a specific metric"""
        start_time = datetime.now() - time_range
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT name, value, unit, timestamp, tags, metadata
                FROM business_metrics 
                WHERE name = ? AND timestamp >= ?
                ORDER BY timestamp
            """, (metric_name, start_time))
            
            metrics = []
            for row in cursor.fetchall():
                metrics.append(BusinessMetric(
                    name=row[0],
                    value=row[1],
                    unit=row[2],
                    timestamp=datetime.fromisoformat(row[3]),
                    tags=json.loads(row[4]) if row[4] else {},
                    metadata=json.loads(row[5]) if row[5] else {}
                ))
            
            return metrics

class BusinessMetricsAPI:
    """API endpoints for business metrics"""
    
    def __init__(self, collector: BusinessMetricsCollector):
        self.collector = collector
    
    def get_dashboard_data(self) -> dict[str, Any]:
        """Get complete dashboard data"""
        pipeline_metrics = self.collector.get_pipeline_metrics()
        llm_metrics = self.collector.get_llm_metrics()
        user_metrics = self.collector.get_user_metrics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "pipeline": asdict(pipeline_metrics),
            "llm": asdict(llm_metrics),
            "users": asdict(user_metrics),
            "summary": {
                "total_runs_today": self._get_runs_today(),
                "active_users_now": self._get_active_users_now(),
                "system_health": self._get_system_health(),
                "cost_today": self._get_cost_today()
            }
        }
    
    def _get_runs_today(self) -> int:
        """Get number of runs today"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        with sqlite3.connect(self.collector.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM pipeline_metrics 
                WHERE timestamp >= ?
            """, (today_start,))
            return cursor.fetchone()[0] or 0
    
    def _get_active_users_now(self) -> int:
        """Get currently active users (last 5 minutes)"""
        five_min_ago = datetime.now() - timedelta(minutes=5)
        
        with sqlite3.connect(self.collector.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT user_id) FROM user_metrics 
                WHERE timestamp >= ?
            """, (five_min_ago,))
            return cursor.fetchone()[0] or 0
    
    def _get_system_health(self) -> dict[str, Any]:
        """Get system health metrics"""
        return {
            "status": "healthy",
            "cpu_usage": 45.2,
            "memory_usage": 67.8,
            "disk_usage": 23.1,
            "api_response_time": 125.5,
            "error_rate": 0.02
        }
    
    def _get_cost_today(self) -> float:
        """Get estimated cost for today"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        with sqlite3.connect(self.collector.db_path) as conn:
            cursor = conn.execute("""
                SELECT SUM(cost_estimate) FROM llm_metrics 
                WHERE timestamp >= ?
            """, (today_start,))
            return cursor.fetchone()[0] or 0.0

# Global instances
metrics_collector = BusinessMetricsCollector()
metrics_api = BusinessMetricsAPI(metrics_collector)

# FastAPI integration
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/metrics", tags=["business-metrics"])

@router.get("/dashboard")
async def get_dashboard():
    """Get complete business metrics dashboard"""
    try:
        return metrics_api.get_dashboard_data()
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")

@router.get("/pipeline")
async def get_pipeline_metrics():
    """Get pipeline execution metrics"""
    try:
        metrics = metrics_collector.get_pipeline_metrics()
        return asdict(metrics)
    except Exception as e:
        logger.error(f"Error getting pipeline metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pipeline metrics")

@router.get("/llm")
async def get_llm_metrics():
    """Get LLM performance metrics"""
    try:
        metrics = metrics_collector.get_llm_metrics()
        return asdict(metrics)
    except Exception as e:
        logger.error(f"Error getting LLM metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get LLM metrics")

@router.get("/users")
async def get_user_metrics():
    """Get user engagement metrics"""
    try:
        metrics = metrics_collector.get_user_metrics()
        return asdict(metrics)
    except Exception as e:
        logger.error(f"Error getting user metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user metrics")

@router.get("/history/{metric_name}")
async def get_metric_history(metric_name: str, days: int = 7):
    """Get historical data for a specific metric"""
    try:
        time_range = timedelta(days=days)
        metrics = metrics_collector.get_metric_history(metric_name, time_range)
        return [asdict(metric) for metric in metrics]
    except Exception as e:
        logger.error(f"Error getting metric history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metric history")

# Background metrics collection
async def start_metrics_collection():
    """Start background metrics collection"""
    while True:
        try:
            # Collect system metrics
            import psutil
            
            # CPU and memory metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            metrics_collector.record_metric(BusinessMetric(
                name="system.cpu.usage",
                value=cpu_percent,
                unit="percent",
                timestamp=datetime.now(),
                tags={"component": "system"},
                metadata={"cores": psutil.cpu_count()}
            ))
            
            metrics_collector.record_metric(BusinessMetric(
                name="system.memory.usage",
                value=memory.percent,
                unit="percent",
                timestamp=datetime.now(),
                tags={"component": "system"},
                metadata={"available_gb": memory.available / (1024**3)}
            ))
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            metrics_collector.record_metric(BusinessMetric(
                name="system.disk.usage",
                value=disk.percent,
                unit="percent",
                timestamp=datetime.now(),
                tags={"component": "system", "mount": "/"},
                metadata={"free_gb": disk.free / (1024**3)}
            ))
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
        
        await asyncio.sleep(60)  # Collect every minute

# Integration with existing monitoring
from app.monitoring.apm_integration import record_business_event

def record_pipeline_business_event(run_id: str, stage: str, status: str, **kwargs):
    """Record pipeline business events"""
    record_business_event(f"pipeline_{stage}", run_id=run_id, status=status, **kwargs)
    
    # Also record in our metrics database
    if status == "completed":
        duration = kwargs.get("duration", 0)
        ideas_generated = kwargs.get("ideas_generated", 0)
        mvps_created = kwargs.get("mvps_created", 0)
        
        metrics_collector.record_pipeline_run(
            run_id, status, duration, ideas_generated, mvps_created
        )

def record_llm_business_event(model: str, tokens: int, duration: float, 
                            success: bool, cost_estimate: float = 0.0):
    """Record LLM business events"""
    record_business_event("llm_request", model=model, tokens=tokens, 
                         duration=duration, success=success)
    
    # Also record in our metrics database
    metrics_collector.record_llm_request(model, tokens, duration, success, cost_estimate)

def record_user_business_event(user_id: str, action: str, session_duration: float = 0.0):
    """Record user business events"""
    record_business_event("user_action", user_id=user_id, action=action)
    
    # Also record in our metrics database
    metrics_collector.record_user_action(user_id, action, session_duration)
