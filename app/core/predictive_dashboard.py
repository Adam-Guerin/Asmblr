"""
Predictive Dashboard for Asmblr
AI-powered dashboard with real-time predictions and insights
"""

import asyncio
from typing import Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from loguru import logger
import redis.asyncio as redis

from app.core.predictive_monitoring import predictive_monitoring, MetricType
from app.core.adaptive_learning import adaptive_learning_engine, ModelType

class DashboardType(Enum):
    """Dashboard types"""
    OVERVIEW = "overview"
    PERFORMANCE = "performance"
    PREDICTIONS = "predictions"
    ALERTS = "alerts"
    LEARNING = "learning"
    RESOURCES = "resources"

class TimeRange(Enum):
    """Time ranges for dashboard data"""
    LAST_HOUR = "last_hour"
    LAST_6_HOURS = "last_6_hours"
    LAST_24_HOURS = "last_24_hours"
    LAST_WEEK = "last_week"
    LAST_MONTH = "last_month"

@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    refresh_interval: int = 30  # seconds
    max_data_points: int = 1000
    enable_predictions: bool = True
    enable_alerts: bool = True
    enable_learning: bool = True
    theme: str = "dark"

class PredictiveDashboard:
    """AI-powered predictive dashboard"""
    
    def __init__(self, config: DashboardConfig = None):
        self.config = config or DashboardConfig()
        self.app = FastAPI(title="Asmblr Predictive Dashboard")
        self.templates = Jinja2Templates(directory="templates")
        
        # WebSocket connections
        self.active_connections: list[WebSocket] = []
        
        # Redis for real-time data
        self.redis_client = None
        self.redis_enabled = False
        
        # Dashboard data cache
        self.dashboard_cache = {}
        self.cache_ttl = 30  # seconds
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup dashboard routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_overview():
            """Main dashboard overview"""
            return await self._render_dashboard(DashboardType.OVERVIEW)
        
        @self.app.get("/performance", response_class=HTMLResponse)
        async def performance_dashboard():
            """Performance dashboard"""
            return await self._render_dashboard(DashboardType.PERFORMANCE)
        
        @self.app.get("/predictions", response_class=HTMLResponse)
        async def predictions_dashboard():
            """Predictions dashboard"""
            return await self._render_dashboard(DashboardType.PREDICTIONS)
        
        @self.app.get("/alerts", response_class=HTMLResponse)
        async def alerts_dashboard():
            """Alerts dashboard"""
            return await self._render_dashboard(DashboardType.ALERTS)
        
        @self.app.get("/learning", response_class=HTMLResponse)
        async def learning_dashboard():
            """Learning dashboard"""
            return await self._render_dashboard(DashboardType.LEARNING)
        
        @self.app.get("/resources", response_class=HTMLResponse)
        async def resources_dashboard():
            """Resources dashboard"""
            return await self._render_dashboard(DashboardType.RESOURCES)
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await self._handle_websocket(websocket)
        
        @self.app.get("/api/dashboard/{dashboard_type}")
        async def get_dashboard_data(dashboard_type: str, time_range: str = TimeRange.LAST_24_HOURS.value):
            """Get dashboard data via API"""
            try:
                dashboard_enum = DashboardType(dashboard_type)
                time_range_enum = TimeRange(time_range)
                data = await self._get_dashboard_data(dashboard_enum, time_range_enum)
                return data
            except ValueError:
                return {"error": "Invalid dashboard type or time range"}
        
        @self.app.get("/api/metrics")
        async def get_metrics_data(time_range: str = TimeRange.LAST_24_HOURS.value):
            """Get metrics data"""
            try:
                time_range_enum = TimeRange(time_range)
                return await self._get_metrics_data(time_range_enum)
            except ValueError:
                return {"error": "Invalid time range"}
        
        @self.app.get("/api/predictions")
        async def get_predictions_data(time_range: str = TimeRange.LAST_24_HOURS.value):
            """Get predictions data"""
            try:
                time_range_enum = TimeRange(time_range)
                return await self._get_predictions_data(time_range_enum)
            except ValueError:
                return {"error": "Invalid time range"}
        
        @self.app.get("/api/alerts")
        async def get_alerts_data():
            """Get alerts data"""
            return await self._get_alerts_data()
        
        @self.app.get("/api/learning")
        async def get_learning_data():
            """Get learning insights data"""
            return await self._get_learning_data()
        
        @self.app.post("/api/alerts/{alert_id}/acknowledge")
        async def acknowledge_alert(alert_id: str):
            """Acknowledge an alert"""
            success = await predictive_monitoring.acknowledge_alert(alert_id)
            return {"success": success}
        
        @self.app.post("/api/alerts/{alert_id}/resolve")
        async def resolve_alert(alert_id: str):
            """Resolve an alert"""
            success = await predictive_monitoring.resolve_alert(alert_id)
            return {"success": success}
    
    async def initialize(self):
        """Initialize the dashboard"""
        try:
            # Initialize Redis connection
            try:
                self.redis_client = redis.from_url(
                    "redis://localhost:6379/8",
                    max_connections=20
                )
                await self.redis_client.ping()
                self.redis_enabled = True
                logger.info("Redis connection established for dashboard")
            except Exception as e:
                logger.warning(f"Redis not available, using local dashboard: {e}")
            
            # Start background tasks
            await self._start_background_tasks()
            
            logger.info("Predictive dashboard initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize dashboard: {e}")
            raise
    
    async def _render_dashboard(self, dashboard_type: DashboardType) -> str:
        """Render dashboard HTML"""
        try:
            template_name = f"dashboard_{dashboard_type.value}.html"
            
            # Get dashboard data
            data = await self._get_dashboard_data(dashboard_type, TimeRange.LAST_24_HOURS)
            
            # Render template
            return self.templates.TemplateResponse(
                template_name,
                {
                    "request": {},  # FastAPI request object
                    "dashboard_type": dashboard_type.value,
                    "config": asdict(self.config),
                    "data": data
                }
            )
            
        except Exception as e:
            logger.error(f"Dashboard rendering error: {e}")
            return f"<h1>Error rendering dashboard: {e}</h1>"
    
    async def _get_dashboard_data(self, dashboard_type: DashboardType, time_range: TimeRange) -> dict[str, Any]:
        """Get dashboard data"""
        try:
            cache_key = f"dashboard_{dashboard_type.value}_{time_range.value}"
            
            # Check cache
            if cache_key in self.dashboard_cache:
                cache_entry = self.dashboard_cache[cache_key]
                if (datetime.now() - cache_entry['timestamp']).total_seconds() < self.cache_ttl:
                    return cache_entry['data']
            
            # Generate data based on dashboard type
            if dashboard_type == DashboardType.OVERVIEW:
                data = await self._get_overview_data(time_range)
            elif dashboard_type == DashboardType.PERFORMANCE:
                data = await self._get_performance_data(time_range)
            elif dashboard_type == DashboardType.PREDICTIONS:
                data = await self._get_predictions_dashboard_data(time_range)
            elif dashboard_type == DashboardType.ALERTS:
                data = await self._get_alerts_dashboard_data()
            elif dashboard_type == DashboardType.LEARNING:
                data = await self._get_learning_dashboard_data()
            elif dashboard_type == DashboardType.RESOURCES:
                data = await self._get_resources_data(time_range)
            else:
                data = {}
            
            # Cache data
            self.dashboard_cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now()
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Dashboard data error for {dashboard_type.value}: {e}")
            return {"error": str(e)}
    
    async def _get_overview_data(self, time_range: TimeRange) -> dict[str, Any]:
        """Get overview dashboard data"""
        try:
            # Get metrics summary
            metrics_summary = await predictive_monitoring.get_metrics_summary()
            
            # Get predictions summary
            predictions_summary = await predictive_monitoring.get_predictions_summary()
            
            # Get alerts summary
            alerts_summary = await predictive_monitoring.get_alerts_summary()
            
            # Get learning insights
            learning_insights = await adaptive_learning_engine.get_learning_insights()
            
            # System health score
            health_score = self._calculate_health_score(metrics_summary, alerts_summary)
            
            return {
                'health_score': health_score,
                'metrics': metrics_summary,
                'predictions': predictions_summary,
                'alerts': alerts_summary,
                'learning': learning_insights,
                'timestamp': datetime.now().isoformat(),
                'time_range': time_range.value
            }
            
        except Exception as e:
            logger.error(f"Overview data error: {e}")
            return {}
    
    async def _get_performance_data(self, time_range: TimeRange) -> dict[str, Any]:
        """Get performance dashboard data"""
        try:
            # Get detailed metrics for each type
            performance_data = {}
            
            for metric_type in MetricType:
                data_points = list(predictive_monitoring.metrics_data[metric_type])
                
                if data_points:
                    # Filter by time range
                    cutoff_time = self._get_cutoff_time(time_range)
                    filtered_data = [dp for dp in data_points if dp.timestamp > cutoff_time]
                    
                    if filtered_data:
                        values = [dp.value for dp in filtered_data]
                        timestamps = [dp.timestamp.isoformat() for dp in filtered_data]
                        
                        performance_data[metric_type.value] = {
                            'values': values,
                            'timestamps': timestamps,
                            'current': values[-1],
                            'min': min(values),
                            'max': max(values),
                            'avg': sum(values) / len(values),
                            'trend': self._calculate_trend(values)
                        }
            
            return {
                'performance': performance_data,
                'timestamp': datetime.now().isoformat(),
                'time_range': time_range.value
            }
            
        except Exception as e:
            logger.error(f"Performance data error: {e}")
            return {}
    
    async def _get_predictions_dashboard_data(self, time_range: TimeRange) -> dict[str, Any]:
        """Get predictions dashboard data"""
        try:
            predictions_data = {}
            
            for metric_type in MetricType:
                predictions = list(predictive_monitoring.predictions[metric_type])
                
                if predictions:
                    # Filter by time range
                    cutoff_time = self._get_cutoff_time(time_range)
                    filtered_predictions = [p for p in predictions if p.timestamp > cutoff_time]
                    
                    if filtered_predictions:
                        predictions_data[metric_type.value] = {
                            'predictions': [p.to_dict() for p in filtered_predictions],
                            'latest': filtered_predictions[-1].to_dict(),
                            'accuracy': self._calculate_prediction_accuracy(filtered_predictions)
                        }
            
            return {
                'predictions': predictions_data,
                'timestamp': datetime.now().isoformat(),
                'time_range': time_range.value
            }
            
        except Exception as e:
            logger.error(f"Predictions dashboard data error: {e}")
            return {}
    
    async def _get_alerts_dashboard_data(self) -> dict[str, Any]:
        """Get alerts dashboard data"""
        try:
            alerts_summary = await predictive_monitoring.get_alerts_summary()
            
            # Get detailed alerts
            alerts = list(predictive_monitoring.alerts.values())
            alerts.sort(key=lambda a: a.timestamp, reverse=True)
            
            detailed_alerts = [alert.to_dict() for alert in alerts[:50]]  # Last 50 alerts
            
            return {
                'summary': alerts_summary,
                'alerts': detailed_alerts,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Alerts dashboard data error: {e}")
            return {}
    
    async def _get_learning_dashboard_data(self) -> dict[str, Any]:
        """Get learning dashboard data"""
        try:
            learning_insights = await adaptive_learning_engine.get_learning_insights()
            
            # Get model-specific data
            model_data = {}
            for model_type in ModelType:
                if model_type in adaptive_learning_engine.model_metrics:
                    metrics = adaptive_learning_engine.model_metrics[model_type]
                    feature_importance = await adaptive_learning_engine.get_feature_importance(model_type)
                    
                    model_data[model_type.value] = {
                        'metrics': asdict(metrics),
                        'feature_importance': feature_importance,
                        'data_samples': len(adaptive_learning_engine.learning_data[model_type])
                    }
            
            return {
                'insights': learning_insights,
                'models': model_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Learning dashboard data error: {e}")
            return {}
    
    async def _get_resources_data(self, time_range: TimeRange) -> dict[str, Any]:
        """Get resources dashboard data"""
        try:
            # Get resource metrics
            resource_metrics = {
                'cpu': [],
                'memory': [],
                'disk': [],
                'network': []
            }
            
            # Filter by time range
            cutoff_time = self._get_cutoff_time(time_range)
            
            for metric_type in [MetricType.CPU_USAGE, MetricType.MEMORY_USAGE, MetricType.DISK_USAGE, MetricType.NETWORK_IO]:
                data_points = list(predictive_monitoring.metrics_data[metric_type])
                filtered_data = [dp for dp in data_points if dp.timestamp > cutoff_time]
                
                if filtered_data:
                    values = [dp.value for dp in filtered_data]
                    timestamps = [dp.timestamp.isoformat() for dp in filtered_data]
                    
                    resource_metrics[metric_type.value] = {
                        'values': values,
                        'timestamps': timestamps,
                        'current': values[-1],
                        'avg': sum(values) / len(values),
                        'peak': max(values)
                    }
            
            return {
                'resources': resource_metrics,
                'timestamp': datetime.now().isoformat(),
                'time_range': time_range.value
            }
            
        except Exception as e:
            logger.error(f"Resources data error: {e}")
            return {}
    
    def _get_cutoff_time(self, time_range: TimeRange) -> datetime:
        """Get cutoff time for time range"""
        now = datetime.now()
        
        if time_range == TimeRange.LAST_HOUR:
            return now - timedelta(hours=1)
        elif time_range == TimeRange.LAST_6_HOURS:
            return now - timedelta(hours=6)
        elif time_range == TimeRange.LAST_24_HOURS:
            return now - timedelta(hours=24)
        elif time_range == TimeRange.LAST_WEEK:
            return now - timedelta(days=7)
        elif time_range == TimeRange.LAST_MONTH:
            return now - timedelta(days=30)
        
        return now - timedelta(hours=24)
    
    def _calculate_health_score(self, metrics: dict, alerts: dict) -> float:
        """Calculate system health score"""
        try:
            health_score = 100.0
            
            # Deduct points for active alerts
            active_alerts = alerts.get('active_alerts', 0)
            critical_alerts = alerts.get('critical_alerts', 0)
            
            health_score -= active_alerts * 2
            health_score -= critical_alerts * 10
            
            # Deduct points for high resource usage
            metrics_by_type = metrics.get('metrics_by_type', {})
            
            if 'cpu_usage' in metrics_by_type:
                cpu_current = metrics_by_type['cpu_usage'].get('current', 0)
                if cpu_current > 80:
                    health_score -= (cpu_current - 80) * 0.5
            
            if 'memory_usage' in metrics_by_type:
                memory_current = metrics_by_type['memory_usage'].get('current', 0)
                if memory_current > 80:
                    health_score -= (memory_current - 80) * 0.5
            
            return max(0.0, min(100.0, health_score))
            
        except Exception as e:
            logger.error(f"Health score calculation error: {e}")
            return 75.0
    
    def _calculate_trend(self, values: list[float]) -> str:
        """Calculate trend from values"""
        try:
            if len(values) < 2:
                return "stable"
            
            # Simple linear trend calculation
            recent_values = values[-10:] if len(values) >= 10 else values
            n = len(recent_values)
            
            if n < 2:
                return "stable"
            
            # Calculate slope
            x = list(range(n))
            y = recent_values
            
            x_mean = sum(x) / n
            y_mean = sum(y) / n
            
            numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
            
            if denominator == 0:
                return "stable"
            
            slope = numerator / denominator
            
            # Determine trend
            if abs(slope) < 0.1:
                return "stable"
            elif slope > 0:
                return "increasing"
            else:
                return "decreasing"
            
        except Exception as e:
            logger.error(f"Trend calculation error: {e}")
            return "stable"
    
    def _calculate_prediction_accuracy(self, predictions: list) -> float:
        """Calculate prediction accuracy"""
        try:
            if len(predictions) < 5:
                return 0.0
            
            # Simple accuracy calculation based on confidence
            confidences = [p.confidence for p in predictions]
            return sum(confidences) / len(confidences)
            
        except Exception as e:
            logger.error(f"Prediction accuracy calculation error: {e}")
            return 0.0
    
    async def _handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connections"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        try:
            while True:
                # Send real-time updates
                await self._send_websocket_update(websocket)
                await asyncio.sleep(self.config.refresh_interval)
                
        except WebSocketDisconnect:
            self.active_connections.remove(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
    
    async def _send_websocket_update(self, websocket: WebSocket):
        """Send update via WebSocket"""
        try:
            # Get latest data
            overview_data = await self._get_overview_data(TimeRange.LAST_HOUR)
            alerts_data = await self._get_alerts_dashboard_data()
            
            update = {
                'type': 'dashboard_update',
                'timestamp': datetime.now().isoformat(),
                'overview': overview_data,
                'alerts': alerts_data
            }
            
            await websocket.send_json(update)
            
        except Exception as e:
            logger.error(f"WebSocket update error: {e}")
    
    async def _start_background_tasks(self):
        """Start background dashboard tasks"""
        asyncio.create_task(self._cache_cleanup_task())
        asyncio.create_task(self._websocket_broadcast_task())
        
        logger.info("Background dashboard tasks started")
    
    async def _cache_cleanup_task(self):
        """Background cache cleanup task"""
        while True:
            try:
                # Clean expired cache entries
                expired_keys = []
                for key, entry in self.dashboard_cache.items():
                    if (datetime.now() - entry['timestamp']).total_seconds() > self.cache_ttl * 2:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.dashboard_cache[key]
                
                await asyncio.sleep(60)  # Clean every minute
                
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(60)
    
    async def _websocket_broadcast_task(self):
        """Background WebSocket broadcast task"""
        while True:
            try:
                if self.active_connections:
                    # Broadcast to all connected clients
                    message = {
                        'type': 'ping',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    disconnected = []
                    for connection in self.active_connections:
                        try:
                            await connection.send_json(message)
                        except:
                            disconnected.append(connection)
                    
                    # Remove disconnected clients
                    for connection in disconnected:
                        self.active_connections.remove(connection)
                
                await asyncio.sleep(30)  # Ping every 30 seconds
                
            except Exception as e:
                logger.error(f"WebSocket broadcast error: {e}")
                await asyncio.sleep(30)
    
    async def run(self, host: str = "0.0.0.0", port: int = 8080):
        """Run the dashboard server"""
        try:
            config = uvicorn.Config(
                app=self.app,
                host=host,
                port=port,
                log_level="info"
            )
            
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            logger.error(f"Dashboard server error: {e}")
            raise

# Dashboard HTML Templates

DASHBOARD_OVERVIEW_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Asmblr Predictive Dashboard - Overview</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .health-excellent { background: linear-gradient(135deg, #10b981, #059669); }
        .health-good { background: linear-gradient(135deg, #3b82f6, #2563eb); }
        .health-warning { background: linear-gradient(135deg, #f59e0b, #d97706); }
        .health-critical { background: linear-gradient(135deg, #ef4444, #dc2626); }
    </style>
</head>
<body class="bg-gray-900 text-white">
    <div class="container mx-auto p-6">
        <header class="mb-8">
            <h1 class="text-4xl font-bold mb-2">Asmblr Predictive Dashboard</h1>
            <p class="text-gray-400">Real-time AI-powered monitoring and predictions</p>
        </header>
        
        <!-- Health Score -->
        <div class="mb-8">
            <div class="health-{{ 'excellent' if data.health_score > 80 else 'good' if data.health_score > 60 else 'warning' if data.health_score > 40 else 'critical' }} rounded-lg p-6 text-center">
                <h2 class="text-2xl font-bold mb-2">System Health Score</h2>
                <div class="text-6xl font-bold">{{ "%.1f"|format(data.health_score) }}%</div>
                <p class="mt-2">{{ 'Excellent' if data.health_score > 80 else 'Good' if data.health_score > 60 else 'Warning' if data.health_score > 40 else 'Critical' }}</p>
            </div>
        </div>
        
        <!-- Metrics Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-lg font-semibold mb-2">Total Metrics</h3>
                <div class="text-3xl font-bold text-blue-400">{{ data.metrics.total_metrics }}</div>
            </div>
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-lg font-semibold mb-2">Predictions</h3>
                <div class="text-3xl font-bold text-green-400">{{ data.predictions.total_predictions }}</div>
            </div>
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-lg font-semibold mb-2">Active Alerts</h3>
                <div class="text-3xl font-bold text-yellow-400">{{ data.alerts.active_alerts }}</div>
            </div>
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-lg font-semibold mb-2">Model Accuracy</h3>
                <div class="text-3xl font-bold text-purple-400">{{ "%.1f"|format(data.learning.global_metrics.avg_accuracy * 100) }}%</div>
            </div>
        </div>
        
        <!-- Charts -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-lg font-semibold mb-4">System Metrics</h3>
                <canvas id="metricsChart"></canvas>
            </div>
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-lg font-semibold mb-4">Recent Alerts</h3>
                <div id="alertsList" class="space-y-2">
                    {% for alert in data.alerts.recent_alerts[:5] %}
                    <div class="bg-gray-700 rounded p-3">
                        <div class="flex justify-between items-center">
                            <span class="font-medium">{{ alert.metric_type }}</span>
                            <span class="text-{{ 'red' if alert.severity == 'critical' else 'yellow' if alert.severity == 'warning' else 'blue' }}">
                                {{ alert.severity.upper() }}
                            </span>
                        </div>
                        <p class="text-sm text-gray-400 mt-1">{{ alert.message }}</p>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // WebSocket connection
        const ws = new WebSocket('ws://localhost:8080/ws');
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'dashboard_update') {
                updateDashboard(data);
            }
        };
        
        // Initialize charts
        const ctx = document.getElementById('metricsChart').getContext('2d');
        const metricsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU Usage',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                }, {
                    label: 'Memory Usage',
                    data: [],
                    borderColor: 'rgb(16, 185, 129)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
        
        function updateDashboard(data) {
            // Update health score
            const healthScore = data.overview.health_score;
            document.querySelector('.text-6xl').textContent = healthScore.toFixed(1) + '%';
            
            // Update metrics
            document.querySelector('.text-blue-400').textContent = data.overview.metrics.total_metrics;
            document.querySelector('.text-green-400').textContent = data.overview.predictions.total_predictions;
            document.querySelector('.text-yellow-400').textContent = data.overview.alerts.active_alerts;
            
            // Update chart (simplified)
            // In practice, you'd update with real data
        }
    </script>
</body>
</html>
"""

# Global dashboard instance
predictive_dashboard = PredictiveDashboard()
