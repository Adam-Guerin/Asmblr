import os
import re
import threading
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
from dotenv import load_dotenv
from app.core.lightweight_config import lightweight_config

# Define BASE_DIR first since it's used in detect_lightweight_mode
BASE_DIR = Path(__file__).resolve().parents[2]

# Safe type conversion functions
def safe_int(env_var: str, default: int, min_val: int | None = None, max_val: int | None = None) -> int:
    """Safely convert environment variable to int with validation"""
    try:
        raw_value = os.getenv(env_var, str(default))
        # Prevent extremely large values that could cause issues
        if raw_value is None or len(str(raw_value)) > 20:
            print(f"⚠️ Invalid {env_var} value (too long or None), using default: {default}")
            return default
        
        value = int(raw_value)
        if min_val is not None and value < min_val:
            print(f"⚠️ {env_var} value {value} below minimum {min_val}, using {min_val}")
            value = min_val
        if max_val is not None and value > max_val:
            print(f"⚠️ {env_var} value {value} above maximum {max_val}, using {max_val}")
            value = max_val
        return value
    except (ValueError, TypeError):
        print(f"⚠️ Invalid {env_var} value, using default: {default}")
        return default

def safe_float(env_var: str, default: float, min_val: float | None = None, max_val: float | None = None) -> float:
    """Safely convert environment variable to float with validation"""
    try:
        value = float(os.getenv(env_var, str(default)))
        if min_val is not None and value < min_val:
            print(f"⚠️ {env_var} value {value} below minimum {min_val}, using {min_val}")
            value = min_val
        if max_val is not None and value > max_val:
            print(f"⚠️ {env_var} value {value} above maximum {max_val}, using {max_val}")
            value = max_val
        return value
    except (ValueError, TypeError):
        print(f"⚠️ Invalid {env_var} value, using default: {default}")
        return default

def safe_bool(env_var: str, default: bool) -> bool:
    """Safely convert environment variable to bool"""
    value = os.getenv(env_var)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')

# Lightweight mode detection and automatic loading
def detect_lightweight_mode():
    """Detect if lightweight mode should be enabled"""
    # Check for explicit lightweight flag (standardized variable name)
    lightweight_flag = (
        os.getenv("LIGHTWEIGHT_MODE", "").lower() == "true" or
        os.getenv("ASMblr_LIGHTWEIGHT", "").lower() == "true"
    )
    
    # Check for .env.light file existence
    env_light_exists = Path(BASE_DIR / ".env.light").exists()
    
    # Check for resource constraints (auto-detection)
    try:
        import psutil
        # Check available memory (less than 4GB = lightweight)
        available_memory_gb = psutil.virtual_memory().available / (1024**3)
        memory_constrained = available_memory_gb < 4
        
        # Check available CPU (less than 4 cores = lightweight)
        cpu_count = psutil.cpu_count()
        cpu_constrained = cpu_count < 4
        
        auto_detect_lightweight = memory_constrained or cpu_constrained
    except ImportError:
        auto_detect_lightweight = False
    
    return lightweight_flag or env_light_exists or auto_detect_lightweight

# Load appropriate environment file with validation
def load_environment_file():
    """Load appropriate environment file with validation and fallback"""
    env_file = BASE_DIR / ".env"
    env_light_file = BASE_DIR / ".env.light"
    
    if detect_lightweight_mode():
        print("Lightweight mode detected - attempting to load .env.light")
        if env_light_file.exists():
            try:
                load_dotenv(env_light_file)
                print(f" Loaded .env.light from {env_light_file}")
                # Set lightweight mode flag for other components
                os.environ["LIGHTWEIGHT_MODE"] = "true"
                return True  # Success
            except Exception as e:
                print(f" Failed to load .env.light: {e}")
                print("Falling back to .env...")
        else:
            print(f" .env.light not found at {env_light_file}")
            print("Falling back to .env...")
        
        # Fallback to .env
        try:
            load_dotenv(env_file)
            print(f" Loaded .env from {env_file}")
            os.environ["LIGHTWEIGHT_MODE"] = "true"
            return True  # Success
        except Exception as e:
            print(f" Failed to load .env: {e}")
            print(" No environment configuration loaded!")
            return False  # Failure
    else:
        print("Standard mode - loading .env")
        if env_file.exists():
            try:
                load_dotenv(env_file)
                print(f" Loaded .env from {env_file}")
                return True  # Success
            except Exception as e:
                print(f" Failed to load .env: {e}")
                print(" No environment configuration loaded!")
                return False  # Failure
        else:
            print(f" .env not found at {env_file}")
            print(" No environment configuration loaded!")
            return False  # Failure

# Environment loading will be deferred to first use
_env_loaded = False
_env_lock = threading.Lock()

def _ensure_env_loaded():
    """Ensure environment is loaded only once, thread-safely"""
    global _env_loaded
    with _env_lock:
        # Double-check pattern to prevent race condition
        if not _env_loaded:
            success = load_environment_file()
            if success:
                _env_loaded = True
            # If loading fails, _env_loaded remains False, allowing retry

