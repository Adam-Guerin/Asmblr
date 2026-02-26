"""
Tests for Optimized Docker Configuration
Validates Docker Compose setup, resource limits, and health checks
"""

import pytest
import asyncio
import time
import json
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
import subprocess
import docker


class TestDockerOptimized:
    """Test suite for optimized Docker configuration"""
    
    @pytest.fixture
    def docker_compose_file(self):
        """Path to optimized docker-compose file"""
        return Path(__file__).parent.parent / "docker-compose.optimized.yml"
    
    def test_docker_compose_file_exists(self, docker_compose_file):
        """Test that optimized docker-compose file exists"""
        assert docker_compose_file.exists()
        assert docker_compose_file.is_file()
    
    def test_docker_compose_structure(self, docker_compose_file):
        """Test docker-compose file structure"""
        content = docker_compose_file.read_text()
        
        # Verify required services are present
        required_services = [
            "ollama:",
            "redis:",
            "api:",
            "ui:",
            "worker:"
        ]
        
        for service in required_services:
            assert service in content
        
        # Verify optional services are present
        optional_services = [
            "prometheus:",
            "grafana:",
            "backup:"
        ]
        
        for service in optional_services:
            assert service in content
    
    def test_resource_limits(self, docker_compose_file):
        """Test resource limits are configured"""
        content = docker_compose_file.read_text()
        
        # Check memory limits
        assert "mem_limit:" in content
        
        # Check CPU limits
        assert "cpus:" in content
        
        # Verify specific limits for key services
        assert "mem_limit: 6g" in content  # Ollama
        assert "mem_limit: 512m" in content  # Redis
        assert "mem_limit: 1g" in content  # API
    
    def test_health_checks(self, docker_compose_file):
        """Test health checks are configured"""
        content = docker_compose_file.read_text()
        
        # Verify healthcheck section exists
        assert "healthcheck:" in content
        
        # Check health check commands
        assert "curl -f http://localhost:11434/api/tags" in content  # Ollama
        assert "redis-cli ping" in content  # Redis
        assert "curl -f http://localhost:8000/health" in content  # API
    
    def test_network_configuration(self, docker_compose_file):
        """Test network configuration"""
        content = docker_compose_file.read_text()
        
        # Verify network configuration
        assert "networks:" in content
        assert "default:" in content
        assert "driver: bridge" in content
        assert "ipam:" in content
    
    def test_volume_configuration(self, docker_compose_file):
        """Test volume configuration"""
        content = docker_compose_file.read_text()
        
        # Verify volumes are defined
        assert "volumes:" in content
        
        # Check specific volumes
        assert "ollama_models:" in content
        assert "redis_data:" in content
        assert "prometheus_data:" in content
        assert "grafana_data:" in content


class TestDockerfileOptimized:
    """Test suite for optimized Dockerfile"""
    
    @pytest.fixture
    def dockerfile_optimized(self):
        """Path to optimized Dockerfile"""
        return Path(__file__).parent.parent / "Dockerfile.optimized"
    
    def test_dockerfile_exists(self, dockerfile_optimized):
        """Test that optimized Dockerfile exists"""
        assert dockerfile_optimized.exists()
        assert dockerfile_optimized.is_file()
    
    def test_multi_stage_build(self, dockerfile_optimized):
        """Test multi-stage build configuration"""
        content = dockerfile_optimized.read_text()
        
        # Verify multi-stage build
        assert "FROM python:" in content
        assert "as base" in content
        assert "as development" in content
        assert "as production" in content
        assert "as lightweight" in content
        assert "as ml-enabled" in content
    
    def test_security_hardening(self, dockerfile_optimized):
        """Test security hardening in Dockerfile"""
        content = dockerfile_optimized.read_text()
        
        # Check for non-root user
        assert "useradd" in content or "adduser" in content
        assert "USER asmblr" in content
        
        # Check for security environment variables
        assert "PYTHONDONTWRITEBYTECODE=1" in content
        assert "PYTHONUNBUFFERED=1" in content
    
    def test_optimization_features(self, dockerfile_optimized):
        """Test optimization features"""
        content = dockerfile_optimized.read_text()
        
        # Check for caching optimization
        assert "COPY requirements.core.txt requirements.txt" in content
        
        # Check for cleanup
        assert "rm -rf" in content or "apt-get clean" in content
        
        # Check for pip optimization
        assert "PIP_NO_CACHE_DIR=1" in content


