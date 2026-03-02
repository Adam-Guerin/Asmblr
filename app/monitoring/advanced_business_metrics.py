"""
Métriques Business Avancées pour Asmblr
Tracking des KPIs métier et analytics avancés
"""

import asyncio
import json
import logging
from typing import Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import defaultdict, deque
import redis
from prometheus_client import Gauge, Counter, Histogram
import sqlite3
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types de métriques business"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    RATIO = "ratio"


@dataclass
class BusinessMetric:
    """Définition d'une métrique business"""
    name: str
    description: str
    metric_type: MetricType
    unit: str
    tags: list[str]
    target_value: float | None = None
    alert_threshold: float | None = None


@dataclass
class MVPIdeaMetrics:
    """Métriques pour les idées MVP"""
    idea_id: str
    timestamp: datetime
    topic: str
    confidence_score: float
    market_signal_score: float
    actionability_score: float
    novelty_score: float
    icp_alignment_score: float
    processing_time: float
    llm_tokens_used: int
    sources_analyzed: int
    pains_extracted: int
    opportunities_generated: int
    final_decision: str  # PASS, KILL, ABORT
    decision_rationale: str


@dataclass
class MVPBuildMetrics:
    """Métriques pour les builds MVP"""
    build_id: str
    idea_id: str
    timestamp: datetime
    build_duration: float
    cycles_completed: int
    cycles_failed: int
    ui_lint_score: float
    test_success_rate: float
    build_success: bool
    frontend_stack: str
    backend_stack: str
    features_implemented: int
    bugs_fixed: int
    code_quality_score: float


@dataclass
class UserEngagementMetrics:
    """Métriques d'engagement utilisateur"""
    user_id: str
    session_id: str
    timestamp: datetime
    session_duration: float
    ideas_generated: int
    mvps_built: int
    feedback_submitted: int
    features_used: list[str]
    satisfaction_score: float | None
    conversion_rate: float
    churn_risk: float


@dataclass
class RevenueMetrics:
    """Métriques de revenus"""
    period: str  # daily, weekly, monthly
    timestamp: datetime
    total_revenue: float
    active_users: int
    paying_users: int
    trial_users: int
    churned_users: int
    mrr: float  # Monthly Recurring Revenue
    arr: float  # Annual Recurring Revenue
    ltv: float  # Lifetime Value
    cac: float  # Customer Acquisition Cost