@dataclass
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"
    general_model: str = os.getenv("GENERAL_MODEL") or "llama3.1:8b"
    code_model: str = os.getenv("CODE_MODEL") or "qwen2.5-coder:7b"
    general_model_fallbacks: str = os.getenv("GENERAL_MODEL_FALLBACKS") or ""
    code_model_fallbacks: str = os.getenv("CODE_MODEL_FALLBACKS") or ""

    default_n_ideas: int = safe_int("DEFAULT_N_IDEAS", 10, 1, 50)
    fast_mode: bool = safe_bool("FAST_MODE", False)
    mvp_build_command: str = os.getenv("MVP_BUILD_COMMAND", "")
    mvp_test_command: str = os.getenv("MVP_TEST_COMMAND", "")
    mvp_install_command: str = os.getenv("MVP_INSTALL_COMMAND", "")
    mvp_dev_command: str = os.getenv("MVP_DEV_COMMAND", "")
    mvp_dev_base_url: str = os.getenv("MVP_DEV_BASE_URL", "http://127.0.0.1:3000")
    mvp_dev_startup_timeout: int = safe_int("MVP_DEV_STARTUP_TIMEOUT", 35, 10, 300)
    mvp_dev_check_paths: str = os.getenv("MVP_DEV_CHECK_PATHS", "/,/api/status,/api/health")
    mvp_install_timeout: int = safe_int("MVP_INSTALL_TIMEOUT", 600, 60, 3600)
    mvp_build_timeout: int = safe_int("MVP_BUILD_TIMEOUT", 300, 60, 1800)
    mvp_test_timeout: int = safe_int("MVP_TEST_TIMEOUT", 300, 60, 1800)
    mvp_force_autofix: bool = safe_bool("MVP_FORCE_AUTOFIX", False)
    mvp_disable_llm: bool = safe_bool("MVP_DISABLE_LLM", False)
    frontend_style: str = os.getenv("FRONTEND_STYLE", "startup_clean")
    request_timeout: int = safe_int("REQUEST_TIMEOUT", 20, 5, 300)
    rate_limit_per_domain: int = safe_int("RATE_LIMIT_PER_DOMAIN", 2, 1, 20)
    max_sources: int = safe_int("MAX_SOURCES", 8, 1, 50)
    retry_max_attempts: int = safe_int("RETRY_MAX_ATTEMPTS", 3, 1, 10)
    retry_min_wait: int = safe_int("RETRY_MIN_WAIT", 1, 1, 60)
    retry_max_wait: int = safe_int("RETRY_MAX_WAIT", 6, 1, 300)
    min_pages: int = safe_int("MIN_PAGES", 3, 1, 20)
    min_pains: int = safe_int("MIN_PAINS", 3, 1, 20)
    min_competitors: int = safe_int("MIN_COMPETITORS", 1, 0, 10)
    min_avg_text_len: int = safe_int("MIN_AVG_TEXT_LEN", 200, 50, 1000)
    min_unique_domains: int = safe_int("MIN_UNIQUE_DOMAINS", 2, 1, 10)
    market_signal_threshold: int = safe_int("MARKET_SIGNAL_THRESHOLD", 40, 10, 100)
    signal_sources_target: int = safe_int("SIGNAL_SOURCES_TARGET", 6, 1, 20)
    signal_pains_target: int = safe_int("SIGNAL_PAINS_TARGET", 8, 1, 30)
    signal_domain_target: int = safe_int("SIGNAL_DOMAIN_TARGET", 4, 1, 10)
    signal_repeat_target: int = safe_int("SIGNAL_REPEAT_TARGET", 2, 1, 10)
    signal_pages_target: int = safe_int("SIGNAL_PAGES_TARGET", 12, 1, 50)
    signal_cluster_density_target: int = safe_int("SIGNAL_CLUSTER_DENSITY_TARGET", 3, 1, 10)
    signal_novel_keywords_target: int = safe_int("SIGNAL_NOVEL_KEYWORDS_TARGET", 8, 1, 20)
    signal_quality_threshold: int = safe_int("SIGNAL_QUALITY_THRESHOLD", 45, 10, 100)
    signal_recency_days: int = safe_int("SIGNAL_RECENCY_DAYS", 365, 7, 3650)
    idea_actionability_min_score: int = safe_int("IDEA_ACTIONABILITY_MIN_SCORE", 55, 0, 100)
    idea_actionability_adjustment_max: int = safe_int("IDEA_ACTIONABILITY_ADJUSTMENT_MAX", 12, 1, 50)
    idea_actionability_require_eligible_top: bool = safe_bool("IDEA_ACTIONABILITY_REQUIRE_ELIGIBLE_TOP", False)
    learning_history_max_runs: int = safe_int("LEARNING_HISTORY_MAX_RUNS", 200, 10, 1000)
    learning_exploration_rate: float = safe_float("LEARNING_EXPLORATION_RATE", 0.18, 0.0, 1.0)
    learning_success_bonus_max: int = safe_int("LEARNING_SUCCESS_BONUS_MAX", 8, 1, 50)
    learning_failure_penalty_max: int = safe_int("LEARNING_FAILURE_PENALTY_MAX", 10, 1, 50)
    learning_novelty_bonus_max: int = safe_int("LEARNING_NOVELTY_BONUS_MAX", 6, 1, 20)
    learning_clone_penalty_start: float = safe_float("LEARNING_CLONE_PENALTY_START", 0.75, 0.0, 1.0)
    primary_icp: str = os.getenv("PRIMARY_ICP", "Founders B2B SaaS pre-seed")
    primary_icp_keywords: str = os.getenv(
        "PRIMARY_ICP_KEYWORDS",
        "founder,founders,b2b,saas,pre-seed,startup,startups,small team,operators",
    )
    enable_agent_skills: bool = safe_bool("ENABLE_AGENT_SKILLS", True)
    agent_skills_dirs: str = os.getenv(
        "AGENT_SKILLS_DIRS",
        "skills,~/.codex/skills",
    )
    agent_skill_prompt_max_chars: int = safe_int("AGENT_SKILL_PROMPT_MAX_CHARS", 3200, 100, 10000)
    agent_skill_role_map: str = os.getenv(
        "AGENT_SKILL_ROLE_MAP",
        (
            "researcher=startup-analyst|deep-research|apify-market-research|context7-auto-research|competitive-landscape|market-sizing-analysis|research-engineer;"
            "analyst=competitor-alternatives|competitive-landscape|startup-business-analyst-market-opportunity|startup-business-analyst-business-case|startup-business-analyst-financial-projections|startup-metrics-framework|pricing-strategy;"
            "product=product-manager-toolkit|ai-product|startup-financial-modeling|startup-metrics-framework|prompt-engineering|prompt-engineering-patterns|api-documentation;"
            "tech-lead=software-architecture|frontend-dev-guidelines|testing-patterns|test-driven-development|test-automator|performance-engineer|observability-engineer|postmortem-writing|api-security-best-practices;"
            "growth=seo-content-writer|seo-content-planner|seo-keyword-strategist|seo-audit|programmatic-seo|social-content|content-marketer|copywriting|onboarding-cro;"
            "brand=brand-guidelines-community|brand-guidelines|ui-ux-designer|ui-ux-pro-max|frontend-design|canvas-design"
        ),
    )
    icp_alignment_bonus_max: int = safe_int("ICP_ALIGNMENT_BONUS_MAX", 8, 1, 50)
    enable_self_healing: bool = safe_bool("ENABLE_SELF_HEALING", True)
    stage_retry_attempts: int = safe_int("STAGE_RETRY_ATTEMPTS", 2, 1, 10)
    stage_retry_backoff_sec: float = safe_float("STAGE_RETRY_BACKOFF_SEC", 1.0, 0.1, 60.0)

    runs_dir: Path = BASE_DIR / os.getenv("RUNS_DIR", "runs")
    data_dir: Path = BASE_DIR / os.getenv("DATA_DIR", "data")
    config_dir: Path = BASE_DIR / os.getenv("CONFIG_DIR", "configs")
    knowledge_dir: Path = BASE_DIR / os.getenv("KNOWLEDGE_DIR", "knowledge")
    enable_progressive_cycles: bool = safe_bool("ENABLE_PROGRESSIVE_CYCLES", True)
    enable_logo_diffusion: bool = safe_bool("ENABLE_LOGO_DIFFUSION", False)
    logo_model_id: str = os.getenv("LOGO_MODEL_ID", "runwayml/stable-diffusion-v1-5")
    logo_image_size: int = safe_int("LOGO_IMAGE_SIZE", 512, 64, 2048)
    logo_steps: int = safe_int("LOGO_STEPS", 28, 1, 100)
    logo_guidance: float = safe_float("LOGO_GUIDANCE", 7.0, 1.0, 20.0)
    logo_seed: int = safe_int("LOGO_SEED", 0, 0, 2147483647)
    logo_device: str = os.getenv("LOGO_DEVICE", "cuda")

    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = safe_int("API_PORT", 8000, 1024, 65535)
    ui_host: str = os.getenv("UI_HOST", "127.0.0.1")
    ui_port: int = safe_int("UI_PORT", 8501, 1024, 65535)
    ui_password: str = os.getenv("UI_PASSWORD", "")
    ui_password_prev: str = os.getenv("UI_PASSWORD_PREV", "")
    ui_password_prev_expires_at: str = os.getenv("UI_PASSWORD_PREV_EXPIRES_AT", "")
    kill_threshold: int = safe_int("KILL_THRESHOLD", 55, 1, 100)
    api_key: str = os.getenv("API_KEY", "")  # Remove auto-generation for public version
    api_key_prev: str = os.getenv("API_KEY_PREV", "")
    api_key_prev_expires_at: str = os.getenv("API_KEY_PREV_EXPIRES_AT", "")
    enforce_key_rotation: bool = safe_bool("ENFORCE_KEY_ROTATION", True)
    prod_mode: bool = safe_bool("PROD_MODE", False)
    require_prod_checklist: bool = safe_bool("REQUIRE_PROD_CHECKLIST", True)
    run_rate_limit_per_min: int = safe_int("RUN_RATE_LIMIT_PER_MIN", 6, 1, 60)
    run_rate_limit_burst: int = safe_int("RUN_RATE_LIMIT_BURST", 3, 1, 20)
    run_retention_days: int = safe_int("RUN_RETENTION_DAYS", 30, 1, 365)
    run_max_count: int = safe_int("RUN_MAX_COUNT", 200, 1, 1000)
    run_compress_after_days: int = safe_int("RUN_COMPRESS_AFTER_DAYS", 7, 1, 90)
    run_maintenance_interval_min: int = safe_int("RUN_MAINTENANCE_INTERVAL_MIN", 60, 5, 1440)
    run_archive_dirs: str = os.getenv(
        "RUN_ARCHIVE_DIRS",
        "repo_skeleton,landing_page,content_pack,mvp_repo,mvp_cycles,project_build",
    )
    backup_dir: str = os.getenv("BACKUP_DIR", "data/backups")
    backup_retention_days: int = safe_int("BACKUP_RETENTION_DAYS", 14, 1, 365)
    audit_log_file: str = os.getenv("AUDIT_LOG_FILE", "data/audit.log")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # LLM Cache Configuration
    enable_cache: bool = safe_bool("ENABLE_CACHE", False)
    cache_ttl: int = safe_int("CACHE_TTL", 3600, 60, 86400)
    cache_max_size: int = safe_int("CACHE_MAX_SIZE", 10000, 100, 100000)
    cache_similarity_threshold: float = safe_float("CACHE_SIMILARITY_THRESHOLD", 0.85, 0.0, 1.0)
    redis_cache_db: int = safe_int("REDIS_CACHE_DB", 1, 0, 15)
    cache_async_enabled: bool = safe_bool("CACHE_ASYNC_ENABLED", True)
    cache_background_cleanup: bool = safe_bool("CACHE_BACKGROUND_CLEANUP", True)
    cache_compression_enabled: bool = safe_bool("CACHE_COMPRESSION_ENABLED", True)
    
    # Concurrency Optimization Settings
    worker_concurrency: int = safe_int("WORKER_CONCURRENCY", 3, 1, 20)
    api_concurrency: int = safe_int("API_CONCURRENCY", 10, 1, 100)
    uvicorn_workers: int = safe_int("UVICORN_WORKERS", 2, 1, 16)
    uvicorn_backlog: int = safe_int("UVICORN_BACKLOG", 2048, 64, 8192)
    queue_max_size: int = safe_int("QUEUE_MAX_SIZE", 1000, 100, 10000)
    batch_processing_size: int = safe_int("BATCH_PROCESSING_SIZE", 10, 1, 100)
    max_connections_per_pool: int = safe_int("MAX_CONNECTIONS_PER_POOL", 20, 1, 100)
    connection_timeout: int = safe_int("CONNECTION_TIMEOUT", 30, 5, 300)
    read_timeout: int = safe_int("READ_TIMEOUT", 60, 5, 600)
    write_timeout: int = safe_int("WRITE_TIMEOUT", 60, 5, 600)
    enable_async_tasks: bool = safe_bool("ENABLE_ASYNC_TASKS", True)
    async_workers: int = safe_int("ASYNC_WORKERS", 4, 1, 32)
    task_queue_size: int = safe_int("TASK_QUEUE_SIZE", 500, 50, 5000)
    background_processing: bool = safe_bool("BACKGROUND_PROCESSING", True)
    rq_queue_name: str = os.getenv("RQ_QUEUE_NAME", "asmblr")
    rq_default_timeout: int = safe_int("RQ_DEFAULT_TIMEOUT", 7200, 300, 14400)
    run_max_concurrent: int = safe_int("RUN_MAX_CONCURRENT", 1, 1, 10)
    run_queue_backoff_sec: int = safe_int("RUN_QUEUE_BACKOFF_SEC", 30, 5, 300)
    worker_port: int = safe_int("WORKER_PORT", 8001, 1024, 65535)
    enable_app_packaging: bool = safe_bool("ENABLE_APP_PACKAGING", True)
    app_package_targets: str = os.getenv(
        "APP_PACKAGE_TARGETS",
        "mvp_repo,landing_page,content_pack,distribution,hosting,brand_direction.md,brand_identity.json,logo.svg,launch_checklist.md,prd.md,tech_spec.md",
    )
    enable_distribution: bool = safe_bool("ENABLE_DISTRIBUTION", True)
    campaign_auto_expand_assets: bool = safe_bool("CAMPAIGN_AUTO_EXPAND_ASSETS", True)
    campaign_target_assets: int = safe_int("CAMPAIGN_TARGET_ASSETS", 30, 1, 100)
    campaign_posts_target: int = safe_int("CAMPAIGN_POSTS_TARGET", 12, 1, 50)
    campaign_ads_target: int = safe_int("CAMPAIGN_ADS_TARGET", 12, 1, 50)
    campaign_outreach_target: int = safe_int("CAMPAIGN_OUTREACH_TARGET", 4, 1, 20)
    campaign_videos_target: int = safe_int("CAMPAIGN_VIDEOS_TARGET", 2, 1, 10)
    campaign_boost_from_organic: bool = safe_bool("CAMPAIGN_BOOST_FROM_ORGANIC", True)
    campaign_organic_top_assets: int = safe_int("CAMPAIGN_ORGANIC_TOP_ASSETS", 6, 1, 20)
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "")
    public_base_domain: str = os.getenv("PUBLIC_BASE_DOMAIN", "")
    public_url_template: str = os.getenv("PUBLIC_URL_TEMPLATE", "https://{slug}.{domain}")
    offline_creation: bool = safe_bool("OFFLINE_CREATION", False)
    enable_local_social_images: bool = safe_bool("ENABLE_LOCAL_SOCIAL_IMAGES", True)
    social_image_model_id: str = os.getenv("SOCIAL_IMAGE_MODEL_ID", "runwayml/stable-diffusion-v1-5")
    social_image_size: int = safe_int("SOCIAL_IMAGE_SIZE", 768, 256, 2048)
    social_image_steps: int = safe_int("SOCIAL_IMAGE_STEPS", 28, 1, 100)
    social_image_guidance: float = safe_float("SOCIAL_IMAGE_GUIDANCE", 7.0, 1.0, 20.0)
    social_image_seed: int = safe_int("SOCIAL_IMAGE_SEED", 0, 0, 2147483647)
    social_metrics_provider: str = os.getenv("SOCIAL_METRICS_PROVIDER", "").strip()
    social_metrics_user_id: str = os.getenv("SOCIAL_METRICS_USER_ID", "").strip()
    social_metrics_blog_id: str = os.getenv("SOCIAL_METRICS_BLOG_ID", "").strip()
    social_metrics_token: str = os.getenv("SOCIAL_METRICS_TOKEN", "").strip()
    social_metrics_window_days: int = safe_int("SOCIAL_METRICS_WINDOW_DAYS", 7, 1, 90)
    social_metrics_timeout_s: float = safe_float("SOCIAL_METRICS_TIMEOUT_S", 5.0, 1.0, 60.0)
    social_metrics_api_key: str = os.getenv("SOCIAL_METRICS_API_KEY", "").strip()
    social_metrics_api_url: str = os.getenv("SOCIAL_METRICS_API_URL", "").strip()
    enable_local_video: bool = safe_bool("ENABLE_LOCAL_VIDEO", True)
    local_video_model_id: str = os.getenv(
        "LOCAL_VIDEO_MODEL_ID",
        "stabilityai/stable-video-diffusion-img2vid-xt",
    )
    local_video_frames: int = safe_int("LOCAL_VIDEO_FRAMES", 24, 8, 120)
    local_video_fps: int = safe_int("LOCAL_VIDEO_FPS", 8, 1, 60)
    enable_video_generation: bool = safe_bool("ENABLE_VIDEO_GENERATION", True)
    veo3_api_base: str = os.getenv("VEO3_API_BASE", "")
    veo3_api_key: str = os.getenv("VEO3_API_KEY", "")
    veo3_timeout_s: int = safe_int("VEO3_TIMEOUT_S", 120, 30, 600)
    veo3_poll_interval_s: int = safe_int("VEO3_POLL_INTERVAL_S", 5, 1, 60)
    veo3_submit_path: str = os.getenv("VEO3_SUBMIT_PATH", "/generate")
    veo3_status_path: str = os.getenv("VEO3_STATUS_PATH", "/status/{job_id}")
    veo3_download_path: str = os.getenv("VEO3_DOWNLOAD_PATH", "/download/{job_id}")
    enable_publishing: bool = safe_bool("ENABLE_PUBLISHING", True)
    publish_dry_run: bool = safe_bool("PUBLISH_DRY_RUN", True)
    publish_timeout_s: int = safe_int("PUBLISH_TIMEOUT_S", 30, 10, 300)
    linkedin_token: str = os.getenv("LINKEDIN_TOKEN", "")
    linkedin_author: str = os.getenv("LINKEDIN_AUTHOR", "")
    x_bearer_token: str = os.getenv("X_BEARER_TOKEN", "")
    x_user_id: str = os.getenv("X_USER_ID", "")
    youtube_token: str = os.getenv("YOUTUBE_TOKEN", "")
    youtube_channel_id: str = os.getenv("YOUTUBE_CHANNEL_ID", "")
    instagram_token: str = os.getenv("INSTAGRAM_TOKEN", "")
    instagram_account_id: str = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
    enable_ads: bool = safe_bool("ENABLE_ADS", False)
    ads_dry_run: bool = safe_bool("ADS_DRY_RUN", True)
    ads_timeout_s: int = safe_int("ADS_TIMEOUT_S", 30, 10, 300)
    ads_budget_usd: int = safe_int("ADS_BUDGET_USD", 100, 1, 10000)
    ads_countries: str = os.getenv("ADS_COUNTRIES", "US")
    ads_language: str = os.getenv("ADS_LANGUAGE", "en")
    ads_audience: str = os.getenv("ADS_AUDIENCE", "")
    ads_interests: str = os.getenv("ADS_INTERESTS", "")
    google_ads_customer_id: str = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")
    google_ads_dev_token: str = os.getenv("GOOGLE_ADS_DEV_TOKEN", "")
    google_ads_client_id: str = os.getenv("GOOGLE_ADS_CLIENT_ID", "")
    google_ads_client_secret: str = os.getenv("GOOGLE_ADS_CLIENT_SECRET", "")
    google_ads_refresh_token: str = os.getenv("GOOGLE_ADS_REFRESH_TOKEN", "")
    meta_ads_access_token: str = os.getenv("META_ADS_ACCESS_TOKEN", "")
    meta_ads_account_id: str = os.getenv("META_ADS_ACCOUNT_ID", "")
    tiktok_ads_access_token: str = os.getenv("TIKTOK_ADS_ACCESS_TOKEN", "")
    tiktok_ads_account_id: str = os.getenv("TIKTOK_ADS_ACCOUNT_ID", "")
    enable_hosting: bool = safe_bool("ENABLE_HOSTING", True)
    hosting_provider: str = os.getenv("HOSTING_PROVIDER", "aws_apprunner")
    hosting_domain: str = os.getenv("HOSTING_DOMAIN", "")
    hosting_subdomain_template: str = os.getenv("HOSTING_SUBDOMAIN_TEMPLATE", "{slug}.{domain}")
    enable_deploy: bool = safe_bool("ENABLE_DEPLOY", False)
    deploy_dry_run: bool = safe_bool("DEPLOY_DRY_RUN", True)
    deploy_timeout_s: int = safe_int("DEPLOY_TIMEOUT_S", 600, 60, 3600)

    lightweight_mode: bool = safe_bool("LIGHTWEIGHT_MODE", False)
    resource_optimization: bool = safe_bool("RESOURCE_OPTIMIZATION", True)
    auto_tuning: bool = safe_bool("AUTO_TUNING", True)

    def __post_init__(self):
        """Apply lightweight optimizations after initialization"""
        # Validate base settings first before any modifications
        self._validate_base_settings()
        
        if self.lightweight_mode:
            # Apply AI-driven optimizations
            lightweight_config.apply_ai_optimizations({
                "project_type": "auto",
                "quality_priority": "balanced"
            })
            # Re-validate after lightweight modifications
            self._validate_lightweight_settings()
    
    def _validate_base_settings(self) -> None:
        """Validate critical base settings before lightweight modifications"""
        # These validations must pass before any lightweight optimizations
        critical_validations = [
            (self.run_max_count > 0, "RUN_MAX_COUNT must be positive"),
            (self.run_retention_days > 0, "RUN_RETENTION_DAYS must be positive"),
            (0 <= self.kill_threshold <= 100, "KILL_THRESHOLD must be between 0 and 100"),
            (self.mvp_build_timeout > 0, "MVP_BUILD_TIMEOUT must be positive"),
            (self.mvp_test_timeout > 0, "MVP_TEST_TIMEOUT must be positive"),
            (self.mvp_install_timeout > 0, "MVP_INSTALL_TIMEOUT must be positive"),
        ]
        
        for condition, error_msg in critical_validations:
            if not condition:
                raise ValueError(error_msg)
    
    def _validate_lightweight_settings(self) -> None:
        """Validate settings after lightweight modifications"""
        # Additional validations for lightweight mode
        lightweight_validations = [
            (self.request_timeout > 0, "REQUEST_TIMEOUT must be positive"),
            (self.max_sources > 0, "MAX_SOURCES must be positive"),
            (self.default_n_ideas > 0, "DEFAULT_N_IDEAS must be positive"),
        ]
        
        for condition, error_msg in lightweight_validations:
            if not condition:
                raise ValueError(f"Lightweight mode validation failed: {error_msg}")

