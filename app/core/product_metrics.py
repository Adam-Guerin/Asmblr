"""Product metrics tracking and dashboard for Asmblr."""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

class RunMetrics(TypedDict):
    """Metrics for a single run."""
    run_id: str
    created_at: float
    idea_to_landing_days: Optional[float]  # Temps en jours entre idée et landing
    mvp_published: bool
    has_feedback: bool
    feedback_count: int
    iterations_after_feedback: int
    last_updated: float

class ProductMetrics:
    """Track and manage product metrics for Asmblr."""
    
    def __init__(self, data_dir: Path):
        """Initialize with path to data directory."""
        self.data_dir = data_dir
        self.metrics_file = data_dir / "product_metrics.json"
        self._runs: Dict[str, RunMetrics] = {}
        self._load_metrics()
    
    def _load_metrics(self) -> None:
        """Load metrics from JSON file."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._runs = {run['run_id']: run for run in data.get('runs', [])}
            except (json.JSONDecodeError, KeyError):
                self._runs = {}
        
    def _save_metrics(self) -> None:
        """Save metrics to JSON file."""
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump({'runs': list(self._runs.values())}, f, indent=2)
    
    def record_run_start(self, run_id: str) -> None:
        """Record when a new run is started."""
        now = time.time()
        if run_id not in self._runs:
            self._runs[run_id] = {
                'run_id': run_id,
                'created_at': now,
                'idea_to_landing_days': None,
                'mvp_published': False,
                'has_feedback': False,
                'feedback_count': 0,
                'iterations_after_feedback': 0,
                'last_updated': now
            }
            self._save_metrics()
    
    def record_landing_created(self, run_id: str) -> None:
        """Record when a landing page is created for a run."""
        if run_id in self._runs and self._runs[run_id]['idea_to_landing_days'] is None:
            time_diff = (time.time() - self._runs[run_id]['created_at']) / (24 * 3600)
            self._runs[run_id]['idea_to_landing_days'] = round(time_diff, 2)
            self._runs[run_id]['last_updated'] = time.time()
            self._save_metrics()
    
    def record_mvp_published(self, run_id: str) -> None:
        """Record when an MVP is published."""
        if run_id in self._runs and not self._runs[run_id]['mvp_published']:
            self._runs[run_id]['mvp_published'] = True
            self._runs[run_id]['last_updated'] = time.time()
            self._save_metrics()
    
    def record_feedback(self, run_id: str, feedback_count: int = 1) -> None:
        """Record user feedback for a run."""
        if run_id in self._runs:
            self._runs[run_id]['has_feedback'] = True
            self._runs[run_id]['feedback_count'] += feedback_count
            self._runs[run_id]['last_updated'] = time.time()
            self._save_metrics()
    
    def record_iteration(self, run_id: str) -> None:
        """Record an iteration after feedback."""
        if run_id in self._runs:
            self._runs[run_id]['iterations_after_feedback'] += 1
            self._runs[run_id]['last_updated'] = time.time()
            self._save_metrics()
    
    def record_user_feedback(self, run_id: str, feedback_count: int = 1) -> None:
        """Record user feedback for a run."""
        if run_id in self._runs:
            self._runs[run_id]['has_feedback'] = True
            self._runs[run_id]['feedback_count'] += feedback_count
            self._runs[run_id]['last_updated'] = time.time()
            self._save_metrics()
    
    def record_manual_mvp_publication(self, run_id: str) -> None:
        """Manually record MVP publication (for cases where MVP is published outside pipeline)."""
        if run_id in self._runs and not self._runs[run_id]['mvp_published']:
            self._runs[run_id]['mvp_published'] = True
            self._runs[run_id]['last_updated'] = time.time()
            self._save_metrics()
    
    def get_dashboard_metrics(self, days: int = 30) -> dict:
        """Calculate and return dashboard metrics."""
        now = time.time()
        time_threshold = now - (days * 24 * 3600)
        
        recent_runs = [
            run for run in self._runs.values() 
            if run['created_at'] >= time_threshold
        ]
        
        if not recent_runs:
            return {
                'runs_count': 0,
                'mvp_published_pct': 0,
                'avg_idea_to_landing_days': 0,
                'runs_with_feedback_pct': 0,
                'runs_with_iterations_pct': 0,
                'last_updated': now
            }
        
        # Calculate metrics
        runs_count = len(recent_runs)
        mvp_published = sum(1 for r in recent_runs if r['mvp_published'])
        
        landing_times = [r['idea_to_landing_days'] for r in recent_runs 
                        if r['idea_to_landing_days'] is not None]
        avg_landing_time = round(sum(landing_times) / len(landing_times), 1) if landing_times else 0
        
        runs_with_feedback = sum(1 for r in recent_runs if r['has_feedback'])
        runs_with_iterations = sum(1 for r in recent_runs if r['iterations_after_feedback'] > 0)
        
        return {
            'runs_count': runs_count,
            'mvp_published_pct': round((mvp_published / runs_count) * 100, 1) if runs_count else 0,
            'avg_idea_to_landing_days': avg_landing_time,
            'runs_with_feedback_pct': round((runs_with_feedback / runs_count) * 100, 1) if runs_count else 0,
            'runs_with_iterations_pct': round((runs_with_iterations / runs_count) * 100, 1) if runs_count else 0,
            'last_updated': now
        }

# Global instance
PRODUCT_METRICS = None

def init_product_metrics(data_dir: Path) -> None:
    """Initialize the global product metrics instance."""
    global PRODUCT_METRICS
    PRODUCT_METRICS = ProductMetrics(data_dir)