class AdvancedBusinessMetrics:
    """Système de métriques business avancées"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        db_path: str = "data/business_metrics.db",
        retention_days: int = 90
    ):
        self.redis_url = redis_url
        self.db_path = db_path
        self.retention_days = retention_days
        
        # Redis pour les métriques temps réel
        self.redis_client = redis.from_url(redis_url)
        
        # SQLite pour l'historique
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        # Définition des métriques business
        self.business_metrics = self._define_business_metrics()
        
        # Métriques Prometheus
        self.setup_prometheus_metrics()
        
        # Cache des métriques
        self.metrics_cache: dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Historique pour les tendances
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))
        
        logger.info("Advanced Business Metrics initialisé")
    
    def _init_database(self):
        """Initialise la base de données SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table des idées MVP
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mvp_idea_metrics (
                id TEXT PRIMARY KEY,
                timestamp DATETIME,
                topic TEXT,
                confidence_score REAL,
                market_signal_score REAL,
                actionability_score REAL,
                novelty_score REAL,
                icp_alignment_score REAL,
                processing_time REAL,
                llm_tokens_used INTEGER,
                sources_analyzed INTEGER,
                pains_extracted INTEGER,
                opportunities_generated INTEGER,
                final_decision TEXT,
                decision_rationale TEXT
            )
        """)
        
        # Table des builds MVP
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mvp_build_metrics (
                id TEXT PRIMARY KEY,
                idea_id TEXT,
                timestamp DATETIME,
                build_duration REAL,
                cycles_completed INTEGER,
                cycles_failed INTEGER,
                ui_lint_score REAL,
                test_success_rate REAL,
                build_success BOOLEAN,
                frontend_stack TEXT,
                backend_stack TEXT,
                features_implemented INTEGER,
                bugs_fixed INTEGER,
                code_quality_score REAL,
                FOREIGN KEY (idea_id) REFERENCES mvp_idea_metrics (id)
            )
        """)
        
        # Table de l'engagement utilisateur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_engagement_metrics (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                session_id TEXT,
                timestamp DATETIME,
                session_duration REAL,
                ideas_generated INTEGER,
                mvps_built INTEGER,
                feedback_submitted INTEGER,
                features_used TEXT,
                satisfaction_score REAL,
                conversion_rate REAL,
                churn_risk REAL
            )
        """)
        
        # Table des revenus
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS revenue_metrics (
                id TEXT PRIMARY KEY,
                period TEXT,
                timestamp DATETIME,
                total_revenue REAL,
                active_users INTEGER,
                paying_users INTEGER,
                trial_users INTEGER,
                churned_users INTEGER,
                mrr REAL,
                arr REAL,
                ltv REAL,
                cac REAL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _define_business_metrics(self) -> dict[str, BusinessMetric]:
        """Définit les métriques business"""
        return {
            # Métriques de pipeline
            'ideas_generated_per_hour': BusinessMetric(
                name='ideas_generated_per_hour',
                description='Nombre d\'idées générées par heure',
                metric_type=MetricType.GAUGE,
                unit='ideas/hour',
                tags=['pipeline', 'generation'],
                target_value=10.0,
                alert_threshold=2.0
            ),
            'idea_success_rate': BusinessMetric(
                name='idea_success_rate',
                description='Taux de succès des idées (PASS / total)',
                metric_type=MetricType.RATIO,
                unit='percentage',
                tags=['pipeline', 'quality'],
                target_value=0.7,
                alert_threshold=0.3
            ),
            'avg_processing_time': BusinessMetric(
                name='avg_processing_time',
                description='Temps moyen de traitement des idées',
                metric_type=MetricType.HISTOGRAM,
                unit='seconds',
                tags=['pipeline', 'performance'],
                target_value=30.0,
                alert_threshold=60.0
            ),
            
            # Métriques MVP
            'mvp_build_success_rate': BusinessMetric(
                name='mvp_build_success_rate',
                description='Taux de succès des builds MVP',
                metric_type=MetricType.RATIO,
                unit='percentage',
                tags=['mvp', 'quality'],
                target_value=0.9,
                alert_threshold=0.7
            ),
            'avg_build_duration': BusinessMetric(
                name='avg_build_duration',
                description='Durée moyenne des builds MVP',
                metric_type=MetricType.HISTOGRAM,
                unit='seconds',
                tags=['mvp', 'performance'],
                target_value=300.0,
                alert_threshold=600.0
            ),
            'code_quality_score': BusinessMetric(
                name='code_quality_score',
                description='Score moyen de qualité du code',
                metric_type=MetricType.GAUGE,
                unit='score',
                tags=['mvp', 'quality'],
                target_value=8.0,
                alert_threshold=6.0
            ),
            
            # Métriques utilisateur
            'user_satisfaction_score': BusinessMetric(
                name='user_satisfaction_score',
                description='Score de satisfaction utilisateur',
                metric_type=MetricType.GAUGE,
                unit='score',
                tags=['user', 'satisfaction'],
                target_value=4.5,
                alert_threshold=3.0
            ),
            'user_retention_rate': BusinessMetric(
                name='user_retention_rate',
                description='Taux de rétention utilisateur',
                metric_type=MetricType.RATIO,
                unit='percentage',
                tags=['user', 'retention'],
                target_value=0.8,
                alert_threshold=0.6
            ),
            'conversion_rate': BusinessMetric(
                name='conversion_rate',
                description='Taux de conversion trial → payant',
                metric_type=MetricType.RATIO,
                unit='percentage',
                tags=['user', 'revenue'],
                target_value=0.2,
                alert_threshold=0.1
            ),
            
            # Métriques de revenus
            'monthly_recurring_revenue': BusinessMetric(
                name='monthly_recurring_revenue',
                description='Revenu mensuel récurrent',
                metric_type=MetricType.GAUGE,
                unit='USD',
                tags=['revenue', 'mrr'],
                target_value=10000.0,
                alert_threshold=5000.0
            ),
            'customer_lifetime_value': BusinessMetric(
                name='customer_lifetime_value',
                description='Valeur vie client',
                metric_type=MetricType.GAUGE,
                unit='USD',
                tags=['revenue', 'ltv'],
                target_value=500.0,
                alert_threshold=200.0
            ),
            'customer_acquisition_cost': BusinessMetric(
                name='customer_acquisition_cost',
                description='Coût d\'acquisition client',
                metric_type=MetricType.GAUGE,
                unit='USD',
                tags=['revenue', 'cac'],
                target_value=50.0,
                alert_threshold=100.0
            )
        }
    
    def setup_prometheus_metrics(self):
        """Configure les métriques Prometheus"""
        self.prometheus_metrics = {}
        
        for metric_name, metric_def in self.business_metrics.items():
            if metric_def.metric_type == MetricType.COUNTER:
                self.prometheus_metrics[metric_name] = Counter(
                    f'asmblr_business_{metric_name}',
                    metric_def.description,
                    metric_def.tags
                )
            elif metric_def.metric_type == MetricType.GAUGE:
                self.prometheus_metrics[metric_name] = Gauge(
                    f'asmblr_business_{metric_name}',
                    metric_def.description,
                    metric_def.tags
                )
            elif metric_def.metric_type == MetricType.HISTOGRAM:
                self.prometheus_metrics[metric_name] = Histogram(
                    f'asmblr_business_{metric_name}',
                    metric_def.description,
                    metric_def.tags,
                    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
                )
    
    async def record_idea_metrics(self, metrics: MVPIdeaMetrics):
        """Enregistre les métriques d'une idée MVP"""
        try:
            # Sauvegarder en base de données
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO mvp_idea_metrics 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.idea_id,
                metrics.timestamp.isoformat(),
                metrics.topic,
                metrics.confidence_score,
                metrics.market_signal_score,
                metrics.actionability_score,
                metrics.novelty_score,
                metrics.icp_alignment_score,
                metrics.processing_time,
                metrics.llm_tokens_used,
                metrics.sources_analyzed,
                metrics.pains_extracted,
                metrics.opportunities_generated,
                metrics.final_decision,
                metrics.decision_rationale
            ))
            
            conn.commit()
            conn.close()
            
            # Mettre à jour les métriques temps réel
            await self._update_realtime_metrics(metrics)
            
            # Stocker dans Redis pour l'analyse
            redis_key = f"idea_metrics:{metrics.idea_id}"
            self.redis_client.setex(
                redis_key,
                timedelta(hours=24),
                json.dumps(asdict(metrics), default=str)
            )
            
            logger.info(f"Métriques idée enregistrées: {metrics.idea_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement des métriques idée: {e}")
    
    async def record_build_metrics(self, metrics: MVPBuildMetrics):
        """Enregistre les métriques d'un build MVP"""
        try:
            # Sauvegarder en base de données
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO mvp_build_metrics 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.build_id,
                metrics.idea_id,
                metrics.timestamp.isoformat(),
                metrics.build_duration,
                metrics.cycles_completed,
                metrics.cycles_failed,
                metrics.ui_lint_score,
                metrics.test_success_rate,
                metrics.build_success,
                metrics.frontend_stack,
                metrics.backend_stack,
                metrics.features_implemented,
                metrics.bugs_fixed,
                metrics.code_quality_score
            ))
            
            conn.commit()
            conn.close()
            
            # Mettre à jour les métriques temps réel
            await self._update_build_metrics(metrics)
            
            # Stocker dans Redis
            redis_key = f"build_metrics:{metrics.build_id}"
            self.redis_client.setex(
                redis_key,
                timedelta(hours=24),
                json.dumps(asdict(metrics), default=str)
            )
            
            logger.info(f"Métriques build enregistrées: {metrics.build_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement des métriques build: {e}")
    
    async def record_user_engagement(self, metrics: UserEngagementMetrics):
        """Enregistre les métriques d'engagement utilisateur"""
        try:
            # Sauvegarder en base de données
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_engagement_metrics 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"{metrics.user_id}_{metrics.session_id}",
                metrics.user_id,
                metrics.session_id,
                metrics.timestamp.isoformat(),
                metrics.session_duration,
                metrics.ideas_generated,
                metrics.mvps_built,
                metrics.feedback_submitted,
                json.dumps(metrics.features_used),
                metrics.satisfaction_score,
                metrics.conversion_rate,
                metrics.churn_risk
            ))
            
            conn.commit()
            conn.close()
            
            # Mettre à jour les métriques temps réel
            await self._update_user_metrics(metrics)
            
            logger.info(f"Métriques utilisateur enregistrées: {metrics.user_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement des métriques utilisateur: {e}")
    
    async def record_revenue_metrics(self, metrics: RevenueMetrics):
        """Enregistre les métriques de revenus"""
        try:
            # Sauvegarder en base de données
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO revenue_metrics 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"{metrics.period}_{metrics.timestamp.strftime('%Y%m%d')}",
                metrics.period,
                metrics.timestamp.isoformat(),
                metrics.total_revenue,
                metrics.active_users,
                metrics.paying_users,
                metrics.trial_users,
                metrics.churned_users,
                metrics.mrr,
                metrics.arr,
                metrics.ltv,
                metrics.cac
            ))
            
            conn.commit()
            conn.close()
            
            # Mettre à jour les métriques Prometheus
            self.prometheus_metrics['monthly_recurring_revenue'].set(metrics.mrr)
            self.prometheus_metrics['customer_lifetime_value'].set(metrics.ltv)
            self.prometheus_metrics['customer_acquisition_cost'].set(metrics.cac)
            
            logger.info(f"Métriques revenus enregistrées: {metrics.period}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement des métriques revenus: {e}")
    
    async def _update_realtime_metrics(self, metrics: MVPIdeaMetrics):
        """Met à jour les métriques temps réel pour les idées"""
        current_time = datetime.now()
        
        # Compteur d'idées générées
        hour_key = current_time.strftime('%Y%m%d%H')
        ideas_key = f"ideas_count:{hour_key}"
        self.redis_client.incr(ideas_key)
        self.redis_client.expire(ideas_key, timedelta(hours=25))
        
        # Métriques de qualité
        if metrics.final_decision == 'PASS':
            self.redis_client.incr("ideas_passed")
        elif metrics.final_decision == 'KILL':
            self.redis_client.incr("ideas_killed")
        else:
            self.redis_client.incr("ideas_aborted")
        
        # Tokens utilisés
        self.redis_client.incrby("total_tokens_used", metrics.llm_tokens_used)
        
        # Temps de traitement
        self.prometheus_metrics['avg_processing_time'].observe(metrics.processing_time)
    
    async def _update_build_metrics(self, metrics: MVPBuildMetrics):
        """Met à jour les métriques temps réel pour les builds"""
        # Taux de succès
        total_builds = int(self.redis_client.get("total_builds") or 0) + 1
        successful_builds = int(self.redis_client.get("successful_builds") or 0)
        
        self.redis_client.set("total_builds", total_builds)
        
        if metrics.build_success:
            successful_builds += 1
            self.redis_client.set("successful_builds", successful_builds)
        
        success_rate = successful_builds / total_builds
        self.prometheus_metrics['mvp_build_success_rate'].set(success_rate)
        
        # Durée du build
        self.prometheus_metrics['avg_build_duration'].observe(metrics.build_duration)
        
        # Qualité du code
        if metrics.code_quality_score:
            self.prometheus_metrics['code_quality_score'].set(metrics.code_quality_score)
    
    async def _update_user_metrics(self, metrics: UserEngagementMetrics):
        """Met à jour les métriques temps réel pour les utilisateurs"""
        # Satisfaction
        if metrics.satisfaction_score:
            self.prometheus_metrics['user_satisfaction_score'].set(metrics.satisfaction_score)
        
        # Conversion
        if metrics.conversion_rate:
            self.prometheus_metrics['conversion_rate'].set(metrics.conversion_rate)
    
    async def get_dashboard_metrics(self) -> dict[str, Any]:
        """Retourne les métriques pour le dashboard"""
        try:
            current_time = datetime.now()
            
            # Métriques de pipeline
            pipeline_metrics = await self._get_pipeline_metrics(current_time)
            
            # Métriques MVP
            mvp_metrics = await self._get_mvp_metrics(current_time)
            
            # Métriques utilisateur
            user_metrics = await self._get_user_metrics(current_time)
            
            # Métriques de revenus
            revenue_metrics = await self._get_revenue_metrics(current_time)
            
            # Tendances
            trends = await self._calculate_trends()
            
            return {
                'timestamp': current_time.isoformat(),
                'pipeline': pipeline_metrics,
                'mvp': mvp_metrics,
                'users': user_metrics,
                'revenue': revenue_metrics,
                'trends': trends,
                'alerts': await self._check_alerts()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques dashboard: {e}")
            return {'error': str(e)}
    
    async def _get_pipeline_metrics(self, current_time: datetime) -> dict[str, Any]:
        """Récupère les métriques de pipeline"""
        # Idées générées dans la dernière heure
        hour_key = current_time.strftime('%Y%m%d%H')
        ideas_count = int(self.redis_client.get(f"ideas_count:{hour_key}") or 0)
        
        # Taux de succès
        total_ideas = (int(self.redis_client.get("ideas_passed") or 0) +
                      int(self.redis_client.get("ideas_killed") or 0) +
                      int(self.redis_client.get("ideas_aborted") or 0))
        
        passed_ideas = int(self.redis_client.get("ideas_passed") or 0)
        success_rate = passed_ideas / total_ideas if total_ideas > 0 else 0
        
        # Tokens utilisés
        total_tokens = int(self.redis_client.get("total_tokens_used") or 0)
        
        return {
            'ideas_per_hour': ideas_count,
            'success_rate': success_rate,
            'total_ideas': total_ideas,
            'tokens_used': total_tokens
        }
    
    async def _get_mvp_metrics(self, current_time: datetime) -> dict[str, Any]:
        """Récupère les métriques MVP"""
        # Stats des builds
        total_builds = int(self.redis_client.get("total_builds") or 0)
        successful_builds = int(self.redis_client.get("successful_builds") or 0)
        
        build_success_rate = successful_builds / total_builds if total_builds > 0 else 0
        
        # Qualité moyenne du code (derniers 7 jours)
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT AVG(code_quality_score) as avg_quality
            FROM mvp_build_metrics
            WHERE timestamp >= datetime('now', '-7 days')
            AND code_quality_score IS NOT NULL
        """
        avg_quality = conn.execute(query).fetchone()[0] or 0
        conn.close()
        
        return {
            'total_builds': total_builds,
            'success_rate': build_success_rate,
            'avg_quality_score': avg_quality
        }
    
    async def _get_user_metrics(self, current_time: datetime) -> dict[str, Any]:
        """Récupère les métriques utilisateur"""
        conn = sqlite3.connect(self.db_path)
        
        # Utilisateurs actifs (derniers 7 jours)
        active_users_query = """
            SELECT COUNT(DISTINCT user_id) as count
            FROM user_engagement_metrics
            WHERE timestamp >= datetime('now', '-7 days')
        """
        active_users = conn.execute(active_users_query).fetchone()[0] or 0
        
        # Satisfaction moyenne
        satisfaction_query = """
            SELECT AVG(satisfaction_score) as avg_satisfaction
            FROM user_engagement_metrics
            WHERE timestamp >= datetime('now', '-7 days')
            AND satisfaction_score IS NOT NULL
        """
        avg_satisfaction = conn.execute(satisfaction_query).fetchone()[0] or 0
        
        # Taux de conversion
        conversion_query = """
            SELECT AVG(conversion_rate) as avg_conversion
            FROM user_engagement_metrics
            WHERE timestamp >= datetime('now', '-30 days')
            AND conversion_rate IS NOT NULL
        """
        avg_conversion = conn.execute(conversion_query).fetchone()[0] or 0
        
        conn.close()
        
        return {
            'active_users': active_users,
            'avg_satisfaction': avg_satisfaction,
            'conversion_rate': avg_conversion
        }
    
    async def _get_revenue_metrics(self, current_time: datetime) -> dict[str, Any]:
        """Récupère les métriques de revenus"""
        conn = sqlite3.connect(self.db_path)
        
        # MRR du mois courant
        mrr_query = """
            SELECT mrr
            FROM revenue_metrics
            WHERE period = 'monthly'
            AND timestamp >= datetime('now', 'start of month')
            ORDER BY timestamp DESC
            LIMIT 1
        """
        mrr_result = conn.execute(mrr_query).fetchone()
        current_mrr = mrr_result[0] if mrr_result else 0
        
        # LTV et CAC moyens
        ltv_cac_query = """
            SELECT AVG(ltv) as avg_ltv, AVG(cac) as avg_cac
            FROM revenue_metrics
            WHERE timestamp >= datetime('now', '-30 days')
        """
        ltv_cac_result = conn.execute(ltv_cac_query).fetchone()
        avg_ltv = ltv_cac_result[0] if ltv_cac_result and ltv_cac_result[0] else 0
        avg_cac = ltv_cac_result[1] if ltv_cac_result and ltv_cac_result[1] else 0
        
        conn.close()
        
        return {
            'mrr': current_mrr,
            'ltv': avg_ltv,
            'cac': avg_cac,
            'ltv_cac_ratio': avg_ltv / avg_cac if avg_cac > 0 else 0
        }
    
    async def _calculate_trends(self) -> dict[str, str]:
        """Calcule les tendances des métriques"""
        trends = {}
        
        for metric_name in self.business_metrics.keys():
            # Récupérer les dernières valeurs
            values = list(self.metrics_history[metric_name])
            
            if len(values) >= 2:
                recent_avg = np.mean([v['value'] for v in values[-5:]])
                older_avg = np.mean([v['value'] for v in values[-10:-5]])
                
                if recent_avg > older_avg * 1.1:
                    trends[metric_name] = 'up'
                elif recent_avg < older_avg * 0.9:
                    trends[metric_name] = 'down'
                else:
                    trends[metric_name] = 'stable'
            else:
                trends[metric_name] = 'insufficient_data'
        
        return trends
    
    async def _check_alerts(self) -> list[dict[str, Any]]:
        """Vérifie les alertes basées sur les seuils"""
        alerts = []
        
        for metric_name, metric_def in self.business_metrics.items():
            if metric_def.alert_threshold is None:
                continue
            
            # Récupérer la valeur actuelle
            if metric_name in self.prometheus_metrics:
                try:
                    if metric_def.metric_type == MetricType.GAUGE:
                        current_value = self.prometheus_metrics[metric_name]._value._value
                    else:
                        # Pour les autres types, utiliser la dernière valeur de l'historique
                        values = list(self.metrics_history[metric_name])
                        current_value = values[-1]['value'] if values else 0
                    
                    # Vérifier le seuil
                    if current_value < metric_def.alert_threshold:
                        alerts.append({
                            'metric': metric_name,
                            'current_value': current_value,
                            'threshold': metric_def.alert_threshold,
                            'severity': 'warning',
                            'message': f"{metric_def.description} est en dessous du seuil: {current_value:.2f} < {metric_def.alert_threshold:.2f}"
                        })
                
                except Exception as e:
                    logger.warning(f"Erreur lors de la vérification de l'alerte {metric_name}: {e}")
        
        return alerts
    
    async def generate_business_report(self, period: str = 'weekly') -> dict[str, Any]:
        """Génère un rapport business détaillé"""
        try:
            # Déterminer la période
            if period == 'daily':
                start_date = datetime.now() - timedelta(days=1)
            elif period == 'weekly':
                start_date = datetime.now() - timedelta(weeks=1)
            elif period == 'monthly':
                start_date = datetime.now() - timedelta(days=30)
            else:
                start_date = datetime.now() - timedelta(weeks=1)
            
            conn = sqlite3.connect(self.db_path)
            
            # Statistiques des idées
            idea_stats = self._get_idea_statistics(conn, start_date)
            
            # Statistiques des builds
            build_stats = self._get_build_statistics(conn, start_date)
            
            # Statistiques utilisateurs
            user_stats = self._get_user_statistics(conn, start_date)
            
            # Statistiques de revenus
            revenue_stats = self._get_revenue_statistics(conn, start_date)
            
            conn.close()
            
            return {
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': datetime.now().isoformat(),
                'idea_metrics': idea_stats,
                'build_metrics': build_stats,
                'user_metrics': user_stats,
                'revenue_metrics': revenue_stats,
                'recommendations': await self._generate_recommendations()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport business: {e}")
            return {'error': str(e)}
    
    def _get_idea_statistics(self, conn: sqlite3.Connection, start_date: datetime) -> dict[str, Any]:
        """Calcule les statistiques des idées"""
        query = """
            SELECT 
                COUNT(*) as total_ideas,
                COUNT(CASE WHEN final_decision = 'PASS' THEN 1 END) as passed_ideas,
                COUNT(CASE WHEN final_decision = 'KILL' THEN 1 END) as killed_ideas,
                COUNT(CASE WHEN final_decision = 'ABORT' THEN 1 END) as aborted_ideas,
                AVG(confidence_score) as avg_confidence,
                AVG(market_signal_score) as avg_market_signal,
                AVG(actionability_score) as avg_actionability,
                AVG(processing_time) as avg_processing_time,
                SUM(llm_tokens_used) as total_tokens
            FROM mvp_idea_metrics
            WHERE timestamp >= ?
        """
        
        result = conn.execute(query, (start_date.isoformat(),)).fetchone()
        
        if result and result[0] > 0:
            return {
                'total_ideas': result[0],
                'passed_ideas': result[1],
                'killed_ideas': result[2],
                'aborted_ideas': result[3],
                'success_rate': result[1] / result[0],
                'avg_confidence': result[4] or 0,
                'avg_market_signal': result[5] or 0,
                'avg_actionability': result[6] or 0,
                'avg_processing_time': result[7] or 0,
                'total_tokens': result[8] or 0
            }
        else:
            return {'total_ideas': 0}
    
    def _get_build_statistics(self, conn: sqlite3.Connection, start_date: datetime) -> dict[str, Any]:
        """Calcule les statistiques des builds"""
        query = """
            SELECT 
                COUNT(*) as total_builds,
                COUNT(CASE WHEN build_success = 1 THEN 1 END) as successful_builds,
                AVG(build_duration) as avg_duration,
                AVG(ui_lint_score) as avg_ui_score,
                AVG(test_success_rate) as avg_test_rate,
                AVG(code_quality_score) as avg_quality,
                SUM(features_implemented) as total_features,
                SUM(bugs_fixed) as total_bugs
            FROM mvp_build_metrics
            WHERE timestamp >= ?
        """
        
        result = conn.execute(query, (start_date.isoformat(),)).fetchone()
        
        if result and result[0] > 0:
            return {
                'total_builds': result[0],
                'successful_builds': result[1],
                'success_rate': result[1] / result[0],
                'avg_duration': result[2] or 0,
                'avg_ui_score': result[3] or 0,
                'avg_test_rate': result[4] or 0,
                'avg_quality': result[5] or 0,
                'total_features': result[6] or 0,
                'total_bugs': result[7] or 0
            }
        else:
            return {'total_builds': 0}
    
    def _get_user_statistics(self, conn: sqlite3.Connection, start_date: datetime) -> dict[str, Any]:
        """Calcule les statistiques utilisateurs"""
        # Utilisateurs actifs
        active_users_query = """
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM user_engagement_metrics
            WHERE timestamp >= ?
        """
        active_users = conn.execute(active_users_query, (start_date.isoformat(),)).fetchone()[0] or 0
        
        # Satisfaction et engagement
        engagement_query = """
            SELECT 
                AVG(session_duration) as avg_session_duration,
                AVG(ideas_generated) as avg_ideas_generated,
                AVG(mvps_built) as avg_mvps_built,
                AVG(satisfaction_score) as avg_satisfaction,
                AVG(conversion_rate) as avg_conversion
            FROM user_engagement_metrics
            WHERE timestamp >= ?
        """
        result = conn.execute(engagement_query, (start_date.isoformat(),)).fetchone()
        
        return {
            'active_users': active_users,
            'avg_session_duration': result[0] or 0,
            'avg_ideas_generated': result[1] or 0,
            'avg_mvps_built': result[2] or 0,
            'avg_satisfaction': result[3] or 0,
            'avg_conversion': result[4] or 0
        }
    
    def _get_revenue_statistics(self, conn: sqlite3.Connection, start_date: datetime) -> dict[str, Any]:
        """Calcule les statistiques de revenus"""
        query = """
            SELECT 
                SUM(total_revenue) as total_revenue,
                AVG(active_users) as avg_active_users,
                AVG(paying_users) as avg_paying_users,
                AVG(mrr) as avg_mrr,
                AVG(ltv) as avg_ltv,
                AVG(cac) as avg_cac
            FROM revenue_metrics
            WHERE timestamp >= ?
        """
        
        result = conn.execute(query, (start_date.isoformat(),)).fetchone()
        
        if result and result[0]:
            return {
                'total_revenue': result[0] or 0,
                'avg_active_users': result[1] or 0,
                'avg_paying_users': result[2] or 0,
                'avg_mrr': result[3] or 0,
                'avg_ltv': result[4] or 0,
                'avg_cac': result[5] or 0,
                'ltv_cac_ratio': (result[4] or 0) / (result[5] or 1)
            }
        else:
            return {'total_revenue': 0}
    
    async def _generate_recommendations(self) -> list[str]:
        """Génère des recommandations basées sur les métriques"""
        recommendations = []
        
        # Récupérer les métriques actuelles
        dashboard_metrics = await self.get_dashboard_metrics()
        
        # Analyser et générer des recommandations
        if dashboard_metrics.get('pipeline', {}).get('success_rate', 0) < 0.5:
            recommendations.append(
                "Le taux de succès des idées est faible. Considérez à améliorer les critères de qualité ou à affiner les sources de données."
            )
        
        if dashboard_metrics.get('mvp', {}).get('success_rate', 0) < 0.8:
            recommendations.append(
                "Le taux de succès des builds MVP pourrait être amélioré. Vérifiez les templates et les cycles de build."
            )
        
        if dashboard_metrics.get('users', {}).get('avg_satisfaction', 0) < 3.5:
            recommendations.append(
                "La satisfaction utilisateur est basse. Envisagez d'améliorer l'UX ou d'ajouter des fonctionnalités demandées."
            )
        
        if dashboard_metrics.get('revenue', {}).get('ltv_cac_ratio', 0) < 3:
            recommendations.append(
                "Le ratio LTV/CAC est faible. Optimisez l'acquisition client ou augmentez la valeur vie client."
            )
        
        return recommendations


# Singleton global
_business_metrics: AdvancedBusinessMetrics | None = None


async def get_business_metrics() -> AdvancedBusinessMetrics:
    """Retourne l'instance singleton des métriques business"""
    global _business_metrics
    
    if _business_metrics is None:
        _business_metrics = AdvancedBusinessMetrics()
    
    return _business_metrics


# Exemple d'utilisation
async def example_usage():
    """Exemple d'utilisation des métriques business avancées"""
    metrics = await get_business_metrics()
    
    # Enregistrer une métrique d'idée
    idea_metrics = MVPIdeaMetrics(
        idea_id="idea-123",
        timestamp=datetime.now(),
        topic="AI Startup Generator",
        confidence_score=0.85,
        market_signal_score=0.78,
        actionability_score=0.92,
        novelty_score=0.73,
        icp_alignment_score=0.88,
        processing_time=25.5,
        llm_tokens_used=1500,
        sources_analyzed=8,
        pains_extracted=12,
        opportunities_generated=3,
        final_decision="PASS",
        decision_rationale="Strong market signals and high actionability"
    )
    
    await metrics.record_idea_metrics(idea_metrics)
    
    # Récupérer le dashboard
    dashboard = await metrics.get_dashboard_metrics()
    print(f"Dashboard metrics: {dashboard}")
    
    # Générer un rapport
    report = await metrics.generate_business_report('weekly')
    print(f"Weekly report: {report}")


if __name__ == "__main__":
    asyncio.run(example_usage())