def get_settings() -> Settings:
    """Get settings with validation and lazy environment loading."""
    _ensure_env_loaded()  # Ensure environment is loaded before creating settings
    settings = Settings()
    
    # Validate critical settings
    if settings.run_max_count <= 0:
        raise ValueError("RUN_MAX_COUNT must be positive")
    if settings.run_retention_days <= 0:
        raise ValueError("RUN_RETENTION_DAYS must be positive")
    if settings.kill_threshold < 0 or settings.kill_threshold > 100:
        raise ValueError("KILL_THRESHOLD must be between 0 and 100")
    
    # Validate timeouts
    if settings.mvp_build_timeout <= 0:
        raise ValueError("MVP_BUILD_TIMEOUT must be positive")
    if settings.mvp_test_timeout <= 0:
        raise ValueError("MVP_TEST_TIMEOUT must be positive")
    if settings.mvp_install_timeout <= 0:
        raise ValueError("MVP_INSTALL_TIMEOUT must be positive")
    
    # Validate rate limits
    if settings.run_rate_limit_per_min <= 0:
        raise ValueError("RUN_RATE_LIMIT_PER_MIN must be positive")
    if settings.run_rate_limit_burst <= 0:
        raise ValueError("RUN_RATE_LIMIT_BURST must be positive")
    
    # Validate URLs
    _validate_url(settings.ollama_base_url, "OLLAMA_BASE_URL")
    _validate_url(settings.mvp_dev_base_url, "MVP_DEV_BASE_URL")
    
    # Validate ports
    _validate_port(settings.api_port, "API_PORT")
    _validate_port(settings.ui_port, "UI_PORT")
    _validate_port(settings.worker_port, "WORKER_PORT")
    
    # Validate model names
    _validate_model_name(settings.general_model, "GENERAL_MODEL")
    _validate_model_name(settings.code_model, "CODE_MODEL")
    
    # Validate paths
    _validate_path(settings.runs_dir, "RUNS_DIR")
    _validate_path(settings.data_dir, "DATA_DIR")
    _validate_path(settings.config_dir, "CONFIG_DIR")
    _validate_path(settings.knowledge_dir, "KNOWLEDGE_DIR")
    
    return settings

