"""
Automated A/B Testing System for Asmblr
Advanced experimentation platform with statistical analysis and automated decision making
"""

import asyncio
import json
import logging
from typing import Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import uuid
import numpy as np
from scipy import stats
import redis
import sqlite3
from pathlib import Path
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """Status of an experiment"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"


class VariantType(Enum):
    """Types of variants"""
    CONTROL = "control"
    TREATMENT = "treatment"


class MetricType(Enum):
    """Types of metrics"""
    CONVERSION = "conversion"
    REVENUE = "revenue"
    ENGAGEMENT = "engagement"
    SATISFACTION = "satisfaction"
    PERFORMANCE = "performance"


class StatisticalTest(Enum):
    """Statistical tests"""
    T_TEST = "t_test"
    Z_TEST = "z_test"
    CHI_SQUARE = "chi_square"
    WILCOXON = "wilcoxon"
    MANN_WHITNEY = "mann_whitney"


@dataclass
class Variant:
    """Experiment variant"""
    variant_id: str
    name: str
    type: VariantType
    configuration: dict[str, Any]
    traffic_allocation: float  # 0.0 to 1.0
    description: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'variant_id': self.variant_id,
            'name': self.name,
            'type': self.type.value,
            'configuration': self.configuration,
            'traffic_allocation': self.traffic_allocation,
            'description': self.description
        }


@dataclass
class Metric:
    """Experiment metric"""
    metric_id: str
    name: str
    type: MetricType
    description: str
    unit: str
    higher_is_better: bool = True
    target_improvement: float = 0.0  # Target improvement percentage
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'metric_id': self.metric_id,
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'unit': self.unit,
            'higher_is_better': self.higher_is_better,
            'target_improvement': self.target_improvement
        }


@dataclass
class Experiment:
    """A/B test experiment"""
    experiment_id: str
    name: str
    description: str
    hypothesis: str
    variants: list[Variant]
    metrics: list[Metric]
    status: ExperimentStatus
    created_at: datetime
    started_at: datetime | None = None
    ended_at: datetime | None = None
    sample_size: int = 0
    confidence_level: float = 0.95
    min_sample_size: int = 100
    statistical_power: float = 0.8
    significance_threshold: float = 0.05
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'experiment_id': self.experiment_id,
            'name': self.name,
            'description': self.description,
            'hypothesis': self.hypothesis,
            'variants': [v.to_dict() for v in self.variants],
            'metrics': [m.to_dict() for m in self.metrics],
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'sample_size': self.sample_size,
            'confidence_level': self.confidence_level,
            'min_sample_size': self.min_sample_size,
            'statistical_power': self.statistical_power,
            'significance_threshold': self.significance_threshold
        }


@dataclass
class ExperimentResult:
    """Results of an experiment"""
    experiment_id: str
    variant_results: dict[str, dict[str, Any]]
    statistical_tests: dict[str, dict[str, Any]]
    winner: str | None = None
    confidence: float = 0.0
    recommendation: str = ""
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class UserAssignment:
    """User assignment to variant"""
    user_id: str
    experiment_id: str
    variant_id: str
    assigned_at: datetime
    converted: bool = False
    conversion_value: float = 0.0
    metrics: dict[str, float] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}


class ExperimentDatabase:
    """Database for storing experiment data"""
    
    def __init__(self, db_path: str = "data/ab_testing.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Experiments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                hypothesis TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                ended_at TEXT,
                sample_size INTEGER DEFAULT 0,
                confidence_level REAL DEFAULT 0.95,
                min_sample_size INTEGER DEFAULT 100,
                statistical_power REAL DEFAULT 0.8,
                significance_threshold REAL DEFAULT 0.05
            )
        """)
        
        # Variants table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS variants (
                variant_id TEXT PRIMARY KEY,
                experiment_id TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                configuration TEXT,
                traffic_allocation REAL NOT NULL,
                description TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments (experiment_id)
            )
        """)
        
        # Metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                metric_id TEXT PRIMARY KEY,
                experiment_id TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                unit TEXT,
                higher_is_better BOOLEAN DEFAULT 1,
                target_improvement REAL DEFAULT 0.0,
                FOREIGN KEY (experiment_id) REFERENCES experiments (experiment_id)
            )
        """)
        
        # User assignments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_assignments (
                user_id TEXT NOT NULL,
                experiment_id TEXT NOT NULL,
                variant_id TEXT NOT NULL,
                assigned_at TEXT NOT NULL,
                converted BOOLEAN DEFAULT 0,
                conversion_value REAL DEFAULT 0.0,
                metrics TEXT,
                PRIMARY KEY (user_id, experiment_id),
                FOREIGN KEY (experiment_id) REFERENCES experiments (experiment_id),
                FOREIGN KEY (variant_id) REFERENCES variants (variant_id)
            )
        """)
        
        # Results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiment_results (
                experiment_id TEXT PRIMARY KEY,
                variant_results TEXT NOT NULL,
                statistical_tests TEXT NOT NULL,
                winner TEXT,
                confidence REAL DEFAULT 0.0,
                recommendation TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (experiment_id) REFERENCES experiments (experiment_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_experiment(self, experiment: Experiment) -> None:
        """Save an experiment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Save experiment
            cursor.execute("""
                INSERT OR REPLACE INTO experiments 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment.experiment_id,
                experiment.name,
                experiment.description,
                experiment.hypothesis,
                experiment.status.value,
                experiment.created_at.isoformat(),
                experiment.started_at.isoformat() if experiment.started_at else None,
                experiment.ended_at.isoformat() if experiment.ended_at else None,
                experiment.sample_size,
                experiment.confidence_level,
                experiment.min_sample_size,
                experiment.statistical_power,
                experiment.significance_threshold
            ))
            
            # Save variants
            for variant in experiment.variants:
                cursor.execute("""
                    INSERT OR REPLACE INTO variants 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    variant.variant_id,
                    experiment.experiment_id,
                    variant.name,
                    variant.type.value,
                    json.dumps(variant.configuration),
                    variant.traffic_allocation,
                    variant.description
                ))
            
            # Save metrics
            for metric in experiment.metrics:
                cursor.execute("""
                    INSERT OR REPLACE INTO metrics 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric.metric_id,
                    experiment.experiment_id,
                    metric.name,
                    metric.type.value,
                    metric.description,
                    metric.unit,
                    metric.higher_is_better,
                    metric.target_improvement
                ))
            
            conn.commit()
            logger.info(f"Saved experiment: {experiment.experiment_id}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving experiment: {e}")
            raise
        finally:
            conn.close()
    
    def get_experiment(self, experiment_id: str) -> Experiment | None:
        """Get an experiment by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get experiment
            cursor.execute("""
                SELECT * FROM experiments WHERE experiment_id = ?
            """, (experiment_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            experiment = Experiment(
                experiment_id=row[0],
                name=row[1],
                description=row[2],
                hypothesis=row[3],
                status=ExperimentStatus(row[4]),
                created_at=datetime.fromisoformat(row[5]),
                started_at=datetime.fromisoformat(row[6]) if row[6] else None,
                ended_at=datetime.fromisoformat(row[7]) if row[7] else None,
                sample_size=row[8],
                confidence_level=row[9],
                min_sample_size=row[10],
                statistical_power=row[11],
                significance_threshold=row[12]
            )
            
            # Get variants
            cursor.execute("""
                SELECT * FROM variants WHERE experiment_id = ?
            """, (experiment_id,))
            
            experiment.variants = []
            for row in cursor.fetchall():
                variant = Variant(
                    variant_id=row[0],
                    name=row[2],
                    type=VariantType(row[3]),
                    configuration=json.loads(row[4]) if row[4] else {},
                    traffic_allocation=row[5],
                    description=row[6] or ""
                )
                experiment.variants.append(variant)
            
            # Get metrics
            cursor.execute("""
                SELECT * FROM metrics WHERE experiment_id = ?
            """, (experiment_id,))
            
            experiment.metrics = []
            for row in cursor.fetchall():
                metric = Metric(
                    metric_id=row[0],
                    name=row[2],
                    type=MetricType(row[3]),
                    description=row[4],
                    unit=row[5],
                    higher_is_better=bool(row[6]),
                    target_improvement=row[7]
                )
                experiment.metrics.append(metric)
            
            return experiment
            
        except Exception as e:
            logger.error(f"Error getting experiment {experiment_id}: {e}")
            return None
        finally:
            conn.close()
    
    def save_user_assignment(self, assignment: UserAssignment) -> None:
        """Save a user assignment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO user_assignments 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                assignment.user_id,
                assignment.experiment_id,
                assignment.variant_id,
                assignment.assigned_at.isoformat(),
                assignment.converted,
                assignment.conversion_value,
                json.dumps(assignment.metrics)
            ))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving user assignment: {e}")
            raise
        finally:
            conn.close()
    
    def get_user_assignments(self, experiment_id: str) -> list[UserAssignment]:
        """Get all user assignments for an experiment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM user_assignments WHERE experiment_id = ?
            """, (experiment_id,))
            
            assignments = []
            for row in cursor.fetchall():
                assignment = UserAssignment(
                    user_id=row[0],
                    experiment_id=row[1],
                    variant_id=row[2],
                    assigned_at=datetime.fromisoformat(row[3]),
                    converted=bool(row[4]),
                    conversion_value=row[5],
                    metrics=json.loads(row[6]) if row[6] else {}
                )
                assignments.append(assignment)
            
            return assignments
            
        except Exception as e:
            logger.error(f"Error getting user assignments: {e}")
            return []
        finally:
            conn.close()


class StatisticalAnalyzer:
    """Statistical analysis for A/B tests"""
    
    def __init__(self):
        pass
    
    def analyze_conversion(self, control_conversions: int, control_total: int,
                        treatment_conversions: int, treatment_total: int,
                        confidence_level: float = 0.95) -> dict[str, Any]:
        """Analyze conversion rates between control and treatment"""
        
        # Calculate conversion rates
        control_rate = control_conversions / control_total if control_total > 0 else 0
        treatment_rate = treatment_conversions / treatment_total if treatment_total > 0 else 0
        
        # Calculate relative improvement
        relative_improvement = (treatment_rate - control_rate) / control_rate if control_rate > 0 else 0
        
        # Two-proportion z-test
        pooled_rate = (control_conversions + treatment_conversions) / (control_total + treatment_total)
        se = np.sqrt(pooled_rate * (1 - pooled_rate) * (1/control_total + 1/treatment_total))
        
        if se > 0:
            z_score = (treatment_rate - control_rate) / se
            p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
        else:
            z_score = 0
            p_value = 1.0
        
        # Confidence interval
        alpha = 1 - confidence_level
        z_critical = stats.norm.ppf(1 - alpha/2)
        
        if se > 0:
            ci_lower = (treatment_rate - control_rate) - z_critical * se
            ci_upper = (treatment_rate - control_rate) + z_critical * se
        else:
            ci_lower = ci_upper = 0
        
        # Determine significance
        is_significant = p_value < (1 - confidence_level)
        
        return {
            'control_rate': control_rate,
            'treatment_rate': treatment_rate,
            'relative_improvement': relative_improvement,
            'absolute_improvement': treatment_rate - control_rate,
            'z_score': z_score,
            'p_value': p_value,
            'confidence_interval': (ci_lower, ci_upper),
            'is_significant': is_significant,
            'test_type': 'two_proportion_z_test'
        }
    
    def analyze_continuous_metric(self, control_values: list[float], treatment_values: list[float],
                                   confidence_level: float = 0.95) -> dict[str, Any]:
        """Analyze continuous metrics between control and treatment"""
        
        if not control_values or not treatment_values:
            return {'error': 'No data provided'}
        
        control_mean = np.mean(control_values)
        treatment_mean = np.mean(treatment_values)
        
        # Relative improvement
        relative_improvement = (treatment_mean - control_mean) / control_mean if control_mean != 0 else 0
        
        # Two-sample t-test
        t_stat, p_value = stats.ttest_ind(treatment_values, control_values)
        
        # Confidence interval
        alpha = 1 - confidence_level
        df = len(control_values) + len(treatment_values) - 2
        se = np.sqrt(np.var(control_values, ddof=1)/len(control_values) + 
                     np.var(treatment_values, ddof=1)/len(treatment_values))
        
        t_critical = stats.t.ppf(1 - alpha/2, df)
        ci_lower = (treatment_mean - control_mean) - t_critical * se
        ci_upper = (treatment_mean - control_mean) + t_critical * se
        
        # Determine significance
        is_significant = p_value < (1 - confidence_level)
        
        return {
            'control_mean': control_mean,
            'treatment_mean': treatment_mean,
            'relative_improvement': relative_improvement,
            'absolute_improvement': treatment_mean - control_mean,
            't_statistic': t_stat,
            'p_value': p_value,
            'confidence_interval': (ci_lower, ci_upper),
            'is_significant': is_significant,
            'test_type': 'two_sample_t_test'
        }
    
    def calculate_sample_size(self, baseline_rate: float, minimum_detectable_effect: float,
                            power: float = 0.8, alpha: float = 0.05) -> int:
        """Calculate required sample size for conversion rate test"""
        
        # Standard normal distribution values
        z_alpha = stats.norm.ppf(1 - alpha/2)
        z_beta = stats.norm.ppf(power)
        
        # Pooled proportion (approximation)
        p1 = baseline_rate
        p2 = baseline_rate * (1 + minimum_detectable_effect)
        p_pooled = (p1 + p2) / 2
        
        # Sample size formula
        n = (z_alpha * np.sqrt(2 * p_pooled * (1 - p_pooled)) + 
              z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2)))**2 / (p2 - p1)**2
        
        return int(np.ceil(n))


class TrafficSplitter:
    """Traffic splitter for A/B tests"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url)
        self.user_assignments: dict[str, dict[str, str]] = {}
    
    def assign_user_to_variant(self, user_id: str, experiment: Experiment) -> Variant | None:
        """Assign a user to a variant"""
        
        # Check if user is already assigned
        if user_id in self.user_assignments.get(experiment.experiment_id, {}):
            assigned_variant_id = self.user_assignments[experiment.experiment_id][user_id]
            
            # Find the variant
            for variant in experiment.variants:
                if variant.variant_id == assigned_variant_id:
                    return variant
        
        # Assign to a variant based on traffic allocation
        rand = random.random()
        cumulative = 0.0
        
        for variant in experiment.variants:
            cumulative += variant.traffic_allocation
            if rand <= cumulative:
                # Save assignment
                if experiment.experiment_id not in self.user_assignments:
                    self.user_assignments[experiment.experiment_id] = {}
                
                self.user_assignments[experiment.experiment_id][user_id] = variant.variant_id
                
                # Save to Redis
                assignment_key = f"assignment:{experiment.experiment_id}:{user_id}"
                self.redis_client.setex(
                    assignment_key,
                    timedelta(days=30),
                    json.dumps({
                        'variant_id': variant.variant_id,
                        'assigned_at': datetime.utcnow().isoformat()
                    })
                )
                
                return variant
        
        return None
    
    def get_user_variant(self, user_id: str, experiment_id: str) -> str | None:
        """Get the variant assigned to a user"""
        
        # Check memory first
        if experiment_id in self.user_assignments:
            if user_id in self.user_assignments[experiment_id]:
                return self.user_assignments[experiment_id][user_id]
        
        # Check Redis
        assignment_key = f"assignment:{experiment_id}:{user_id}"
        assignment_data = self.redis_client.get(assignment_key)
        
        if assignment_data:
            assignment = json.loads(assignment_data)
            
            # Cache in memory
            if experiment_id not in self.user_assignments:
                self.user_assignments[experiment_id] = {}
            self.user_assignments[experiment_id][user_id] = assignment['variant_id']
            
            return assignment['variant_id']
        
        return None


class ExperimentRunner:
    """Runner for A/B test experiments"""
    
    def __init__(self, db_path: str = "data/ab_testing.db", redis_url: str = "redis://localhost:6379/0"):
        self.database = ExperimentDatabase(db_path)
        self.analyzer = StatisticalAnalyzer()
        self.traffic_splitter = TrafficSplitter(redis_url)
        self.running_experiments: dict[str, Experiment] = {}
    
    def create_experiment(self, name: str, description: str, hypothesis: str,
                         variants: list[dict[str, Any]], metrics: list[dict[str, Any]],
                         **kwargs) -> Experiment:
        """Create a new experiment"""
        
        experiment_id = str(uuid.uuid4())
        
        # Create variants
        experiment_variants = []
        for i, variant_data in enumerate(variants):
            variant = Variant(
                variant_id=str(uuid.uuid4()),
                name=variant_data['name'],
                type=VariantType(variant_data.get('type', 'treatment' if i > 0 else 'control')),
                configuration=variant_data.get('configuration', {}),
                traffic_allocation=variant_data.get('traffic_allocation', 1.0 / len(variants)),
                description=variant_data.get('description', '')
            )
            experiment_variants.append(variant)
        
        # Create metrics
        experiment_metrics = []
        for metric_data in metrics:
            metric = Metric(
                metric_id=str(uuid.uuid4()),
                name=metric_data['name'],
                type=MetricType(metric_data['type']),
                description=metric_data.get('description', ''),
                unit=metric_data.get('unit', ''),
                higher_is_better=metric_data.get('higher_is_better', True),
                target_improvement=metric_data.get('target_improvement', 0.0)
            )
            experiment_metrics.append(metric)
        
        # Create experiment
        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            hypothesis=hypothesis,
            variants=experiment_variants,
            metrics=experiment_metrics,
            status=ExperimentStatus.DRAFT,
            created_at=datetime.utcnow(),
            **kwargs
        )
        
        # Save experiment
        self.database.save_experiment(experiment)
        
        logger.info(f"Created experiment: {experiment_id}")
        return experiment
    
    def start_experiment(self, experiment_id: str) -> bool:
        """Start an experiment"""
        experiment = self.database.get_experiment(experiment_id)
        if not experiment:
            return False
        
        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.utcnow()
        
        self.database.save_experiment(experiment)
        self.running_experiments[experiment_id] = experiment
        
        logger.info(f"Started experiment: {experiment_id}")
        return True
    
    def stop_experiment(self, experiment_id: str) -> bool:
        """Stop an experiment"""
        experiment = self.database.get_experiment(experiment_id)
        if not experiment:
            return False
        
        experiment.status = ExperimentStatus.STOPPED
        experiment.ended_at = datetime.utcnow()
        
        self.database.save_experiment(experiment)
        
        if experiment_id in self.running_experiments:
            del self.running_experiments[experiment_id]
        
        logger.info(f"Stopped experiment: {experiment_id}")
        return True
    
    def get_user_variant(self, user_id: str, experiment_id: str) -> Variant | None:
        """Get the variant for a user in an experiment"""
        experiment = self.database.get_experiment(experiment_id)
        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            return None
        
        return self.traffic_splitter.assign_user_to_variant(user_id, experiment)
    
    def track_conversion(self, user_id: str, experiment_id: str, 
                        metric_values: dict[str, float] = None) -> bool:
        """Track conversion for a user"""
        
        # Get variant assignment
        variant_id = self.traffic_splitter.get_user_variant(user_id, experiment_id)
        if not variant_id:
            return False
        
        # Create assignment
        assignment = UserAssignment(
            user_id=user_id,
            experiment_id=experiment_id,
            variant_id=variant_id,
            assigned_at=datetime.utcnow(),
            converted=True,
            conversion_value=metric_values.get('revenue', 0.0) if metric_values else 0.0,
            metrics=metric_values or {}
        )
        
        # Save assignment
        self.database.save_user_assignment(assignment)
        
        return True
    
    def analyze_experiment(self, experiment_id: str) -> ExperimentResult | None:
        """Analyze an experiment and generate results"""
        
        experiment = self.database.get_experiment(experiment_id)
        if not experiment:
            return None
        
        # Get all assignments
        assignments = self.database.get_user_assignments(experiment_id)
        
        if not assignments:
            return ExperimentResult(
                experiment_id=experiment_id,
                variant_results={},
                statistical_tests={},
                recommendation="No data available"
            )
        
        # Group assignments by variant
        variant_data = {}
        for variant in experiment.variants:
            variant_data[variant.variant_id] = {
                'assignments': [],
                'conversions': 0,
                'conversion_values': [],
                'metrics': {}
            }
        
        for assignment in assignments:
            if assignment.variant_id in variant_data:
                variant_data[assignment.variant_id]['assignments'].append(assignment)
                
                if assignment.converted:
                    variant_data[assignment.variant_id]['conversions'] += 1
                    variant_data[assignment.variant_id]['conversion_values'].append(assignment.conversion_value)
                
                # Aggregate metrics
                for metric_name, value in (assignment.metrics or {}).items():
                    if metric_name not in variant_data[assignment.variant_id]['metrics']:
                        variant_data[assignment.variant_id]['metrics'][metric_name] = []
                    variant_data[assignment.variant_id]['metrics'][metric_name].append(value)
        
        # Analyze each metric
        variant_results = {}
        statistical_tests = {}
        
        for metric in experiment.metrics:
            metric_name = metric.name
            
            # Get control and treatment data
            control_variant = None
            treatment_variants = []
            
            for variant in experiment.variants:
                if variant.type == VariantType.CONTROL:
                    control_variant = variant
                else:
                    treatment_variants.append(variant)
            
            if not control_variant or not treatment_variants:
                continue
            
            control_data = variant_data[control_variant.variant_id]
            
            for treatment_variant in treatment_variants:
                treatment_data = variant_data[treatment_variant.variant_id]
                
                # Analyze based on metric type
                if metric.type == MetricType.CONVERSION:
                    # Conversion rate analysis
                    result = self.analyzer.analyze_conversion(
                        control_data['conversions'],
                        len(control_data['assignments']),
                        treatment_data['conversions'],
                        len(treatment_data['assignments']),
                        experiment.confidence_level
                    )
                elif metric.type == MetricType.REVENUE:
                    # Revenue analysis (continuous)
                    result = self.analyzer.analyze_continuous_metric(
                        control_data['conversion_values'],
                        treatment_data['conversion_values'],
                        experiment.confidence_level
                    )
                else:
                    # Other continuous metrics
                    control_metric_values = control_data['metrics'].get(metric_name, [])
                    treatment_metric_values = treatment_data['metrics'].get(metric_name, [])
                    
                    if control_metric_values and treatment_metric_values:
                        result = self.analyzer.analyze_continuous_metric(
                            control_metric_values,
                            treatment_metric_values,
                            experiment.confidence_level
                        )
                    else:
                        continue
                
                # Store results
                variant_key = f"{metric_name}_{treatment_variant.variant_id}"
                variant_results[variant_key] = result
                statistical_tests[variant_key] = result
        
        # Determine winner
        winner = None
        confidence = 0.0
        recommendation = ""
        
        # Simple winner determination (could be more sophisticated)
        significant_results = [
            (key, result) for key, result in statistical_tests.items()
            if result.get('is_significant', False)
        ]
        
        if significant_results:
            # Find the best performing variant
            best_result = max(significant_results, key=lambda x: x[1].get('relative_improvement', 0))
            best_key = best_result[0]
            
            # Extract variant ID from key
            parts = best_key.split('_')
            metric_name = '_'.join(parts[:-1])
            variant_id = parts[-1]
            
            winner = variant_id
            confidence = 1.0 - best_result[1].get('p_value', 1.0)
            recommendation = f"{metric_name}: {best_result[1].get('relative_improvement', 0):.2%} improvement (p={best_result[1].get('p_value', 1.0):.3f})"
        
        return ExperimentResult(
            experiment_id=experiment_id,
            variant_results=variant_results,
            statistical_tests=statistical_tests,
            winner=winner,
            confidence=confidence,
            recommendation=recommendation
        )


# Example usage
async def example_usage():
    """Example of A/B testing usage"""
    
    # Initialize experiment runner
    runner = ExperimentRunner()
    
    # Create an experiment
    experiment = runner.create_experiment(
        name="Idea Generation UI Test",
        description="Test different UI layouts for idea generation",
        hypothesis="The new UI layout will increase idea generation conversion rate by 10%",
        variants=[
            {
                "name": "Current UI",
                "type": "control",
                "configuration": {"layout": "current", "colors": "blue"},
                "traffic_allocation": 0.5
            },
            {
                "name": "New UI",
                "type": "treatment",
                "configuration": {"layout": "new", "colors": "green"},
                "traffic_allocation": 0.5
            }
        ],
        metrics=[
            {
                "name": "idea_generation_conversion",
                "type": "conversion",
                "description": "Users who generate at least one idea",
                "unit": "percentage",
                "higher_is_better": True,
                "target_improvement": 0.10
            },
            {
                "name": "user_satisfaction",
                "type": "engagement",
                "description": "User satisfaction score",
                "unit": "score",
                "higher_is_better": True,
                "target_improvement": 0.05
            }
        ]
    )
    
    print(f"Created experiment: {experiment.experiment_id}")
    
    # Start the experiment
    runner.start_experiment(experiment.experiment_id)
    
    # Simulate user traffic
    for i in range(100):
        user_id = f"user_{i}"
        
        # Get variant for user
        variant = runner.get_user_variant(user_id, experiment.experiment_id)
        
        if variant:
            print(f"User {user_id} assigned to {variant.name}")
            
            # Simulate conversion (50% chance)
            if random.random() < 0.5:
                metric_values = {
                    "user_satisfaction": random.uniform(3.0, 5.0)
                }
                runner.track_conversion(user_id, experiment.experiment_id, metric_values)
    
    # Analyze results
    results = runner.analyze_experiment(experiment.experiment_id)
    
    print(f"Experiment Results:")
    print(f"Winner: {results.winner}")
    print(f"Confidence: {results.confidence:.2f}")
    print(f"Recommendation: {results.recommendation}")
    
    # Stop experiment
    runner.stop_experiment(experiment.experiment_id)


if __name__ == "__main__":
    asyncio.run(example_usage())
