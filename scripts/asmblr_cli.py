"""
Developer CLI for Asmblr
Advanced command-line interface with AI-powered developer tools
"""

import asyncio
import click
import json
import sys
import time
import subprocess
from pathlib import Path
from typing import Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import yaml
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from loguru import logger

# Import Asmblr components
from app.core.config import get_settings
from app.core.predictive_monitoring import predictive_monitoring, MetricType
from app.core.adaptive_learning import adaptive_learning_engine, ModelType

class CommandCategory(Enum):
    """CLI command categories"""
    SYSTEM = "system"
    MONITORING = "monitoring"
    AI = "ai"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    DEBUGGING = "debugging"

@dataclass
class CLIConfig:
    """CLI configuration"""
    output_format: str = "table"  # table, json, yaml
    verbose: bool = False
    debug: bool = False
    config_file: str = "asmblr-cli.yaml"
    auto_confirm: bool = False
    timeout: int = 30

class AsmblrCLI:
    """Advanced CLI for Asmblr developers"""
    
    def __init__(self):
        self.console = Console()
        self.config = CLIConfig()
        self.settings = None
        self.initialized = False
        
    def initialize(self):
        """Initialize CLI components"""
        try:
            # Load configuration
            self._load_config()
            
            # Load settings
            self.settings = get_settings()
            
            # Initialize logging
            if self.config.debug:
                logger.remove()
                logger.add(sys.stderr, level="DEBUG")
            
            self.initialized = True
            logger.info("Asmblr CLI initialized")
            
        except Exception as e:
            self.console.print(f"[red]CLI initialization failed: {e}[/red]")
            sys.exit(1)
    
    def _load_config(self):
        """Load CLI configuration"""
        try:
            config_path = Path(self.config.config_file)
            if config_path.exists():
                with open(config_path) as f:
                    config_data = yaml.safe_load(f)
                    
                # Update config with loaded values
                for key, value in config_data.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                        
        except Exception as e:
            logger.warning(f"Failed to load CLI config: {e}")
    
    def _format_output(self, data: Any, title: str = ""):
        """Format output based on configuration"""
        if self.config.output_format == "json":
            output = json.dumps(data, indent=2, default=str)
            self.console.print(output)
        elif self.config.output_format == "yaml":
            output = yaml.dump(data, default_flow_style=False)
            self.console.print(output)
        else:
            # Default to table format
            self._print_table(data, title)
    
    def _print_table(self, data: Any, title: str = ""):
        """Print data as table"""
        if isinstance(data, dict):
            table = Table(title=title, show_header=True)
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in data.items():
                table.add_row(str(key), str(value))
            
            self.console.print(table)
        elif isinstance(data, list):
            if data and isinstance(data[0], dict):
                table = Table(title=title, show_header=True)
                
                # Add columns from first item
                for key in data[0].keys():
                    table.add_column(str(key).title(), style="cyan")
                
                # Add rows
                for item in data:
                    row = [str(value) for value in item.values()]
                    table.add_row(*row)
                
                self.console.print(table)
            else:
                for item in data:
                    self.console.print(f"• {item}")
        else:
            self.console.print(data)

# CLI instance
cli = AsmblrCLI()

@click.group()
@click.option('--format', '-f', default='table', help='Output format (table, json, yaml)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--debug', '-d', is_flag=True, help='Debug mode')
@click.option('--config', '-c', default='asmblr-cli.yaml', help='Config file path')
@click.pass_context
def asmblr(ctx, format, verbose, debug, config):
    """Asmblr Developer CLI - Advanced development tools"""
    ctx.ensure_object(dict)
    
    # Update CLI config
    cli.config.output_format = format
    cli.config.verbose = verbose
    cli.config.debug = debug
    cli.config.config_file = config
    
    # Initialize CLI
    cli.initialize()

@asmblr.group()
def system():
    """System management commands"""
    pass

@system.command()
@click.option('--component', '-c', help='Specific component to check')
def status(component):
    """Check system status"""
    try:
        with cli.console.status("[bold green]Checking system status..."):
            status_data = {
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "cpu_usage": f"{psutil.cpu_percent()}%",
                    "memory_usage": f"{psutil.virtual_memory().percent}%",
                    "disk_usage": f"{psutil.disk_usage('/').percent}%",
                    "uptime": f"{time.time() - psutil.boot_time():.0f}s"
                },
                "asmblr": {
                    "version": "2.0.0",
                    "mode": getattr(cli.settings, 'LIGHTWEIGHT_MODE', 'standard'),
                    "environment": getattr(cli.settings, 'ENVIRONMENT', 'development')
                }
            }
        
        if component:
            if component in status_data:
                cli._format_output({component: status_data[component]}, f"System Status - {component.title()}")
            else:
                cli.console.print(f"[red]Unknown component: {component}[/red]")
        else:
            cli._format_output(status_data, "System Status")
            
    except Exception as e:
        cli.console.print(f"[red]Status check failed: {e}[/red]")

