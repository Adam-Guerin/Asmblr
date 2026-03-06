# Public Configuration for Asmblr
# Safe defaults for public distribution

from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Import safe conversion functions from main config
import sys
sys.path.append(str(Path(__file__).parent))
from config import safe_int, safe_float, safe_bool

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]

@dataclass
class PublicSettings:
    """Public-safe configuration settings"""
    
    # Ollama Configuration
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    general_model: str = os.getenv("GENERAL_MODEL", "llama3.1:8b")
    code_model: str = os.getenv("CODE_MODEL", "qwen2.5-coder:7b")
    general_model_fallbacks: str = os.getenv("GENERAL_MODEL_FALLBACKS", "")
    code_model_fallbacks: str = os.getenv("CODE_MODEL_FALLBACKS", "")

    # Demo Mode Configuration
    demo_mode: bool = safe_bool("DEMO_MODE", False)
    demo_topic: str = os.getenv("DEMO_TOPIC", "AI-powered task management for remote teams")
    demo_max_ideas: int = safe_int("DEMO_MAX_IDEAS", 5, 1, 20)
    demo_fast_mode: bool = safe_bool("DEMO_FAST_MODE", True)

    # Pipeline Configuration (Public-safe defaults)
    default_n_ideas: int = safe_int("DEFAULT_N_IDEAS", 5, 1, 20)  # Reduced for public
    fast_mode: bool = safe_bool("FAST_MODE", True)  # Default to fast
    mvp_build_command: str = os.getenv("MVP_BUILD_COMMAND", "")
    mvp_test_command: str = os.getenv("MVP_TEST_COMMAND", "")
    mvp_install_command: str = os.getenv("MVP_INSTALL_COMMAND", "")
    mvp_dev_command: str = os.getenv("MVP_DEV_COMMAND", "")
    mvp_dev_base_url: str = os.getenv("MVP_DEV_BASE_URL", "http://127.0.0.1:3000")
    mvp_dev_startup_timeout: int = safe_int("MVP_DEV_STARTUP_TIMEOUT", 60, 30, 300)  # Increased
    mvp_dev_check_paths: str = os.getenv("MVP_DEV_CHECK_PATHS", "/,/api/status,/api/health")
    mvp_install_timeout: int = safe_int("MVP_INSTALL_TIMEOUT", 900, 60, 1800)  # 15 minutes
    mvp_build_timeout: int = safe_int("MVP_BUILD_TIMEOUT", 600, 60, 1800)  # 10 minutes
    mvp_test_timeout: int = safe_int("MVP_TEST_TIMEOUT", 600, 60, 1800)  # 10 minutes
    mvp_force_autofix: bool = safe_bool("MVP_FORCE_AUTOFIX", True)
    mvp_disable_llm: bool = safe_bool("MVP_DISABLE_LLM", False)
    frontend_style: str = os.getenv("FRONTEND_STYLE", "startup_clean")
    
    # Network Configuration (Conservative defaults)
    request_timeout: int = safe_int("REQUEST_TIMEOUT", 30, 10, 120)  # Increased
    rate_limit_per_domain: int = safe_int("RATE_LIMIT_PER_DOMAIN", 1, 1, 10)  # More restrictive
    max_sources: int = safe_int("MAX_SOURCES", 5, 1, 20)  # Reduced for public
    retry_max_attempts: int = safe_int("RETRY_MAX_ATTEMPTS", 2, 1, 5)  # Reduced
    retry_min_wait: int = safe_int("RETRY_MIN_WAIT", 2, 1, 60)  # Increased
    retry_max_wait: int = safe_int("RETRY_MAX_WAIT", 10, 5, 300)  # Increased
    
    # Quality Thresholds (Adjusted for public use)
    min_pages: int = safe_int("MIN_PAGES", 2, 1, 10)  # More lenient
    min_pains: int = safe_int("MIN_PAINS", 2, 1, 10)  # More lenient
    min_competitors: int = safe_int("MIN_COMPETITORS", 0, 0, 5)  # Optional
    min_avg_text_len: int = safe_int("MIN_AVG_TEXT_LEN", 150, 50, 500)  # Reduced
    min_unique_domains: int = safe_int("MIN_UNIQUE_DOMAINS", 1, 1, 5)  # More lenient
    market_signal_threshold: int = safe_int("MARKET_SIGNAL_THRESHOLD", 30, 10, 80)  # Reduced
    
    # Signal Processing (Adjusted for public)
    signal_sources_target: int = safe_int("SIGNAL_SOURCES_TARGET", 4, 1, 10)  # Reduced
    signal_pains_target: int = safe_int("SIGNAL_PAINS_TARGET", 5, 1, 15)  # Reduced
    signal_domain_target: int = safe_int("SIGNAL_DOMAIN_TARGET", 2, 1, 5)  # Reduced
    signal_repeat_target: int = safe_int("SIGNAL_REPEAT_TARGET", 1, 1, 5)  # Reduced
    signal_pages_target: int = safe_int("SIGNAL_PAGES_TARGET", 8, 1, 20)  # Reduced
    signal_cluster_density_target: int = safe_int("SIGNAL_CLUSTER_DENSITY_TARGET", 2, 1, 5)  # Reduced
    signal_novel_keywords_target: int = safe_int("SIGNAL_NOVEL_KEYWORDS_TARGET", 5, 1, 15)  # Reduced
    signal_quality_threshold: int = safe_int("SIGNAL_QUALITY_THRESHOLD", 35, 10, 80)  # Reduced
    signal_recency_days: int = safe_int("SIGNAL_RECENCY_DAYS", 730, 30, 3650)  # Extended to 2 years
    
    # ICP Configuration (Public-friendly defaults)
    idea_actionability_min_score: int = safe_int("IDEA_ACTIONABILITY_MIN_SCORE", 45, 20, 80)  # Reduced
    idea_actionability_adjustment_max: int = safe_int("IDEA_ACTIONABILITY_ADJUSTMENT_MAX", 15, 5, 30)  # Increased
    idea_actionability_require_eligible_top: bool = safe_bool("IDEA_ACTIONABILITY_REQUIRE_ELIGIBLE_TOP", False)
    primary_icp: str = os.getenv("PRIMARY_ICP", "Startups and small teams")
    primary_icp_keywords: str = os.getenv("PRIMARY_ICP_KEYWORDS", "startup,startups,small team,entrepreneur,founder")
    icp_alignment_bonus_max: int = safe_int("ICP_ALIGNMENT_BONUS_MAX", 10, 1, 20)  # Increased
    
    # Performance Configuration
    enable_self_healing: bool = safe_bool("ENABLE_SELF_HEALING", False)  # Disabled for public
    stage_retry_attempts: int = safe_int("STAGE_RETRY_ATTEMPTS", 1, 1, 3)  # Reduced
    stage_retry_backoff_sec: float = safe_float("STAGE_RETRY_BACKOFF_SEC", 2.0, 0.5, 10.0)  # Increased
    
    # Paths
    runs_dir: Path = BASE_DIR / os.getenv("RUNS_DIR", "runs")
    data_dir: Path = BASE_DIR / os.getenv("DATA_DIR", "data")
    config_dir: Path = BASE_DIR / os.getenv("CONFIG_DIR", "configs")
    knowledge_dir: Path = BASE_DIR / os.getenv("KNOWLEDGE_DIR", "knowledge")
    enable_progressive_cycles: bool = safe_bool("ENABLE_PROGRESSIVE_CYCLES", True)
    
    # Feature Flags (Public-safe defaults)
    enable_logo_diffusion: bool = safe_bool("ENABLE_LOGO_DIFFUSION", False)  # Disabled
    logo_model_id: str = os.getenv("LOGO_MODEL_ID", "runwayml/stable-diffusion-v1-5")
    logo_image_size: int = safe_int("LOGO_IMAGE_SIZE", 256, 128, 512)  # Reduced
    logo_steps: int = safe_int("LOGO_STEPS", 20, 10, 50)  # Reduced
    logo_guidance: float = safe_float("LOGO_GUIDANCE", 5.0, 1.0, 15.0)
    logo_seed: int = safe_int("LOGO_SEED", 42, 0, 2147483647)
    logo_device: str = os.getenv("LOGO_DEVICE", "cpu")  # Force CPU for public
    
    # API Configuration (Public-safe)
    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = safe_int("API_PORT", 8000, 1024, 65535)
    ui_host: str = os.getenv("UI_HOST", "127.0.0.1")
    ui_port: int = safe_int("UI_PORT", 8501, 1024, 65535)
    ui_password: str = os.getenv("UI_PASSWORD", "")  # No default password
    ui_password_prev: str = os.getenv("UI_PASSWORD_PREV", "")
    ui_password_prev_expires_at: str = os.getenv("UI_PASSWORD_PREV_EXPIRES_AT", "")
    
    # Decision Thresholds (More lenient for public)
    kill_threshold: int = safe_int("KILL_THRESHOLD", 45, 20, 80)  # Reduced
    
    # Security Configuration (Public-safe)
    api_key: str = os.getenv("API_KEY", "")  # No auto-generation
    api_key_prev: str = os.getenv("API_KEY_PREV", "")
    api_key_prev_expires_at: str = os.getenv("API_KEY_PREV_EXPIRES_AT", "")
    enforce_key_rotation: bool = safe_bool("ENFORCE_KEY_ROTATION", False)  # Disabled
    prod_mode: bool = safe_bool("PROD_MODE", False)
    require_prod_checklist: bool = safe_bool("REQUIRE_PROD_CHECKLIST", False)  # Disabled
    
    # Rate Limiting (More restrictive for public)
    run_rate_limit_per_min: int = safe_int("RUN_RATE_LIMIT_PER_MIN", 3, 1, 10)  # Reduced
    run_rate_limit_burst: int = safe_int("RUN_RATE_LIMIT_BURST", 2, 1, 5)  # Reduced
    run_retention_days: int = safe_int("RUN_RETENTION_DAYS", 7, 1, 30)  # Reduced
    run_max_count: int = safe_int("RUN_MAX_COUNT", 50, 10, 200)  # Reduced
    run_compress_after_days: int = safe_int("RUN_COMPRESS_AFTER_DAYS", 3, 1, 7)  # Reduced
    run_maintenance_interval_min: int = safe_int("RUN_MAINTENANCE_INTERVAL_MIN", 30, 5, 120)  # Reduced
    run_archive_dirs: str = os.getenv("RUN_ARCHIVE_DIRS", "")
    
    # Learning Configuration (Disabled for public)
    learning_history_max_runs: int = safe_int("LEARNING_HISTORY_MAX_RUNS", 50, 10, 100)  # Reduced
    learning_exploration_rate: float = safe_float("LEARNING_EXPLORATION_RATE", 0.1, 0.0, 0.5)  # Reduced
    learning_success_bonus_max: int = safe_int("LEARNING_SUCCESS_BONUS_MAX", 5, 1, 15)  # Reduced
    learning_failure_penalty_max: int = safe_int("LEARNING_FAILURE_PENALTY_MAX", 5, 1, 15)  # Reduced
    learning_novelty_bonus_max: int = safe_int("LEARNING_NOVELTY_BONUS_MAX", 3, 1, 10)  # Reduced
    learning_clone_penalty_start: float = safe_float("LEARNING_CLONE_PENALTY_START", 0.8, 0.5, 1.0)  # Increased
    
    # Advanced Features (Optional)
    enable_connection_pooling: bool = safe_bool("ENABLE_CONNECTION_POOLING", False)
    max_http_connections: int = safe_int("MAX_HTTP_CONNECTIONS", 10, 1, 50)  # Reduced
    max_redis_connections: int = safe_int("MAX_REDIS_CONNECTIONS", 5, 1, 20)  # Reduced
    enable_request_batching: bool = safe_bool("ENABLE_REQUEST_BATCHING", False)
    max_batch_size: int = safe_int("MAX_BATCH_SIZE", 20, 1, 100)  # Reduced
    
    # Monitoring (Optional)
    enable_monitoring: bool = safe_bool("ENABLE_MONITORING", False)
    jaeger_endpoint: str = os.getenv("JAEGER_ENDPOINT", "http://localhost:14268/api/traces")
    prometheus_port: int = safe_int("PROMETHEUS_PORT", 9090, 1024, 65535)
    
    # Security Features (Optional)
    enable_rate_limiting: bool = safe_bool("ENABLE_RATE_LIMITING", True)
    max_requests_per_minute: int = safe_int("MAX_REQUESTS_PER_MINUTE", 30, 1, 100)  # Reduced
    enable_ip_blocking: bool = safe_bool("ENABLE_IP_BLOCKING", False)
    
    # Development Features
    log_level: str = os.getenv("LOG_LEVEL", "info")
    log_json: bool = safe_bool("LOG_JSON", False)
    enable_profiling: bool = safe_bool("ENABLE_PROFILING", False)