def _validate_url(url: str, name: str) -> None:
    """Validate URL format"""
    if not url:
        raise ValueError(f"{name} cannot be empty")
    
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"{name} must be a valid URL: {url}")

def _validate_port(port: int, name: str) -> None:
    """Validate port number"""
    if port < 1 or port > 65535:
        raise ValueError(f"{name} must be between 1 and 65535, got: {port}")

def _validate_model_name(model: str, name: str) -> None:
    """Validate model name format"""
    if not model:
        raise ValueError(f"{name} cannot be empty")
    
    # Basic validation for common model name patterns (allow colons for version tags)
    import re
    if not re.match(r'^[a-zA-Z0-9._:-]+$', model):
        raise ValueError(f"{name} contains invalid characters: {model}")

def _validate_path(path: Path, name: str) -> None:
    """Validate path configuration"""
    if not path:
        raise ValueError(f"{name} cannot be empty")
    
    # Ensure path is within reasonable bounds
    try:
        path.resolve()
    except Exception as e:
        raise ValueError(f"{name} contains invalid path: {e}")


def _parse_iso_datetime(value: str | None) -> datetime | None:
    """
    Parse ISO datetime string with validation.
    
    Args:
        value: ISO datetime string to parse
        
    Returns:
        Parsed datetime with UTC timezone or None if invalid
        
    Expected formats:
        - 2024-01-31T12:34:56 (ISO 8601 basic)
        - 2024-01-31T12:34:56Z (with UTC)
        - 2024-01-31T12:34:56+00:00 (with timezone)
        - 20240131T123456 (compact)
    """
    if not value:
        return None
    
    # Basic format validation
    if not isinstance(value, str):
        return None
    
    # Check for reasonable length (ISO datetime should be around 16-25 chars)
    if len(value) < 10 or len(value) > 35:
        return None
    
    # Check for valid ISO datetime patterns
    iso_patterns = [
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$',  # 2024-01-31T12:34:56
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$',  # 2024-01-31T12:34:56Z
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$',  # 2024-01-31T12:34:56+00:00
        r'^\d{8}T\d{6}$',  # 20240131T123456
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{1,6}$',  # 2024-01-31T12:34:56.123456
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{1,6}Z$',  # 2024-01-31T12:34:56.123456Z
    ]
    
    if not any(re.match(pattern, value) for pattern in iso_patterns):
        return None
    
    try:
        # Use datetime.fromisoformat which handles most ISO 8601 formats
        parsed = datetime.fromisoformat(value)
        
        # Additional validation: check if the parsed date is reasonable
        now = datetime.now(UTC)
        # Don't allow dates more than 10 years in the past
        past_boundary = now.replace(year=now.year - 10)
        # Ensure both datetimes are timezone-aware for comparison
        if parsed.tzinfo is None:
            parsed_utc = parsed.replace(tzinfo=UTC)
        else:
            parsed_utc = parsed.astimezone(UTC)
            
        if parsed_utc.year < past_boundary.year:
            return None
        # Don't allow dates more than 10 years in future
        if parsed_utc.year >= now.year + 10:
            return None
        
        # Ensure timezone is set, default to UTC if not
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
            
        return parsed
    except ValueError as e:
        # Log specific parsing error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to parse ISO datetime '{value}': {e}")
        return None
    except Exception as e:
        # Catch any other unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error parsing ISO datetime '{value}': {e}")
        return None