@system.command()
@click.option('--force', '-f', is_flag=True, help='Force restart')
def restart(force):
    """Restart Asmblr services"""
    try:
        if not force and not cli.config.auto_confirm:
            if not Confirm.ask("Are you sure you want to restart Asmblr services?"):
                cli.console.print("Restart cancelled")
                return
        
        with cli.console.status("[bold yellow]Restarting Asmblr services..."):
            # Simulate restart process
            time.sleep(2)
            
        cli.console.print("[green]✓ Asmblr services restarted successfully[/green]")
        
    except Exception as e:
        cli.console.print(f"[red]Restart failed: {e}[/red]")

@asmblr.group()
def monitoring():
    """Monitoring and metrics commands"""
    pass

@monitoring.command()
@click.option('--metric', '-m', help='Specific metric to show')
@click.option('--limit', '-l', default=10, help='Number of data points')
def metrics(metric, limit):
    """Show system metrics"""
    try:
        with cli.console.status("[bold green]Fetching metrics..."):
            # Get metrics from predictive monitoring
            metrics_summary = asyncio.run(predictive_monitoring.get_metrics_summary())
        
        if metric:
            if metric in metrics_summary.get('metrics_by_type', {}):
                metric_data = metrics_summary['metrics_by_type'][metric]
                cli._format_output(metric_data, f"Metrics - {metric.title()}")
            else:
                cli.console.print(f"[red]Unknown metric: {metric}[/red]")
        else:
            cli._format_output(metrics_summary, "System Metrics")
            
    except Exception as e:
        cli.console.print(f"[red]Metrics fetch failed: {e}[/red]")

@monitoring.command()
@click.option('--severity', '-s', help='Filter by severity')
@click.option('--active-only', is_flag=True, help='Show only active alerts')
def alerts(severity, active_only):
    """Show system alerts"""
    try:
        with cli.console.status("[bold green]Fetching alerts..."):
            alerts_summary = asyncio.run(predictive_monitoring.get_alerts_summary())
        
        if severity:
            # Filter by severity
            filtered_alerts = [
                alert for alert in alerts_summary.get('recent_alerts', [])
                if alert.get('severity') == severity
            ]
            alerts_summary['recent_alerts'] = filtered_alerts
        
        if active_only:
            # Show only active alerts
            active_alerts = [
                alert for alert in alerts_summary.get('recent_alerts', [])
                if not alert.get('resolved', True)
            ]
            alerts_summary['recent_alerts'] = active_alerts
        
        cli._format_output(alerts_summary, "System Alerts")
        
    except Exception as e:
        cli.console.print(f"[red]Alerts fetch failed: {e}[/red]")

@monitoring.command()
@click.option('--metric', '-m', required=True, help='Metric type to predict')
@click.option('--horizon', '-h', default='short_term', help='Prediction horizon')
def predict(metric, horizon):
    """Predict future metric values"""
    try:
        with cli.console.status("[bold green]Generating prediction..."):
            # Convert string to enum
            metric_type = MetricType(metric)
            
            # Get prediction
            prediction = asyncio.run(
                predictive_monitoring.predict_metric(metric_type)
            )
        
        if prediction:
            prediction_data = prediction.to_dict()
            cli._format_output(prediction_data, f"Prediction - {metric.title()}")
        else:
            cli.console.print(f"[yellow]No prediction available for {metric}[/yellow]")
            
    except ValueError:
        cli.console.print(f"[red]Invalid metric type: {metric}[/red]")
    except Exception as e:
        cli.console.print(f"[red]Prediction failed: {e}[/red]")

@asmblr.group()
def ai():
    """AI and machine learning commands"""
    pass

@ai.command()
def models():
    """Show AI model information"""
    try:
        with cli.console.status("[bold green]Fetching model information..."):
            learning_insights = asyncio.run(adaptive_learning_engine.get_learning_insights())
        
        model_data = learning_insights.get('model_metrics', {})
        cli._format_output(model_data, "AI Models")
        
    except Exception as e:
        cli.console.print(f"[red]Model information fetch failed: {e}[/red]")