def get_public_settings() -> PublicSettings:
    """Get public-safe settings"""
    return PublicSettings()


def validate_public_settings(settings: PublicSettings) -> List[str]:
    """Validate public settings and return warnings/errors"""
    warnings = []
    errors = []
    
    # Check for required Ollama setup
    if not settings.ollama_base_url:
        errors.append("OLLAMA_BASE_URL is required")
    
    # Check for demo mode vs real mode
    if not settings.demo_mode and not settings.api_key:
        warnings.append("Running without API key in non-demo mode - consider enabling demo mode")
    
    # Check resource limits
    if settings.max_sources > 20:
        warnings.append("High MAX_SOURCES value may impact performance")
    
    if settings.default_n_ideas > 20:
        warnings.append("High DEFAULT_N_IDEAS value may impact performance")
    
    # Check security settings
    if settings.prod_mode and not settings.api_key:
        errors.append("API_KEY is required in production mode")
    
    return warnings + errors


def generate_demo_config() -> str:
    """Generate demo configuration content"""
    return """
# Demo Mode Configuration
DEMO_MODE=true
DEMO_TOPIC="AI-powered task management for remote teams"
DEMO_MAX_IDEAS=5
DEMO_FAST_MODE=true

# Conservative Settings for Demo
DEFAULT_N_IDEAS=5
FAST_MODE=true
MAX_SOURCES=5
RATE_LIMIT_PER_DOMAIN=1
REQUEST_TIMEOUT=30

# Disabled Features for Demo
ENABLE_SELF_HEALING=false
ENABLE_LOGO_DIFFUSION=false
ENABLE_MONITORING=false
ENABLE_CONNECTION_POOLING=false
ENABLE_REQUEST_BATCHING=false
    """


# Helper functions for public distribution
def is_demo_mode() -> bool:
    """Check if running in demo mode"""
    return os.getenv("DEMO_MODE", "false").lower() == "true"


def get_demo_examples() -> Dict[str, Any]:
    """Get demo examples for public users"""
    return {
        "topics": [
            "AI-powered task management for remote teams",
            "Smart scheduling assistant for freelancers",
            "Automated expense tracking for small businesses",
            "Virtual team collaboration platform",
            "AI-driven customer support chatbot"
        ],
        "icp_examples": [
            "Startups and small teams",
            "Freelancers and solopreneurs",
            "Small businesses (1-50 employees)",
            "Remote workers and digital nomads",
            "Non-profit organizations"
        ],
        "sample_configurations": {
            "quick_demo": {
                "DEFAULT_N_IDEAS": "3",
                "FAST_MODE": "true",
                "MAX_SOURCES": "3",
                "DEMO_MODE": "true"
            },
            "full_demo": {
                "DEFAULT_N_IDEAS": "10",
                "FAST_MODE": "false",
                "MAX_SOURCES": "8",
                "DEMO_MODE": "true",
                "ENABLE_LOGO_DIFFUSION": "true"
            }
        }
    }
