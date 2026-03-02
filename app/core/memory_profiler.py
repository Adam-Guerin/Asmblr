"""
Memory Profiler for Asmblr
Tracks memory usage and identifies optimization opportunities
"""

import psutil
import time
import tracemalloc
import threading
from typing import Dict, List, Any
from collections import defaultdict
from loguru import logger

class MemoryProfiler:
    """Advanced memory profiling and optimization"""
    
    def __init__(self, sample_interval: int = 5):
        self.sample_interval = sample_interval
        self.process = psutil.Process()
        self.memory_samples = []
        self.peak_memory = 0
        self.memory_leaks = defaultdict(list)
        self._profiling = False
        self._thread = None
        
        # Start tracemalloc for detailed tracking
        tracemalloc.start()
        
    def start_profiling(self):
        """Start memory profiling"""
        if self._profiling:
            return
        
        self._profiling = True
        self._thread = threading.Thread(target=self._profile_loop, daemon=True)
        self._thread.start()
        logger.info("Memory profiling started")
        
    def stop_profiling(self):
        """Stop memory profiling"""
        self._profiling = False
        if self._thread:
            self._thread.join()
        logger.info("Memory profiling stopped")
        
    def _profile_loop(self):
        """Main profiling loop"""
        while self._profiling:
            try:
                # Get current memory usage
                memory_info = self.process.memory_info()
                current_memory = memory_info.rss / (1024 * 1024)  # MB
                
                self.memory_samples.append({
                    'timestamp': time.time(),
                    'rss_mb': current_memory,
                    'vms_mb': memory_info.vms / (1024 * 1024)
                })
                
                # Track peak memory
                if current_memory > self.peak_memory:
                    self.peak_memory = current_memory
                
                # Get tracemalloc snapshot every 10 samples
                if len(self.memory_samples) % 10 == 0:
                    self._capture_memory_snapshot()
                
                time.sleep(self.sample_interval)
                
            except Exception as e:
                logger.error(f"Memory profiling error: {e}")
                time.sleep(self.sample_interval)
    
    def _capture_memory_snapshot(self):
        """Capture detailed memory snapshot"""
        try:
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            
            # Track top memory consumers
            for stat in top_stats[:5]:
                self.memory_leaks[str(stat.traceback)].append(stat.size)
                
        except Exception as e:
            logger.error(f"Memory snapshot error: {e}")
    
    def get_memory_report(self) -> Dict[str, Any]:
        """Generate comprehensive memory report"""
        if not self.memory_samples:
            return {}
        
        # Calculate statistics
        memory_values = [sample['rss_mb'] for sample in self.memory_samples]
        
        report = {
            'total_samples': len(memory_values),
            'peak_memory_mb': self.peak_memory,
            'avg_memory_mb': sum(memory_values) / len(memory_values),
            'min_memory_mb': min(memory_values),
            'max_memory_mb': max(memory_values),
            'memory_growth_mb': memory_values[-1] - memory_values[0] if len(memory_values) > 1 else 0,
            'top_memory_consumers': self._get_top_consumers()
        }
        
        # Detect potential memory leaks
        if report['memory_growth_mb'] > 100:  # 100MB growth
            report['potential_leak'] = True
            report['leak_recommendation'] = "Review code for memory leaks"
        
        return report
    
    def _get_top_consumers(self) -> List[Dict[str, Any]]:
        """Get top memory consuming code locations"""
        consumers = []
        
        for location, sizes in self.memory_leaks.items():
            if sizes:
                avg_size = sum(sizes) / len(sizes)
                consumers.append({
                    'location': location,
                    'avg_size_mb': avg_size / (1024 * 1024),
                    'max_size_mb': max(sizes) / (1024 * 1024),
                    'samples': len(sizes)
                })
        
        # Sort by average size
        consumers.sort(key=lambda x: x['avg_size_mb'], reverse=True)
        return consumers[:10]
    
    def optimize_memory_usage(self):
        """Suggest memory optimizations"""
        report = self.get_memory_report()
        suggestions = []
        
        if report.get('peak_memory_mb', 0) > 2048:  # > 2GB
            suggestions.append({
                'issue': 'High memory usage',
                'suggestion': 'Enable lazy loading for ML libraries',
                'priority': 'high'
            })
        
        if report.get('memory_growth_mb', 0) > 500:  # > 500MB growth
            suggestions.append({
                'issue': 'Memory growth detected',
                'suggestion': 'Check for memory leaks in long-running processes',
                'priority': 'high'
            })
        
        # Check top consumers
        for consumer in report.get('top_memory_consumers', []):
            if consumer['avg_size_mb'] > 100:  # > 100MB
                suggestions.append({
                    'issue': f'High memory usage in {consumer["location"]}',
                    'suggestion': 'Optimize algorithm or use generators',
                    'priority': 'medium'
                })
        
        return suggestions

# Global profiler instance
_profiler: MemoryProfiler = None

def get_memory_profiler() -> MemoryProfiler:
    """Get global memory profiler"""
    global _profiler
    if _profiler is None:
        _profiler = MemoryProfiler()
    return _profiler