def previous_secret_allowed(
    *,
    previous_value: str,
    current_value: str,
    expires_at: str,
    enforce_rotation: bool,
) -> tuple[bool, str]:
    if not previous_value:
        return False, "not_configured"
    if previous_value == current_value:
        return False, "same_as_current"
    if not enforce_rotation:
        return True, "allowed_legacy"
    expiry = _parse_iso_datetime(expires_at)
    if expiry is None:
        return False, "missing_or_invalid_expiry"
    now = datetime.now(UTC)
    if now >= expiry:
        return False, "expired"
    return True, "within_grace_period"


_SENSITIVE_KEY_PATTERNS = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "cookie",
)


def _mask_secret(value: str) -> str:
    if not value:
        return "***"
    if len(value) <= 8:
        return "***"  # Don't show any characters for short secrets
    return f"{value[:2]}***{value[-2:]}"


def redact_value(value):
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if any(pattern in key_text for pattern in _SENSITIVE_KEY_PATTERNS):
                out[key] = _mask_secret(str(item))
            else:
                out[key] = redact_value(item)
        return out
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    if isinstance(value, str):
        text = value
        text = re.sub(
            r"(?i)\b(api[_-]?key|token|secret|password)\b\s*[:=]\s*['\"]?([A-Za-z0-9_\-\.=+/]{6,})['\"]?",
            lambda m: f"{m.group(1)}={_mask_secret(m.group(2))}",
            text,
        )
        text = re.sub(
            r"(?i)\b(bearer)\s+([A-Za-z0-9_\-\.=+/]{6,})",
            lambda m: f"{m.group(1)} {_mask_secret(m.group(2))}",
            text,
        )
        return text
    return value


