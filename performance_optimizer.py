#!/usr/bin/env python3
"""
Performance Optimizer for Asmblr Phase 3
Optimizes application performance, response times, and resource usage
"""

import os
import time
import json
import psutil
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess
import sys

class PerformanceOptimizer:
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.metrics = {}
        
    def analyze_system_resources(self) -> Dict:
        """Analyze current system resource usage"""
        return {
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_total': psutil.virtual_memory().total / (1024**3),  # GB
            'memory_available': psutil.virtual_memory().available / (1024**3),  # GB
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_connections': len(psutil.net_connections())
        }
    
    def optimize_python_imports(self) -> Dict:
        """Optimize Python imports for faster startup"""
        optimizations = []
        
        # Check for lazy loading opportunities
        app_files = list(self.root_path.glob('app/**/*.py'))
        
        for file_path in app_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for heavy imports at module level
                heavy_imports = ['tensorflow', 'torch', 'transformers', 'crewai', 'langchain']
                
                for heavy_import in heavy_imports:
                    if f'import {heavy_import}' in content or f'from {heavy_import}' in content:
                        optimizations.append({
                            'file': str(file_path.relative_to(self.root_path)),
                            'issue': f'Heavy import {heavy_import} at module level',
                            'suggestion': 'Move to function-level import or use lazy loading'
                        })
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
        
        return {
            'total_files_analyzed': len(app_files),
            'optimizations_found': len(optimizations),
            'optimizations': optimizations[:10]  # Top 10
        }
    
    def optimize_database_queries(self) -> Dict:
        """Analyze and suggest database query optimizations"""
        optimizations = []
        
        # Look for N+1 query patterns
        app_files = list(self.root_path.glob('app/**/*.py'))
        
        for file_path in app_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines):
                    # Check for query patterns in loops
                    if 'for' in line and ('.query(' in line or '.filter(' in line or '.all()' in line):
                        optimizations.append({
                            'file': str(file_path.relative_to(self.root_path)),
                            'line': i + 1,
                            'issue': 'Potential N+1 query in loop',
                            'code': line.strip(),
                            'suggestion': 'Use eager loading or batch queries'
                        })
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
        
        return {
            'optimizations_found': len(optimizations),
            'optimizations': optimizations[:5]
        }
    
    def optimize_caching_strategy(self) -> Dict:
        """Analyze and suggest caching improvements"""
        cache_opportunities = []
        
        # Look for expensive operations that could be cached
        app_files = list(self.root_path.glob('app/**/*.py'))
        
        for file_path in app_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for API calls without caching
                if 'requests.get(' in content or 'requests.post(' in content:
                    if '@cache' not in content and 'cache' not in content.lower():
                        cache_opportunities.append({
                            'file': str(file_path.relative_to(self.root_path)),
                            'issue': 'API calls without caching',
                            'suggestion': 'Add caching layer for API responses'
                        })
                
                # Check for LLM calls without caching
                if 'llm(' in content or 'chat(' in content:
                    if 'cache' not in content.lower():
                        cache_opportunities.append({
                            'file': str(file_path.relative_to(self.root_path)),
                            'issue': 'LLM calls without caching',
                            'suggestion': 'Implement LLM response caching'
                        })
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
        
        return {
            'cache_opportunities': len(cache_opportunities),
            'recommendations': cache_opportunities[:10]
        }
    
    def create_performance_config(self) -> Dict:
        """Create optimized performance configuration"""
        system_info = self.analyze_system_resources()
        
        # Calculate optimal settings based on system resources
        optimal_settings = {
            'workers': min(4, max(2, system_info['cpu_count'])),
            'max_connections': min(100, max(20, system_info['memory_total'] * 10)),
            'cache_size': min(1024, max(128, system_info['memory_available'] * 100)),  # MB
            'timeout': 30,
            'keepalive': 2,
            'max_requests': 1000,
            'max_requests_jitter': 100,
        }
        
        # Create optimized environment file
        env_content = f"""# Performance Optimized Configuration
# Generated by Performance Optimizer

# Worker Configuration
WORKERS={optimal_settings['workers']}
MAX_CONNECTIONS={optimal_settings['max_connections']}
MAX_REQUESTS={optimal_settings['max_requests']}
MAX_REQUESTS_JITTER={optimal_settings['max_requests_jitter']}

# Timeout Configuration
TIMEOUT={optimal_settings['timeout']}
KEEPALIVE={optimal_settings['keepalive']}

# Cache Configuration
CACHE_SIZE={optimal_settings['cache_size']}
CACHE_TTL=3600
CACHE_TYPE=redis

# Database Configuration
DB_POOL_SIZE={optimal_settings['max_connections'] // 4}
DB_MAX_OVERFLOW={optimal_settings['max_connections'] // 8}
DB_POOL_TIMEOUT=30

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# LLM Configuration
LLM_TIMEOUT=60
LLM_MAX_RETRIES=3
LLM_CACHE_TTL=7200

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30
"""
        
        return {
            'optimal_settings': optimal_settings,
            'env_content': env_content
        }
    
    def benchmark_application(self) -> Dict:
        """Run performance benchmarks"""
        benchmarks = {}
        
        # Test startup time
        start_time = time.time()
        try:
            result = subprocess.run([
                sys.executable, '-c', 
                'import app.core.config; import app.core.models; print("OK")'
            ], capture_output=True, text=True, timeout=30, cwd=self.root_path)
            
            startup_time = time.time() - start_time
            benchmarks['startup_time'] = startup_time
            benchmarks['startup_success'] = result.returncode == 0
        except Exception as e:
            benchmarks['startup_time'] = None
            benchmarks['startup_success'] = False
            benchmarks['startup_error'] = str(e)
        
        # Test memory usage
        try:
            process = psutil.Process()
            benchmarks['memory_usage_mb'] = process.memory_info().rss / (1024**2)
        except:
            benchmarks['memory_usage_mb'] = None
        
        # Test import performance
        import_tests = [
            'app.core.config',
            'app.core.models',
            'app.core.llm',
            'app.cli',
            'app.ui'
        ]
        
        import_times = {}
        for module in import_tests:
            start_time = time.time()
            try:
                result = subprocess.run([
                    sys.executable, '-c', f'import {module}; print("OK")'
                ], capture_output=True, text=True, timeout=10, cwd=self.root_path)
                import_times[module] = time.time() - start_time if result.returncode == 0 else None
            except:
                import_times[module] = None
        
        benchmarks['import_times'] = import_times
        
        return benchmarks
    
    def generate_optimization_report(self) -> str:
        """Generate comprehensive optimization report"""
        system_info = self.analyze_system_resources()
        import_opt = self.optimize_python_imports()
        db_opt = self.optimize_database_queries()
        cache_opt = self.optimize_caching_strategy()
        perf_config = self.create_performance_config()
        benchmarks = self.benchmark_application()
        
        report = []
        report.append("# 🚀 Asmblr Performance Optimization Report")
        report.append(f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # System Analysis
        report.append("## 📊 System Analysis")
        report.append(f"- **CPU Cores**: {system_info['cpu_count']}")
        report.append(f"- **CPU Usage**: {system_info['cpu_percent']:.1f}%")
        report.append(f"- **Memory Total**: {system_info['memory_total']:.1f} GB")
        report.append(f"- **Memory Available**: {system_info['memory_available']:.1f} GB")
        report.append(f"- **Memory Usage**: {system_info['memory_percent']:.1f}%")
        report.append(f"- **Disk Usage**: {system_info['disk_usage']:.1f}%")
        report.append("")
        
        # Performance Benchmarks
        report.append("## ⚡ Performance Benchmarks")
        if benchmarks.get('startup_time'):
            report.append(f"- **Startup Time**: {benchmarks['startup_time']:.2f}s")
        if benchmarks.get('memory_usage_mb'):
            report.append(f"- **Memory Usage**: {benchmarks['memory_usage_mb']:.1f} MB")
        
        report.append("### Import Performance")
        for module, import_time in benchmarks.get('import_times', {}).items():
            if import_time:
                report.append(f"- **{module}**: {import_time:.3f}s")
        report.append("")
        
        # Optimization Recommendations
        report.append("## 🛠️ Optimization Recommendations")
        
        if import_opt['optimizations_found'] > 0:
            report.append("### Python Import Optimizations")
            report.append(f"Found {import_opt['optimizations_found']} opportunities:")
            for opt in import_opt['optimizations'][:3]:
                report.append(f"- **{opt['file']}**: {opt['suggestion']}")
            report.append("")
        
        if db_opt['optimizations_found'] > 0:
            report.append("### Database Query Optimizations")
            report.append(f"Found {db_opt['optimizations_found']} potential N+1 queries")
            report.append("")
        
        if cache_opt['cache_opportunities'] > 0:
            report.append("### Caching Opportunities")
            report.append(f"Found {cache_opt['cache_opportunities']} caching opportunities")
            for rec in cache_opt['recommendations'][:3]:
                report.append(f"- **{rec['file']}**: {rec['suggestion']}")
            report.append("")
        
        # Recommended Configuration
        report.append("## ⚙️ Recommended Configuration")
        report.append("```env")
        report.append(perf_config['env_content'])
        report.append("```")
        report.append("")
        
        # Performance Targets
        report.append("## 🎯 Performance Targets")
        report.append("- **Startup Time**: < 3 seconds")
        report.append("- **Memory Usage**: < 500 MB")
        report.append("- **API Response Time**: < 500ms")
        report.append("- **Database Query Time**: < 100ms")
        report.append("- **Cache Hit Rate**: > 80%")
        report.append("")
        
        # Implementation Priority
        report.append("## 📋 Implementation Priority")
        report.append("### High Priority (Immediate)")
        report.append("1. Apply performance configuration")
        report.append("2. Implement LLM response caching")
        report.append("3. Optimize Python imports")
        report.append("")
        report.append("### Medium Priority (This Week)")
        report.append("1. Database query optimization")
        report.append("2. API response caching")
        report.append("3. Memory usage optimization")
        report.append("")
        report.append("### Low Priority (Next Sprint)")
        report.append("1. Advanced caching strategies")
        report.append("2. Database connection pooling")
        report.append("3. Load testing and optimization")
        
        return "\n".join(report)

def main():
    """Main performance optimization function"""
    root_path = Path(".")
    optimizer = PerformanceOptimizer(root_path)
    
    print("🚀 Starting Performance Optimization...")
    
    # Generate optimization report
    report = optimizer.generate_optimization_report()
    
    # Save report
    report_path = root_path / "PERFORMANCE_OPTIMIZATION_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Create performance configuration
    perf_config = optimizer.create_performance_config()
    env_path = root_path / ".env.performance"
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(perf_config['env_content'])
    
    print(f"\n📊 Performance Analysis Complete!")
    print(f"   📄 Report saved: {report_path}")
    print(f"   ⚙️  Config saved: {env_path}")
    
    # Quick summary
    system_info = optimizer.analyze_system_resources()
    benchmarks = optimizer.benchmark_application()
    
    print(f"\n📈 Quick Summary:")
    print(f"   💾 Memory Available: {system_info['memory_available']:.1f} GB")
    print(f"   🖥️  CPU Usage: {system_info['cpu_percent']:.1f}%")
    if benchmarks.get('startup_time'):
        print(f"   ⚡ Startup Time: {benchmarks['startup_time']:.2f}s")
    
    return 0

if __name__ == "__main__":
    exit(main())
