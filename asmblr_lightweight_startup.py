#!/usr/bin/env python3
"""
Lightweight Startup Script for Asmblr
Optimizes memory usage and startup time
"""

import os
import sys
from pathlib import Path

# Set performance environment variables
os.environ["LIGHTWEIGHT_MODE"] = "true"
os.environ["PYTHONOPTIMIZE"] = "2"  # Enable Python optimizations
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"  # Skip bytecode creation

# Limit memory usage (if psutil available)
try:
    import psutil
    import resource
    
    # Set memory limit to 2GB
    memory_limit = 2 * 1024 * 1024 * 1024  # 2GB in bytes
    resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
except ImportError:
    pass

# Import lazy loading first
from app.core.lazy_loader import preload_essentials
preload_essentials()

# Import optimized config
from app.core.config import get_settings

def main():
    """Lightweight main entry point"""
    print("[START] Starting Asmblr in lightweight mode...")
    
    # Load settings with performance optimizations
    settings = get_settings()
    
    # Start resource monitoring
    from app.core.resource_monitor import get_resource_monitor
    monitor = get_resource_monitor()
    monitor.start_monitoring(interval=30)
    
    # Start with minimal services
    from app.cli import main as cli_main
    
    try:
        cli_main()
    finally:
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()