def validate_secrets(settings: Settings) -> dict:
    checks: list[dict] = []

    def _check(name: str, enabled: bool, required: dict[str, str], note: str = "") -> None:
        missing = [key for key, value in required.items() if not value]
        checks.append(
            {
                "name": name,
                "enabled": enabled,
                "missing": missing,
                "ok": (not enabled) or len(missing) == 0,
                "note": note,
            }
        )

    if settings.enable_publishing and not settings.publish_dry_run:
        _check(
            "publishing_x",
            True,
            {
                "X_BEARER_TOKEN": settings.x_bearer_token,
                "X_USER_ID": settings.x_user_id,
            },
            "X posting requires both bearer token and user id.",
        )
        _check(
            "publishing_linkedin",
            True,
            {
                "LINKEDIN_TOKEN": settings.linkedin_token,
                "LINKEDIN_AUTHOR": settings.linkedin_author,
            },
            "LinkedIn posting requires token and author URN.",
        )
        _check(
            "publishing_youtube",
            True,
            {
                "YOUTUBE_TOKEN": settings.youtube_token,
                "YOUTUBE_CHANNEL_ID": settings.youtube_channel_id,
            },
            "YouTube upload requires token + channel id.",
        )
        _check(
            "publishing_instagram",
            True,
            {
                "INSTAGRAM_TOKEN": settings.instagram_token,
                "INSTAGRAM_ACCOUNT_ID": settings.instagram_account_id,
            },
            "Instagram posting requires token + account id.",
        )
    else:
        _check("publishing", settings.enable_publishing, {}, "Dry-run or publishing disabled.")

    if settings.enable_ads and not settings.ads_dry_run:
        _check(
            "ads_google",
            True,
            {
                "GOOGLE_ADS_CUSTOMER_ID": settings.google_ads_customer_id,
                "GOOGLE_ADS_DEV_TOKEN": settings.google_ads_dev_token,
                "GOOGLE_ADS_CLIENT_ID": settings.google_ads_client_id,
                "GOOGLE_ADS_CLIENT_SECRET": settings.google_ads_client_secret,
                "GOOGLE_ADS_REFRESH_TOKEN": settings.google_ads_refresh_token,
            },
            "Google Ads requires customer id, dev token, client id/secret, refresh token.",
        )
        _check(
            "ads_meta",
            True,
            {
                "META_ADS_ACCESS_TOKEN": settings.meta_ads_access_token,
                "META_ADS_ACCOUNT_ID": settings.meta_ads_account_id,
            },
            "Meta Ads requires access token + ad account id.",
        )
        _check(
            "ads_tiktok",
            True,
            {
                "TIKTOK_ADS_ACCESS_TOKEN": settings.tiktok_ads_access_token,
                "TIKTOK_ADS_ACCOUNT_ID": settings.tiktok_ads_account_id,
            },
            "TikTok Ads requires access token + ad account id.",
        )
    else:
        _check("ads", settings.enable_ads, {}, "Dry-run or ads disabled.")

    if settings.enable_hosting:
        provider = (settings.hosting_provider or "").strip().lower()
        env = os.environ
        provider_requirements = {
            "aws_apprunner": {
                "AWS_ACCESS_KEY_ID": env.get("AWS_ACCESS_KEY_ID", ""),
                "AWS_SECRET_ACCESS_KEY": env.get("AWS_SECRET_ACCESS_KEY", ""),
                "AWS_REGION": env.get("AWS_REGION", ""),
            },
            "vercel": {"VERCEL_TOKEN": env.get("VERCEL_TOKEN", "")},
            "netlify": {"NETLIFY_AUTH_TOKEN": env.get("NETLIFY_AUTH_TOKEN", "")},
            "fly": {"FLY_API_TOKEN": env.get("FLY_API_TOKEN", "")},
            "render": {"RENDER_API_KEY": env.get("RENDER_API_KEY", "")},
        }
        required = provider_requirements.get(provider, {})
        _check(
            f"hosting_{provider or 'unknown'}",
            True,
            required,
            "Hosting provider credentials required for deploy.",
        )
    else:
        _check("hosting", False, {}, "Hosting disabled.")

    overall_ok = all(item["ok"] for item in checks if item["enabled"])
    return {"ok": overall_ok, "checks": checks}