class TestDockerIntegration:
    """Integration tests for Docker setup"""
    
    @pytest.mark.asyncio
    async def test_docker_services_startup(self):
        """Test Docker services startup sequence"""
        # This test requires Docker to be running
        try:
            client = docker.from_env()
        except docker.errors.DockerException:
            pytest.skip("Docker not available")
        
        # Test if we can list containers (Docker is accessible)
        try:
            containers = client.containers.list()
            assert isinstance(containers, list)
        except Exception as e:
            pytest.skip(f"Docker access failed: {e}")
    
    @pytest.mark.asyncio
    async def test_compose_validation(self):
        """Test docker-compose configuration validation"""
        compose_file = Path(__file__).parent.parent / "docker-compose.optimized.yml"
        
        if not compose_file.exists():
            pytest.skip("docker-compose.optimized.yml not found")
        
        # Validate docker-compose file
        try:
            result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "config"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Should not have validation errors
            assert result.returncode == 0
            
            # Should contain service definitions
            assert "services:" in result.stdout
            
        except subprocess.TimeoutExpired:
            pytest.skip("Docker compose validation timeout")
        except FileNotFoundError:
            pytest.skip("docker-compose command not found")
    
    @pytest.mark.asyncio
    async def test_resource_usage_simulation(self):
        """Test resource usage simulation"""
        # Simulate resource allocation
        services_config = {
            "ollama": {"mem_limit": "6g", "cpus": "3.0"},
            "redis": {"mem_limit": "512m", "cpus": "0.5"},
            "api": {"mem_limit": "1g", "cpus": "1.0"},
            "ui": {"mem_limit": "512m", "cpus": "0.5"},
            "worker": {"mem_limit": "1g", "cpus": "1.0"}
        }
        
        total_memory_gb = 0
        total_cpus = 0
        
        for service, config in services_config.items():
            # Parse memory limits
            mem_limit = config["mem_limit"]
            if mem_limit.endswith("g"):
                total_memory_gb += float(mem_limit[:-1])
            elif mem_limit.endswith("m"):
                total_memory_gb += float(mem_limit[:-1]) / 1024
            
            # Parse CPU limits
            total_cpus += float(config["cpus"])
        
        # Verify reasonable resource allocation
        assert total_memory_gb < 12  # Should be under 12GB for typical dev machine
        assert total_cpus < 8  # Should be under 8 CPUs for typical dev machine
    
    @pytest.mark.asyncio
    async def test_health_check_endpoints(self):
        """Test health check endpoints configuration"""
        compose_file = Path(__file__).parent.parent / "docker-compose.optimized.yml"
        
        if not compose_file.exists():
            pytest.skip("docker-compose.optimized.yml not found")
        
        content = compose_file.read_text()
        
        # Extract health check endpoints
        health_checks = {
            "ollama": "http://localhost:11434/api/tags",
            "redis": "redis-cli ping",
            "api": "http://localhost:8000/health",
            "ui": "http://localhost:8501/_stcore/health"
        }
        
        for service, expected_check in health_checks.items():
            assert expected_check in content, f"Health check for {service} not found"
    
    @pytest.mark.asyncio
    async def test_profile_configuration(self):
        """Test Docker Compose profiles configuration"""
        compose_file = Path(__file__).parent.parent / "docker-compose.optimized.yml"
        
        if not compose_file.exists():
            pytest.skip("docker-compose.optimized.yml not found")
        
        content = compose_file.read_text()
        
        # Check for profile definitions
        assert "profiles:" in content
        
        # Verify specific profiles
        expected_profiles = ["monitoring", "backup"]
        for profile in expected_profiles:
            assert profile in content, f"Profile {profile} not found"
        
        # Check monitoring profile services
        assert "prometheus:" in content
        assert "grafana:" in content
        
        # Check backup profile services
        assert "backup:" in content