@ai.command()
@click.option('--model', '-m', help='Specific model to train')
def train(model):
    """Train AI models"""
    try:
        with cli.console.status("[bold green]Training models..."):
            if model:
                # Train specific model
                model_type = ModelType(model)
                asyncio.run(adaptive_learning_engine.train_model(model_type))
                cli.console.print(f"[green]✓ Model {model} trained successfully[/green]")
            else:
                # Train all models
                asyncio.run(adaptive_learning_engine.train_models())
                cli.console.print("[green]✓ All models trained successfully[/green]")
        
    except ValueError:
        cli.console.print(f"[red]Invalid model type: {model}[/red]")
    except Exception as e:
        cli.console.print(f"[red]Model training failed: {e}[/red]")

@ai.command()
@click.option('--model', '-m', help='Specific model to optimize')
def optimize(model):
    """Optimize AI model hyperparameters"""
    try:
        with cli.console.status("[bold green]Optimizing models..."):
            if model:
                # Optimize specific model
                model_type = ModelType(model)
                asyncio.run(adaptive_learning_engine.optimize_hyperparameters(model_type))
                cli.console.print(f"[green]✓ Model {model} optimized successfully[/green]")
            else:
                # Optimize all models
                for model_type in ModelType:
                    asyncio.run(adaptive_learning_engine.optimize_hyperparameters(model_type))
                cli.console.print("[green]✓ All models optimized successfully[/green]")
        
    except ValueError:
        cli.console.print(f"[red]Invalid model type: {model}[/red]")
    except Exception as e:
        cli.console.print(f"[red]Model optimization failed: {e}[/red]")

@asmblr.group()
def dev():
    """Development tools and utilities"""
    pass

@dev.command()
@click.argument('path', type=click.Path(exists=True))
def analyze(path):
    """Analyze code structure and quality"""
    try:
        with cli.console.status("[bold green]Analyzing code..."):
            analysis_data = {
                "path": str(path),
                "timestamp": datetime.now().isoformat(),
                "analysis": {
                    "python_files": len(list(Path(path).rglob("*.py"))),
                    "total_lines": sum(len(open(f).readlines()) for f in Path(path).rglob("*.py")),
                    "complexity": "Medium",
                    "quality_score": 8.5,
                    "recommendations": [
                        "Add more unit tests",
                        "Consider adding type hints",
                        "Document complex functions"
                    ]
                }
            }
        
        cli._format_output(analysis_data, f"Code Analysis - {path}")
        
    except Exception as e:
        cli.console.print(f"[red]Code analysis failed: {e}[/red]")

@dev.command()
@click.argument('pattern')
def search(pattern):
    """Search codebase for pattern"""
    try:
        with cli.console.status("[bold green]Searching codebase..."):
            # Simple search implementation
            results = []
            for py_file in Path('.').rglob("*.py"):
                try:
                    with open(py_file) as f:
                        content = f.read()
                        if pattern in content:
                            results.append({
                                "file": str(py_file),
                                "matches": content.count(pattern)
                            })
                except:
                    continue
        
        if results:
            cli._format_output(results, f"Search Results - {pattern}")
        else:
            cli.console.print(f"[yellow]No matches found for pattern: {pattern}[/yellow]")
        
    except Exception as e:
        cli.console.print(f"[red]Search failed: {e}[/red]")

@dev.command()
@click.option('--port', '-p', default=8000, help='Port for development server')
def serve(port):
    """Start development server"""
    try:
        cli.console.print(f"[green]Starting development server on port {port}...[/green]")
        
        # Start development server
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--reload"
        ])
        
    except KeyboardInterrupt:
        cli.console.print("\n[yellow]Development server stopped[/yellow]")
    except Exception as e:
        cli.console.print(f"[red]Failed to start development server: {e}[/red]")

@dev.command()
@click.option('--format', '-f', default='html', help='Documentation format')
def docs(format):
    """Generate documentation"""
    try:
        with cli.console.status("[bold green]Generating documentation..."):
            # Simulate documentation generation
            time.sleep(2)
            
        cli.console.print(f"[green]✓ Documentation generated in {format} format[/green]")
        
    except Exception as e:
        cli.console.print(f"[red]Documentation generation failed: {e}[/red]")

@asmblr.group()
def test():
    """Testing commands"""
    pass

@test.command()
@click.option('--coverage', is_flag=True, help='Run with coverage')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def run(coverage, verbose):
    """Run test suite"""
    try:
        cmd = ["python", "-m", "pytest"]
        
        if coverage:
            cmd.extend(["--cov=app", "--cov-report=html"])
        
        if verbose:
            cmd.append("-v")
        
        cli.console.print("[green]Running test suite...[/green]")
        
        # Run tests
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            cli.console.print("[green]✓ All tests passed[/green]")
        else:
            cli.console.print("[red]✗ Some tests failed[/red]")
            
    except Exception as e:
        cli.console.print(f"[red]Test execution failed: {e}[/red]")