def validate_prod_mode(settings: Settings) -> dict:
    checks: list[dict] = []

    def _check(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    if not settings.prod_mode:
        _check("prod_mode", True, "PROD_MODE=false (checklist not enforced).")
        return {"ok": True, "checks": checks}

    _check("api_key_present", bool(settings.api_key), "API_KEY must be set in prod mode.")
    _check("ui_password_present", bool(settings.ui_password), "UI_PASSWORD must be set in prod mode.")

    if settings.enable_publishing:
        _check("publish_dry_run_disabled", not settings.publish_dry_run, "Set PUBLISH_DRY_RUN=false in prod mode.")
    if settings.enable_ads:
        _check("ads_dry_run_disabled", not settings.ads_dry_run, "Set ADS_DRY_RUN=false in prod mode.")
    if settings.enable_deploy:
        _check("deploy_dry_run_disabled", not settings.deploy_dry_run, "Set DEPLOY_DRY_RUN=false in prod mode.")

    api_prev_ok, api_prev_reason = previous_secret_allowed(
        previous_value=settings.api_key_prev,
        current_value=settings.api_key,
        expires_at=settings.api_key_prev_expires_at,
        enforce_rotation=settings.enforce_key_rotation,
    )
    if settings.api_key_prev:
        _check(
            "api_key_prev_rotation",
            api_prev_ok,
            (
                "API_KEY_PREV must differ from API_KEY and have a valid future "
                "API_KEY_PREV_EXPIRES_AT while rotation is enforced."
                if not api_prev_ok
                else f"Previous API key accepted ({api_prev_reason})."
            ),
        )

    ui_prev_ok, ui_prev_reason = previous_secret_allowed(
        previous_value=settings.ui_password_prev,
        current_value=settings.ui_password,
        expires_at=settings.ui_password_prev_expires_at,
        enforce_rotation=settings.enforce_key_rotation,
    )
    if settings.ui_password_prev:
        _check(
            "ui_password_prev_rotation",
            ui_prev_ok,
            (
                "UI_PASSWORD_PREV must differ from UI_PASSWORD and have a valid future "
                "UI_PASSWORD_PREV_EXPIRES_AT while rotation is enforced."
                if not ui_prev_ok
                else f"Previous UI password accepted ({ui_prev_reason})."
            ),
        )

    secret_validation = validate_secrets(settings)
    for item in secret_validation.get("checks", []):
        if item.get("enabled"):
            missing = item.get("missing") or []
            _check(
                f"secrets_{item.get('name')}",
                bool(item.get("ok")),
                item.get("note") or (f"Missing: {', '.join(missing)}" if missing else "ok"),
            )

    overall_ok = all(item["ok"] for item in checks)
    return {"ok": overall_ok, "checks": checks}