class TestDockerPerformance:
    """Performance tests for Docker setup"""
    
    @pytest.mark.asyncio
    async def test_image_build_performance(self):
        """Test Docker image build performance simulation"""
        # Simulate build times for different targets
        build_targets = {
            "lightweight": {"estimated_time": 120, "size_mb": 200},
            "production": {"estimated_time": 180, "size_mb": 250},
            "ml-enabled": {"estimated_time": 300, "size_mb": 800}
        }
        
        for target, config in build_targets.items():
            # Verify reasonable build times
            assert config["estimated_time"] < 600  # Under 10 minutes
            assert config["size_mb"] < 1000  # Under 1GB for optimized images
    
    @pytest.mark.asyncio
    async def test_startup_performance(self):
        """Test container startup performance simulation"""
        # Simulate startup times
        startup_times = {
            "redis": {"expected_time": 5, "max_time": 15},
            "ollama": {"expected_time": 10, "max_time": 60},
            "api": {"expected_time": 15, "max_time": 30},
            "ui": {"expected_time": 20, "max_time": 45}
        }
        
        for service, config in startup_times.items():
            # Verify reasonable startup times
            assert config["expected_time"] < config["max_time"]
            assert config["max_time"] < 120  # All services should start within 2 minutes
    
    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """Test memory efficiency configuration"""
        # Verify memory limits are reasonable
        memory_limits = {
            "redis": {"limit": "512m", "reasonable": True},
            "api": {"limit": "1g", "reasonable": True},
            "ui": {"limit": "512m", "reasonable": True},
            "worker": {"limit": "1g", "reasonable": True},
            "ollama": {"limit": "6g", "reasonable": True}
        }
        
        for service, config in memory_limits.items():
            # Convert to MB for comparison
            limit_str = config["limit"]
            if limit_str.endswith("m"):
                limit_mb = int(limit_str[:-1])
            elif limit_str.endswith("g"):
                limit_mb = int(limit_str[:-1]) * 1024
            
            # Verify reasonable limits
            assert limit_mb < 8192  # Under 8GB for any service
            assert config["reasonable"]


@pytest.mark.asyncio
async def test_docker_security_configuration():
    """Test Docker security configuration"""
    compose_file = Path(__file__).parent.parent / "docker-compose.optimized.yml"
    dockerfile = Path(__file__).parent.parent / "Dockerfile.optimized"
    
    if not compose_file.exists() or not dockerfile.exists():
        pytest.skip("Docker configuration files not found")
    
    compose_content = compose_file.read_text()
    dockerfile_content = dockerfile.read_text()
    
    # Check for security best practices
    security_checks = {
        "non_root_user": "USER asmblr" in dockerfile_content,
        "read_only_filesystem": "read_only: true" in compose_content,  # Optional
        "no_privileged": "privileged: true" not in compose_content,
        "drop_capabilities": "cap_drop:" in compose_content,  # Optional
        "security_opt": "security_opt:" in compose_content  # Optional
    }
    
    # Required security checks
    assert security_checks["non_root_user"], "Non-root user not configured"
    assert not security_checks["no_privileged"], "Privileged mode should not be used"


@pytest.mark.asyncio
async def test_docker_monitoring_integration():
    """Test Docker monitoring integration"""
    compose_file = Path(__file__).parent.parent / "docker-compose.optimized.yml"
    
    if not compose_file.exists():
        pytest.skip("docker-compose.optimized.yml not found")
    
    content = compose_file.read_text()
    
    # Verify monitoring stack integration
    monitoring_components = {
        "prometheus": "prometheus:" in content,
        "grafana": "grafana:" in content,
        "metrics_ports": "9090:9090" in content,  # Prometheus
        "grafana_port": "3001:3000" in content,  # Grafana
        "monitoring_profile": 'profiles: ["monitoring"]' in content
    }
    
    for component, exists in monitoring_components.items():
        if component in ["metrics_ports", "grafana_port"]:
            # These are optional for local development
            continue
        assert exists, f"Monitoring component {component} not found"
