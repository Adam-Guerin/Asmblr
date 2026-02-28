"""
Advanced Business Intelligence and Analytics for Asmblr
Real-time insights, predictive analytics, and business KPIs
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import uuid
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Metric types"""
    REVENUE = "revenue"
    USERS = "users"
    ENGAGEMENT = "engagement"
    PERFORMANCE = "performance"
    CONVERSION = "conversion"
    RETENTION = "retention"
    SATISFACTION = "satisfaction"

class InsightType(Enum):
    """Insight types"""
    TREND = "trend"
    ANOMALY = "anomaly"
    OPPORTUNITY = "opportunity"
    RISK = "risk"
    PREDICTION = "prediction"
    CORRELATION = "correlation"

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class BusinessMetric:
    """Business metric data"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    period: str  # daily, weekly, monthly
    category: MetricType
    dimensions: Dict[str, str]
    metadata: Dict[str, Any]

@dataclass
class Insight:
    """Business insight"""
    id: str
    type: InsightType
    title: str
    description: str
    confidence: float
    impact: str  # low, medium, high
    urgency: str  # low, medium, high
    data: Dict[str, Any]
    recommendations: List[str]
    created_at: datetime
    expires_at: Optional[datetime]

@dataclass
class Alert:
    """Business alert"""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    metric_name: str
    threshold_value: float
    current_value: float
    trend: str  # up, down, stable
    created_at: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

@dataclass
class Prediction:
    """Business prediction"""
    id: str
    metric_name: str
    prediction_type: str  # revenue, users, churn, etc.
    predicted_value: float
    confidence_interval: Tuple[float, float]
    confidence_score: float
    time_horizon: str  # 7d, 30d, 90d
    factors: List[Dict[str, Any]]
    created_at: datetime

class BusinessIntelligenceEngine:
    """Business intelligence and analytics engine"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.metrics_cache: Dict[str, List[BusinessMetric]] = {}
        self.insights: List[Insight] = []
        self.alerts: List[Alert] = []
        self.predictions: List[Prediction] = []
        
        # ML models
        self.revenue_model = None
        self.user_growth_model = None
        self.anomaly_detector = None
        self.scaler = StandardScaler()
        
        # KPI definitions
        self.kpi_definitions = self._initialize_kpi_definitions()
        
        # Alert thresholds
        self.alert_thresholds = self._initialize_alert_thresholds()
    
    async def initialize(self):
        """Initialize the BI engine"""
        self.redis_client = redis.from_url(self.redis_url)
        
        # Load historical data
        await self._load_historical_data()
        
        # Train ML models
        await self._train_models()
        
        # Start background tasks
        asyncio.create_task(self._continuous_analysis())
        asyncio.create_task(self._generate_predictions())
        
        logger.info("Business Intelligence Engine initialized")
    
    def _initialize_kpi_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize KPI definitions"""
        return {
            "revenue": {
                "name": "Monthly Recurring Revenue",
                "unit": "USD",
                "category": MetricType.REVENUE,
                "target_growth": 0.15,  # 15% monthly growth
                "description": "Total monthly recurring revenue from all subscriptions"
            },
            "active_users": {
                "name": "Active Users",
                "unit": "count",
                "category": MetricType.USERS,
                "target_growth": 0.10,  # 10% monthly growth
                "description": "Number of active users in the period"
            },
            "conversion_rate": {
                "name": "Conversion Rate",
                "unit": "percentage",
                "category": MetricType.CONVERSION,
                "target_value": 0.05,  # 5% conversion rate
                "description": "Percentage of visitors who convert to paying customers"
            },
            "churn_rate": {
                "name": "Customer Churn Rate",
                "unit": "percentage",
                "category": MetricType.RETENTION,
                "target_max": 0.05,  # Max 5% churn rate
                "description": "Percentage of customers who cancel subscription"
            },
            "user_satisfaction": {
                "name": "User Satisfaction Score",
                "unit": "score",
                "category": MetricType.SATISFACTION,
                "target_min": 4.0,  # Min 4.0 out of 5
                "description": "Average user satisfaction score from surveys"
            },
            "avg_session_duration": {
                "name": "Average Session Duration",
                "unit": "minutes",
                "category": MetricType.ENGAGEMENT,
                "target_min": 15,  # Min 15 minutes
                "description": "Average time users spend in the application"
            },
            "feature_adoption": {
                "name": "Feature Adoption Rate",
                "unit": "percentage",
                "category": MetricType.ENGAGEMENT,
                "target_min": 0.60,  # Min 60% adoption
                "description": "Percentage of users using key features"
            },
            "support_response_time": {
                "name": "Support Response Time",
                "unit": "hours",
                "category": MetricType.PERFORMANCE,
                "target_max": 2.0,  # Max 2 hours response time
                "description": "Average time to respond to support tickets"
            }
        }
    
    def _initialize_alert_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Initialize alert thresholds"""
        return {
            "revenue_decline": {
                "metric": "revenue",
                "condition": "decline",
                "threshold": 0.10,  # 10% decline
                "severity": AlertSeverity.HIGH,
                "message": "Revenue has declined by {value}%"
            },
            "high_churn": {
                "metric": "churn_rate",
                "condition": "exceed",
                "threshold": 0.08,  # 8% churn rate
                "severity": AlertSeverity.CRITICAL,
                "message": "Churn rate is {value}% - critical level"
            },
            "low_conversion": {
                "metric": "conversion_rate",
                "condition": "below",
                "threshold": 0.03,  # 3% conversion rate
                "severity": AlertSeverity.MEDIUM,
                "message": "Conversion rate is {value}% - below target"
            },
            "poor_satisfaction": {
                "metric": "user_satisfaction",
                "condition": "below",
                "threshold": 3.5,  # 3.5 satisfaction score
                "severity": AlertSeverity.MEDIUM,
                "message": "User satisfaction is {value} - needs attention"
            },
            "slow_support": {
                "metric": "support_response_time",
                "condition": "exceed",
                "threshold": 4.0,  # 4 hours response time
                "severity": AlertSeverity.LOW,
                "message": "Support response time is {value} hours"
            }
        }
    
    async def _load_historical_data(self):
        """Load historical data from Redis"""
        try:
            # Load metrics for the last 90 days
            for metric_name in self.kpi_definitions.keys():
                metric_data = await self.redis_client.lrange(f"metrics:{metric_name}", 0, -1)
                
                metrics = []
                for data in metric_data:
                    metric_dict = json.loads(data)
                    metric = BusinessMetric(
                        name=metric_dict["name"],
                        value=metric_dict["value"],
                        unit=metric_dict["unit"],
                        timestamp=datetime.fromisoformat(metric_dict["timestamp"]),
                        period=metric_dict["period"],
                        category=MetricType(metric_dict["category"]),
                        dimensions=metric_dict["dimensions"],
                        metadata=metric_dict["metadata"]
                    )
                    metrics.append(metric)
                
                self.metrics_cache[metric_name] = metrics
            
            logger.info(f"Loaded historical data for {len(self.metrics_cache)} metrics")
            
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
    
    async def _train_models(self):
        """Train ML models for predictions"""
        try:
            # Prepare training data
            revenue_data = self._prepare_training_data("revenue")
            user_data = self._prepare_training_data("active_users")
            
            if len(revenue_data) > 30:  # Need at least 30 data points
                # Train revenue prediction model
                X_revenue, y_revenue = self._create_features(revenue_data)
                self.revenue_model = RandomForestRegressor(n_estimators=100, random_state=42)
                self.revenue_model.fit(X_revenue, y_revenue)
                
                # Train user growth model
                X_users, y_users = self._create_features(user_data)
                self.user_growth_model = RandomForestRegressor(n_estimators=100, random_state=42)
                self.user_growth_model.fit(X_users, y_users)
                
                # Train anomaly detector
                all_metrics = []
                for metrics in self.metrics_cache.values():
                    all_metrics.extend([m.value for m in metrics])
                
                if len(all_metrics) > 50:
                    self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
                    self.anomaly_detector.fit(np.array(all_metrics).reshape(-1, 1))
            
            logger.info("ML models trained successfully")
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
    
    def _prepare_training_data(self, metric_name: str) -> List[BusinessMetric]:
        """Prepare training data for a metric"""
        metrics = self.metrics_cache.get(metric_name, [])
        return sorted(metrics, key=lambda m: m.timestamp)
    
    def _create_features(self, metrics: List[BusinessMetric]) -> Tuple[np.ndarray, np.ndarray]:
        """Create features for ML models"""
        if len(metrics) < 2:
            return np.array([]), np.array([])
        
        # Create time-based features
        features = []
        targets = []
        
        for i in range(1, len(metrics)):
            current_metric = metrics[i]
            previous_metric = metrics[i-1]
            
            # Features
            feature_vector = [
                current_metric.timestamp.day,
                current_metric.timestamp.month,
                current_metric.timestamp.weekday(),
                previous_metric.value,
                # Moving averages
                np.mean([m.value for m in metrics[max(0, i-7):i]]),
                np.mean([m.value for m in metrics[max(0, i-30):i]]),
                # Growth rates
                (current_metric.value - previous_metric.value) / max(previous_metric.value, 1)
            ]
            
            features.append(feature_vector)
            targets.append(current_metric.value)
        
        return np.array(features), np.array(targets)
    
    async def record_metric(self, metric: BusinessMetric):
        """Record a business metric"""
        try:
            # Store in Redis
            metric_data = {
                "name": metric.name,
                "value": metric.value,
                "unit": metric.unit,
                "timestamp": metric.timestamp.isoformat(),
                "period": metric.period,
                "category": metric.category.value,
                "dimensions": metric.dimensions,
                "metadata": metric.metadata
            }
            
            await self.redis_client.lpush(f"metrics:{metric.name}", json.dumps(metric_data))
            await self.redis_client.ltrim(f"metrics:{metric.name}", 0, 999)  # Keep last 1000 records
            
            # Update cache
            if metric.name not in self.metrics_cache:
                self.metrics_cache[metric.name] = []
            self.metrics_cache[metric.name].append(metric)
            
            # Keep only last 100 in cache
            if len(self.metrics_cache[metric.name]) > 100:
                self.metrics_cache[metric.name] = self.metrics_cache[metric.name][-100:]
            
            # Check for alerts
            await self._check_alerts(metric)
            
        except Exception as e:
            logger.error(f"Error recording metric: {e}")
    
    async def _check_alerts(self, metric: BusinessMetric):
        """Check if metric triggers any alerts"""
        try:
            # Get recent metrics for trend analysis
            recent_metrics = self.metrics_cache.get(metric.name, [])[-10:]
            
            if len(recent_metrics) < 2:
                return
            
            # Calculate trend
            previous_value = recent_metrics[-2].value
            current_value = metric.value
            trend = (current_value - previous_value) / max(previous_value, 1)
            
            # Check against thresholds
            for alert_name, alert_config in self.alert_thresholds.items():
                if alert_config["metric"] != metric.name:
                    continue
                
                triggered = False
                trigger_value = 0
                
                if alert_config["condition"] == "decline" and trend < -alert_config["threshold"]:
                    triggered = True
                    trigger_value = abs(trend) * 100
                elif alert_config["condition"] == "exceed" and current_value > alert_config["threshold"]:
                    triggered = True
                    trigger_value = current_value
                elif alert_config["condition"] == "below" and current_value < alert_config["threshold"]:
                    triggered = True
                    trigger_value = current_value
                
                if triggered:
                    alert = Alert(
                        id=str(uuid.uuid4()),
                        title=f"{alert_config['metric'].title()} Alert",
                        description=alert_config["message"].format(value=trigger_value),
                        severity=alert_config["severity"],
                        metric_name=metric.name,
                        threshold_value=alert_config["threshold"],
                        current_value=current_value,
                        trend="down" if trend < 0 else "up" if trend > 0 else "stable",
                        created_at=datetime.now()
                    )
                    
                    self.alerts.append(alert)
                    
                    # Keep only last 100 alerts
                    if len(self.alerts) > 100:
                        self.alerts = self.alerts[-100:]
                    
                    logger.warning(f"Alert triggered: {alert.title}")
        
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    async def _continuous_analysis(self):
        """Continuous background analysis"""
        while True:
            try:
                # Analyze trends
                await self._analyze_trends()
                
                # Detect anomalies
                await self._detect_anomalies()
                
                # Generate insights
                await self._generate_insights()
                
                # Clean up old data
                await self._cleanup_old_data()
                
                # Wait for next analysis (every hour)
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in continuous analysis: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _analyze_trends(self):
        """Analyze metric trends"""
        try:
            for metric_name, metrics in self.metrics_cache.items():
                if len(metrics) < 7:  # Need at least 7 data points for trend analysis
                    continue
                
                # Calculate trend over last 7 days
                recent_metrics = metrics[-7:]
                values = [m.value for m in recent_metrics]
                
                # Simple linear regression for trend
                x = np.arange(len(values))
                slope, intercept = np.polyfit(x, values, 1)
                
                # Determine trend direction
                if abs(slope) < 0.01:
                    trend_direction = "stable"
                elif slope > 0:
                    trend_direction = "increasing"
                else:
                    trend_direction = "decreasing"
                
                # Create insight if significant trend
                if abs(slope) > 0.05:  # Significant trend
                    insight = Insight(
                        id=str(uuid.uuid4()),
                        type=InsightType.TREND,
                        title=f"{metric_name.title()} Trend Analysis",
                        description=f"{metric_name} is showing a {trend_direction} trend over the last week",
                        confidence=min(abs(slope) * 10, 1.0),
                        impact="high" if abs(slope) > 0.1 else "medium",
                        urgency="high" if trend_direction == "decreasing" else "medium",
                        data={
                            "metric": metric_name,
                            "trend": trend_direction,
                            "slope": slope,
                            "values": values
                        },
                        recommendations=self._get_trend_recommendations(metric_name, trend_direction, slope),
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(days=7)
                    )
                    
                    self.insights.append(insight)
                    
                    # Keep only last 50 insights
                    if len(self.insights) > 50:
                        self.insights = self.insights[-50:]
        
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
    
    def _get_trend_recommendations(self, metric_name: str, trend_direction: str, slope: float) -> List[str]:
        """Get recommendations based on trend analysis"""
        recommendations = []
        
        if metric_name == "revenue":
            if trend_direction == "decreasing":
                recommendations = [
                    "Review pricing strategy and market positioning",
                    "Analyze customer churn and retention",
                    "Increase marketing and sales efforts",
                    "Consider product improvements or new features"
                ]
            elif trend_direction == "increasing":
                recommendations = [
                    "Scale marketing efforts to maintain growth",
                    "Invest in customer success to reduce churn",
                    "Expand product offerings to capture more value",
                    "Optimize operations for efficiency"
                ]
        
        elif metric_name == "active_users":
            if trend_direction == "decreasing":
                recommendations = [
                    "Analyze user engagement and drop-off points",
                    "Improve onboarding experience",
                    "Run re-engagement campaigns",
                    "Gather user feedback for improvements"
                ]
            elif trend_direction == "increasing":
                recommendations = [
                    "Ensure infrastructure can handle growth",
                    "Focus on user experience and support",
                    "Expand to new markets or segments",
                    "Develop community and engagement features"
                ]
        
        elif metric_name == "churn_rate":
            if trend_direction == "increasing":
                recommendations = [
                    "Identify reasons for customer departure",
                    "Improve product value and features",
                    "Enhance customer support and success",
                    "Review pricing and packaging"
                ]
        
        return recommendations
    
    async def _detect_anomalies(self):
        """Detect anomalies in metrics"""
        try:
            if not self.anomaly_detector:
                return
            
            for metric_name, metrics in self.metrics_cache.items():
                if len(metrics) < 10:
                    continue
                
                values = np.array([m.value for m in metrics]).reshape(-1, 1)
                
                # Detect anomalies
                predictions = self.anomaly_detector.predict(values)
                anomaly_indices = np.where(predictions == -1)[0]
                
                if len(anomaly_indices) > 0:
                    latest_anomaly = metrics[anomaly_indices[-1]]
                    
                    insight = Insight(
                        id=str(uuid.uuid4()),
                        type=InsightType.ANOMALY,
                        title=f"Anomaly Detected in {metric_name}",
                        description=f"Unusual pattern detected in {metric_name}: {latest_anomaly.value} {latest_anomaly.unit}",
                        confidence=0.8,
                        impact="medium",
                        urgency="medium",
                        data={
                            "metric": metric_name,
                            "anomaly_value": latest_anomaly.value,
                            "anomaly_time": latest_anomaly.timestamp.isoformat(),
                            "anomaly_indices": anomaly_indices.tolist()
                        },
                        recommendations=[
                            "Investigate the cause of this anomaly",
                            "Check for data quality issues",
                            "Review recent changes or events",
                            "Monitor for similar patterns"
                        ],
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(days=3)
                    )
                    
                    self.insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
    
    async def _generate_insights(self):
        """Generate business insights"""
        try:
            # Correlation analysis
            await self._analyze_correlations()
            
            # Opportunity detection
            await self._detect_opportunities()
            
            # Risk assessment
            await self._assess_risks()
        
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
    
    async def _analyze_correlations(self):
        """Analyze correlations between metrics"""
        try:
            # Get metrics with sufficient data
            metric_names = [name for name, metrics in self.metrics_cache.items() if len(metrics) >= 30]
            
            if len(metric_names) < 2:
                return
            
            # Create correlation matrix
            correlations = {}
            for i, metric1 in enumerate(metric_names):
                for j, metric2 in enumerate(metric_names[i+1:], i+1):
                    values1 = [m.value for m in self.metrics_cache[metric1][-30:]]
                    values2 = [m.value for m in self.metrics_cache[metric2][-30:]]
                    
                    correlation = np.corrcoef(values1, values2)[0, 1]
                    
                    if abs(correlation) > 0.7:  # Strong correlation
                        correlations[f"{metric1}_vs_{metric2}"] = correlation
                        
                        # Create insight
                        insight_type = InsightType.CORRELATION
                        if correlation > 0:
                            description = f"Strong positive correlation between {metric1} and {metric2}"
                        else:
                            description = f"Strong negative correlation between {metric1} and {metric2}"
                        
                        insight = Insight(
                            id=str(uuid.uuid4()),
                            type=insight_type,
                            title=f"Correlation Analysis: {metric1} vs {metric2}",
                            description=description,
                            confidence=abs(correlation),
                            impact="medium",
                            urgency="low",
                            data={
                                "metric1": metric1,
                                "metric2": metric2,
                                "correlation": correlation,
                                "values1": values1[-10:],
                                "values2": values2[-10:]
                            },
                            recommendations=[
                                f"Monitor {metric1} and {metric2} together",
                                "Investigate causal relationship",
                                "Use correlation for predictive modeling"
                            ],
                            created_at=datetime.now(),
                            expires_at=datetime.now() + timedelta(days=14)
                        )
                        
                        self.insights.append(insight)
            
            # Keep only last 50 insights
            if len(self.insights) > 50:
                self.insights = self.insights[-50:]
        
        except Exception as e:
            logger.error(f"Error analyzing correlations: {e}")
    
    async def _detect_opportunities(self):
        """Detect business opportunities"""
        try:
            # High-performing segments
            for metric_name, metrics in self.metrics_cache.items():
                if len(metrics) < 7:
                    continue
                
                # Look for segments with high performance
                dimensions = {}
                for metric in metrics[-7:]:
                    for key, value in metric.dimensions.items():
                        if key not in dimensions:
                            dimensions[key] = {}
                        if value not in dimensions[key]:
                            dimensions[key][value] = []
                        dimensions[key][value].append(metric.value)
                
                # Find best performing segments
                for dim_name, segments in dimensions.items():
                    if len(segments) < 2:
                        continue
                    
                    segment_performance = {}
                    for segment, values in segments.items():
                        if len(values) >= 3:
                            segment_performance[segment] = np.mean(values)
                    
                    if segment_performance:
                        best_segment = max(segment_performance.items(), key=lambda x: x[1])
                        worst_segment = min(segment_performance.items(), key=lambda x: x[1])
                        
                        # Create opportunity insight
                        if best_segment[1] > worst_segment[1] * 1.5:  # 50% better performance
                            insight = Insight(
                                id=str(uuid.uuid4()),
                                type=InsightType.OPPORTUNITY,
                                title=f"Opportunity: {dim_name} Segment Analysis",
                                description=f"{best_segment[0]} segment performs {best_segment[1]/worst_segment[1]:.1f}x better than {worst_segment[0]}",
                                confidence=0.7,
                                impact="high",
                                urgency="medium",
                                data={
                                    "dimension": dim_name,
                                    "best_segment": best_segment,
                                    "worst_segment": worst_segment,
                                    "performance_ratio": best_segment[1] / worst_segment[1]
                                },
                                recommendations=[
                                    f"Invest more in {best_segment[0]} segment",
                                    f"Analyze why {best_segment[0]} performs better",
                                    f"Apply learnings to {worst_segment[0]} segment",
                                    f"Consider segment-specific strategies"
                                ],
                                created_at=datetime.now(),
                                expires_at=datetime.now() + timedelta(days=30)
                            )
                            
                            self.insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error detecting opportunities: {e}")
    
    async def _assess_risks(self):
        """Assess business risks"""
        try:
            # Check for declining metrics
            for metric_name, metrics in self.metrics_cache.items():
                if len(metrics) < 14:  # Need 2 weeks of data
                    continue
                
                recent_metrics = metrics[-14:]
                values = [m.value for m in recent_metrics]
                
                # Calculate week-over-week change
                week1_avg = np.mean(values[:7])
                week2_avg = np.mean(values[7:])
                
                decline_rate = (week1_avg - week2_avg) / max(week1_avg, 1)
                
                if decline_rate > 0.2:  # 20% decline
                    insight = Insight(
                        id=str(uuid.uuid4()),
                        type=InsightType.RISK,
                        title=f"Risk Alert: {metric_name} Decline",
                        description=f"{metric_name} declined by {decline_rate*100:.1f}% week-over-week",
                        confidence=0.8,
                        impact="high",
                        urgency="high",
                        data={
                            "metric": metric_name,
                            "decline_rate": decline_rate,
                            "week1_avg": week1_avg,
                            "week2_avg": week2_avg
                        },
                        recommendations=[
                            "Investigate immediate cause of decline",
                            "Implement corrective actions",
                            "Monitor closely for next week",
                            "Communicate with stakeholders"
                        ],
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(days=7)
                    )
                    
                    self.insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error assessing risks: {e}")
    
    async def _generate_predictions(self):
        """Generate business predictions"""
        while True:
            try:
                # Generate revenue predictions
                await self._predict_revenue()
                
                # Generate user growth predictions
                await self._predict_user_growth()
                
                # Generate churn predictions
                await self._predict_churn()
                
                # Wait for next prediction (daily)
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"Error generating predictions: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    async def _predict_revenue(self):
        """Predict revenue for next periods"""
        try:
            if not self.revenue_model:
                return
            
            revenue_metrics = self.metrics_cache.get("revenue", [])
            if len(revenue_metrics) < 30:
                return
            
            # Create features for prediction
            X, _ = self._create_features(revenue_metrics)
            if len(X) == 0:
                return
            
            # Predict next 30 days
            last_features = X[-1]
            predictions = []
            
            for days_ahead in [7, 30, 90]:
                # Simple prediction using last features
                predicted_value = self.revenue_model.predict([last_features])[0]
                
                # Add some uncertainty for longer predictions
                uncertainty = 0.1 * (days_ahead / 30)
                confidence_interval = (
                    predicted_value * (1 - uncertainty),
                    predicted_value * (1 + uncertainty)
                )
                
                prediction = Prediction(
                    id=str(uuid.uuid4()),
                    metric_name="revenue",
                    prediction_type="revenue_forecast",
                    predicted_value=predicted_value,
                    confidence_interval=confidence_interval,
                    confidence_score=max(0.5, 1.0 - uncertainty),
                    time_horizon=f"{days_ahead}d",
                    factors=[
                        {"name": "Historical trend", "impact": 0.6},
                        {"name": "Seasonality", "impact": 0.2},
                        {"name": "Market conditions", "impact": 0.2}
                    ],
                    created_at=datetime.now()
                )
                
                predictions.append(prediction)
            
            self.predictions.extend(predictions)
            
            # Keep only last 20 predictions
            if len(self.predictions) > 20:
                self.predictions = self.predictions[-20:]
        
        except Exception as e:
            logger.error(f"Error predicting revenue: {e}")
    
    async def _predict_user_growth(self):
        """Predict user growth"""
        try:
            if not self.user_growth_model:
                return
            
            user_metrics = self.metrics_cache.get("active_users", [])
            if len(user_metrics) < 30:
                return
            
            # Similar to revenue prediction
            X, _ = self._create_features(user_metrics)
            if len(X) == 0:
                return
            
            last_features = X[-1]
            predicted_users = self.user_growth_model.predict([last_features])[0]
            
            prediction = Prediction(
                id=str(uuid.uuid4()),
                metric_name="active_users",
                prediction_type="user_growth_forecast",
                predicted_value=predicted_users,
                confidence_interval=(predicted_users * 0.9, predicted_users * 1.1),
                confidence_score=0.7,
                time_horizon="30d",
                factors=[
                    {"name": "Current growth rate", "impact": 0.5},
                    {"name": "Seasonal patterns", "impact": 0.3},
                    {"name": "Marketing spend", "impact": 0.2}
                ],
                created_at=datetime.now()
            )
            
            self.predictions.append(prediction)
        
        except Exception as e:
            logger.error(f"Error predicting user growth: {e}")
    
    async def _predict_churn(self):
        """Predict customer churn"""
        try:
            # Simple churn prediction based on recent trends
            churn_metrics = self.metrics_cache.get("churn_rate", [])
            if len(churn_metrics) < 14:
                return
            
            recent_churn = [m.value for m in churn_metrics[-14:]]
            churn_trend = np.polyfit(range(len(recent_churn)), recent_churn, 1)[0]
            
            if churn_trend > 0:  # Increasing churn
                predicted_churn = recent_churn[-1] + (churn_trend * 30)  # 30 days ahead
                
                prediction = Prediction(
                    id=str(uuid.uuid4()),
                    metric_name="churn_rate",
                    prediction_type="churn_forecast",
                    predicted_value=predicted_churn,
                    confidence_interval=(predicted_churn * 0.8, predicted_churn * 1.2),
                    confidence_score=0.6,
                    time_horizon="30d",
                    factors=[
                        {"name": "Current churn trend", "impact": 0.7},
                        {"name": "User satisfaction", "impact": 0.2},
                        {"name": "Product engagement", "impact": 0.1}
                    ],
                    created_at=datetime.now()
                )
                
                self.predictions.append(prediction)
        
        except Exception as e:
            logger.error(f"Error predicting churn: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old data"""
        try:
            # Remove old insights
            cutoff_time = datetime.now() - timedelta(days=30)
            self.insights = [i for i in self.insights if i.created_at > cutoff_time]
            
            # Remove old alerts
            self.alerts = [a for a in self.alerts if a.created_at > cutoff_time]
            
            # Remove old predictions
            self.predictions = [p for p in self.predictions if p.created_at > cutoff_time]
        
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data"""
        try:
            # Get current KPIs
            current_kpis = {}
            for metric_name, kpi_def in self.kpi_definitions.items():
                metrics = self.metrics_cache.get(metric_name, [])
                if metrics:
                    current_kpis[metric_name] = {
                        "current_value": metrics[-1].value,
                        "unit": metrics[-1].unit,
                        "previous_value": metrics[-2].value if len(metrics) > 1 else metrics[-1].value,
                        "trend": self._calculate_trend(metrics[-2:] if len(metrics) > 1 else [metrics[-1]]),
                        "target": kpi_def.get("target_value", kpi_def.get("target_growth", kpi_def.get("target_max", kpi_def.get("target_min")))),
                        "status": self._get_kpi_status(metric_name, metrics[-1].value, kpi_def)
                    }
            
            # Get recent insights
            recent_insights = [
                {
                    "id": insight.id,
                    "type": insight.type.value,
                    "title": insight.title,
                    "description": insight.description,
                    "confidence": insight.confidence,
                    "impact": insight.impact,
                    "urgency": insight.urgency,
                    "recommendations": insight.recommendations,
                    "created_at": insight.created_at.isoformat()
                }
                for insight in sorted(self.insights, key=lambda x: x.created_at, reverse=True)[:10]
            ]
            
            # Get active alerts
            active_alerts = [
                {
                    "id": alert.id,
                    "title": alert.title,
                    "description": alert.description,
                    "severity": alert.severity.value,
                    "metric_name": alert.metric_name,
                    "current_value": alert.current_value,
                    "trend": alert.trend,
                    "created_at": alert.created_at.isoformat()
                }
                for alert in sorted(self.alerts, key=lambda x: x.created_at, reverse=True)[:10]
                if not alert.acknowledged
            ]
            
            # Get predictions
            recent_predictions = [
                {
                    "id": pred.id,
                    "metric_name": pred.metric_name,
                    "prediction_type": pred.prediction_type,
                    "predicted_value": pred.predicted_value,
                    "confidence_interval": pred.confidence_interval,
                    "confidence_score": pred.confidence_score,
                    "time_horizon": pred.time_horizon,
                    "factors": pred.factors,
                    "created_at": pred.created_at.isoformat()
                }
                for pred in sorted(self.predictions, key=lambda x: x.created_at, reverse=True)[:5]
            ]
            
            return {
                "timestamp": datetime.now().isoformat(),
                "kpis": current_kpis,
                "insights": recent_insights,
                "alerts": active_alerts,
                "predictions": recent_predictions,
                "summary": {
                    "total_insights": len(self.insights),
                    "active_alerts": len([a for a in self.alerts if not a.acknowledged]),
                    "active_predictions": len(self.predictions),
                    "health_score": self._calculate_health_score()
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {"error": str(e)}
    
    def _calculate_trend(self, metrics: List[BusinessMetric]) -> str:
        """Calculate trend direction"""
        if len(metrics) < 2:
            return "stable"
        
        change = (metrics[-1].value - metrics[0].value) / max(metrics[0].value, 1)
        
        if abs(change) < 0.05:
            return "stable"
        elif change > 0:
            return "up"
        else:
            return "down"
    
    def _get_kpi_status(self, metric_name: str, current_value: float, kpi_def: Dict[str, Any]) -> str:
        """Get KPI status"""
        if "target_value" in kpi_def:
            target = kpi_def["target_value"]
            if current_value >= target * 0.9:
                return "good"
            elif current_value >= target * 0.7:
                return "warning"
            else:
                return "critical"
        elif "target_growth" in kpi_def:
            # For growth metrics, check if meeting growth target
            return "good"  # Simplified
        elif "target_max" in kpi_def:
            max_value = kpi_def["target_max"]
            if current_value <= max_value:
                return "good"
            elif current_value <= max_value * 1.2:
                return "warning"
            else:
                return "critical"
        elif "target_min" in kpi_def:
            min_value = kpi_def["target_min"]
            if current_value >= min_value:
                return "good"
            elif current_value >= min_value * 0.8:
                return "warning"
            else:
                return "critical"
        
        return "unknown"
    
    def _calculate_health_score(self) -> float:
        """Calculate overall business health score"""
        try:
            scores = []
            
            for metric_name, kpi_def in self.kpi_definitions.items():
                metrics = self.metrics_cache.get(metric_name, [])
                if not metrics:
                    continue
                
                current_value = metrics[-1].value
                status = self._get_kpi_status(metric_name, current_value, kpi_def)
                
                if status == "good":
                    scores.append(1.0)
                elif status == "warning":
                    scores.append(0.7)
                elif status == "critical":
                    scores.append(0.3)
                else:
                    scores.append(0.5)
            
            return np.mean(scores) if scores else 0.5
        
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 0.5

# Global BI engine
bi_engine = BusinessIntelligenceEngine()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/analytics", tags=["analytics"])

class MetricRequest(BaseModel):
    name: str
    value: float
    unit: str
    period: str = "daily"
    dimensions: Dict[str, str] = {}
    metadata: Dict[str, Any] = {}

@router.get("/dashboard")
async def get_dashboard():
    """Get analytics dashboard"""
    try:
        return await bi_engine.get_dashboard_data()
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metrics")
async def record_metric(request: MetricRequest):
    """Record a business metric"""
    try:
        metric = BusinessMetric(
            name=request.name,
            value=request.value,
            unit=request.unit,
            timestamp=datetime.now(),
            period=request.period,
            category=MetricType(request.name.split('_')[0]),  # Simple categorization
            dimensions=request.dimensions,
            metadata=request.metadata
        )
        
        await bi_engine.record_metric(metric)
        return {"status": "recorded"}
    except Exception as e:
        logger.error(f"Error recording metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights")
async def get_insights(limit: int = 20):
    """Get business insights"""
    try:
        insights = sorted(bi_engine.insights, key=lambda x: x.created_at, reverse=True)[:limit]
        return [
            {
                "id": insight.id,
                "type": insight.type.value,
                "title": insight.title,
                "description": insight.description,
                "confidence": insight.confidence,
                "impact": insight.impact,
                "urgency": insight.urgency,
                "recommendations": insight.recommendations,
                "created_at": insight.created_at.isoformat()
            }
            for insight in insights
        ]
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_alerts(active_only: bool = True):
    """Get business alerts"""
    try:
        alerts = bi_engine.alerts
        if active_only:
            alerts = [a for a in alerts if not a.acknowledged]
        
        return [
            {
                "id": alert.id,
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity.value,
                "metric_name": alert.metric_name,
                "current_value": alert.current_value,
                "threshold_value": alert.threshold_value,
                "trend": alert.trend,
                "created_at": alert.created_at.isoformat(),
                "acknowledged": alert.acknowledged
            }
            for alert in sorted(alerts, key=lambda x: x.created_at, reverse=True)
        ]
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, user_id: str):
    """Acknowledge an alert"""
    try:
        for alert in bi_engine.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_by = user_id
                alert.acknowledged_at = datetime.now()
                return {"status": "acknowledged"}
        
        raise HTTPException(status_code=404, detail="Alert not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictions")
async def get_predictions():
    """Get business predictions"""
    try:
        predictions = sorted(bi_engine.predictions, key=lambda x: x.created_at, reverse=True)
        return [
            {
                "id": pred.id,
                "metric_name": pred.metric_name,
                "prediction_type": pred.prediction_type,
                "predicted_value": pred.predicted_value,
                "confidence_interval": pred.confidence_interval,
                "confidence_score": pred.confidence_score,
                "time_horizon": pred.time_horizon,
                "factors": pred.factors,
                "created_at": pred.created_at.isoformat()
            }
            for pred in predictions
        ]
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