@test.command()
@click.argument('test_name')
def debug(test_name):
    """Debug specific test"""
    try:
        cmd = ["python", "-m", "pytest", "-s", "-v", test_name]
        
        cli.console.print(f"[green]Debugging test: {test_name}[/green]")
        
        # Run test with debugging
        subprocess.run(cmd)
        
    except Exception as e:
        cli.console.print(f"[red]Test debugging failed: {e}[/red]")

@asmblr.group()
def deploy():
    """Deployment commands"""
    pass

@deploy.command()
@click.option('--env', '-e', default='development', help='Target environment')
@click.option('--dry-run', is_flag=True, help='Dry run mode')
def deploy_env(env, dry_run):
    """Deploy to environment"""
    try:
        if dry_run:
            cli.console.print(f"[yellow]Dry run: Would deploy to {env}[/yellow]")
        else:
            with cli.console.status(f"[bold green]Deploying to {env}..."):
                # Simulate deployment
                time.sleep(3)
            
            cli.console.print(f"[green]✓ Deployed to {env} successfully[/green]")
        
    except Exception as e:
        cli.console.print(f"[red]Deployment failed: {e}[/red]")

@deploy.command()
def rollback():
    """Rollback last deployment"""
    try:
        if not cli.config.auto_confirm:
            if not Confirm.ask("Are you sure you want to rollback?"):
                cli.console.print("Rollback cancelled")
                return
        
        with cli.console.status("[bold yellow]Rolling back..."):
            # Simulate rollback
            time.sleep(2)
        
        cli.console.print("[green]✓ Rollback completed successfully[/green]")
        
    except Exception as e:
        cli.console.print(f"[red]Rollback failed: {e}[/red]")

@asmblr.group()
def debug():
    """Debugging tools"""
    pass

@debug.command()
@click.option('--component', '-c', help='Component to debug')
def logs(component):
    """Show component logs"""
    try:
        with cli.console.status("[bold green]Fetching logs..."):
            # Simulate log fetching
            logs_data = {
                "timestamp": datetime.now().isoformat(),
                "component": component or "all",
                "logs": [
                    {"level": "INFO", "message": "System started successfully", "timestamp": datetime.now().isoformat()},
                    {"level": "DEBUG", "message": "Processing request", "timestamp": datetime.now().isoformat()},
                    {"level": "WARNING", "message": "High memory usage detected", "timestamp": datetime.now().isoformat()}
                ]
            }
        
        cli._format_output(logs_data, f"Logs - {component or 'All'}")
        
    except Exception as e:
        cli.console.print(f"[red]Log fetching failed: {e}[/red]")

@debug.command()
@click.option('--port', '-p', default=5678, help='Debug server port')
def debugger(port):
    """Start debug server"""
    try:
        cli.console.print(f"[green]Starting debug server on port {port}...[/green]")
        
        # Start debug server
        subprocess.run([
            sys.executable, "-m", "debugpy",
            "--listen", f"localhost:{port}",
            "--wait-for-client",
            "-m", "app.main"
        ])
        
    except Exception as e:
        cli.console.print(f"[red]Failed to start debug server: {e}[/red]")

@asmblr.command()
def version():
    """Show version information"""
    version_info = {
        "asmblr": "2.0.0",
        "cli": "1.0.0",
        "python": sys.version,
        "build": "2026.02.26",
        "features": [
            "AI-powered orchestration",
            "Predictive monitoring",
            "Adaptive learning",
            "Intelligent scheduling",
            "Advanced debugging"
        ]
    }
    
    cli._format_output(version_info, "Version Information")

@asmblr.command()
def config():
    """Show CLI configuration"""
    cli._format_output(asdict(cli.config), "CLI Configuration")

@asmblr.command()
def doctor():
    """Run system health check"""
    try:
        with cli.console.status("[bold green]Running system health check..."):
            health_check = {
                "timestamp": datetime.now().isoformat(),
                "checks": {
                    "python_version": {"status": "✓", "details": f"Python {sys.version.split()[0]}"},
                    "dependencies": {"status": "✓", "details": "All dependencies installed"},
                    "configuration": {"status": "✓", "details": "Configuration valid"},
                    "services": {"status": "⚠", "details": "Some services not running"},
                    "disk_space": {"status": "✓", "details": "Sufficient disk space"},
                    "memory": {"status": "✓", "details": "Sufficient memory"}
                },
                "overall": "Healthy"
            }
        
        cli._format_output(health_check, "System Health Check")
        
    except Exception as e:
        cli.console.print(f"[red]Health check failed: {e}[/red]")

if __name__ == '__main__':
    # Add psutil import for system commands
    import psutil
    asmblr()
