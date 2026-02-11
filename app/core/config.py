import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]

@dataclass
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    general_model: str = os.getenv("GENERAL_MODEL", "llama3.1:8b")
    code_model: str = os.getenv("CODE_MODEL", "qwen2.5-coder:7b")
    general_model_fallbacks: str = os.getenv("GENERAL_MODEL_FALLBACKS", "")
    code_model_fallbacks: str = os.getenv("CODE_MODEL_FALLBACKS", "")

    default_n_ideas: int = int(os.getenv("DEFAULT_N_IDEAS", "10"))
    fast_mode: bool = os.getenv("FAST_MODE", "false").lower() == "true"
    mvp_build_command: str = os.getenv("MVP_BUILD_COMMAND", "")
    mvp_test_command: str = os.getenv("MVP_TEST_COMMAND", "")
    mvp_install_command: str = os.getenv("MVP_INSTALL_COMMAND", "")
    mvp_dev_command: str = os.getenv("MVP_DEV_COMMAND", "")
    mvp_dev_base_url: str = os.getenv("MVP_DEV_BASE_URL", "http://127.0.0.1:3000")
    mvp_dev_startup_timeout: int = int(os.getenv("MVP_DEV_STARTUP_TIMEOUT", "35"))
    mvp_dev_check_paths: str = os.getenv("MVP_DEV_CHECK_PATHS", "/,/api/status,/api/health")
    mvp_install_timeout: int = int(os.getenv("MVP_INSTALL_TIMEOUT", "600"))
    mvp_build_timeout: int = int(os.getenv("MVP_BUILD_TIMEOUT", "300"))
    mvp_test_timeout: int = int(os.getenv("MVP_TEST_TIMEOUT", "300"))
    mvp_force_autofix: bool = os.getenv("MVP_FORCE_AUTOFIX", "false").lower() == "true"
    mvp_disable_llm: bool = os.getenv("MVP_DISABLE_LLM", "false").lower() == "true"
    frontend_style: str = os.getenv("FRONTEND_STYLE", "startup_clean")
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "20"))
    rate_limit_per_domain: int = int(os.getenv("RATE_LIMIT_PER_DOMAIN", "2"))
    max_sources: int = int(os.getenv("MAX_SOURCES", "8"))
    retry_max_attempts: int = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
    retry_min_wait: int = int(os.getenv("RETRY_MIN_WAIT", "1"))
    retry_max_wait: int = int(os.getenv("RETRY_MAX_WAIT", "6"))
    min_pages: int = int(os.getenv("MIN_PAGES", "3"))
    min_pains: int = int(os.getenv("MIN_PAINS", "3"))
    min_competitors: int = int(os.getenv("MIN_COMPETITORS", "1"))
    min_avg_text_len: int = int(os.getenv("MIN_AVG_TEXT_LEN", "200"))
    min_unique_domains: int = int(os.getenv("MIN_UNIQUE_DOMAINS", "2"))
    market_signal_threshold: int = int(os.getenv("MARKET_SIGNAL_THRESHOLD", "40"))
    signal_sources_target: int = int(os.getenv("SIGNAL_SOURCES_TARGET", "6"))
    signal_pains_target: int = int(os.getenv("SIGNAL_PAINS_TARGET", "8"))
    signal_domain_target: int = int(os.getenv("SIGNAL_DOMAIN_TARGET", "4"))
    signal_repeat_target: int = int(os.getenv("SIGNAL_REPEAT_TARGET", "2"))
    signal_pages_target: int = int(os.getenv("SIGNAL_PAGES_TARGET", "12"))
    signal_cluster_density_target: int = int(os.getenv("SIGNAL_CLUSTER_DENSITY_TARGET", "3"))
    signal_novel_keywords_target: int = int(os.getenv("SIGNAL_NOVEL_KEYWORDS_TARGET", "8"))
    signal_quality_threshold: int = int(os.getenv("SIGNAL_QUALITY_THRESHOLD", "45"))
    signal_recency_days: int = int(os.getenv("SIGNAL_RECENCY_DAYS", "365"))
    idea_actionability_min_score: int = int(os.getenv("IDEA_ACTIONABILITY_MIN_SCORE", "55"))
    idea_actionability_adjustment_max: int = int(os.getenv("IDEA_ACTIONABILITY_ADJUSTMENT_MAX", "12"))
    idea_actionability_require_eligible_top: bool = os.getenv("IDEA_ACTIONABILITY_REQUIRE_ELIGIBLE_TOP", "false").lower() == "true"
    learning_history_max_runs: int = int(os.getenv("LEARNING_HISTORY_MAX_RUNS", "200"))
    learning_exploration_rate: float = float(os.getenv("LEARNING_EXPLORATION_RATE", "0.18"))
    learning_success_bonus_max: int = int(os.getenv("LEARNING_SUCCESS_BONUS_MAX", "8"))
    learning_failure_penalty_max: int = int(os.getenv("LEARNING_FAILURE_PENALTY_MAX", "10"))
    learning_novelty_bonus_max: int = int(os.getenv("LEARNING_NOVELTY_BONUS_MAX", "6"))
    learning_clone_penalty_start: float = float(os.getenv("LEARNING_CLONE_PENALTY_START", "0.75"))
    primary_icp: str = os.getenv("PRIMARY_ICP", "Founders B2B SaaS pre-seed")
    primary_icp_keywords: str = os.getenv(
        "PRIMARY_ICP_KEYWORDS",
        "founder,founders,b2b,saas,pre-seed,startup,startups,small team,operators",
    )
    icp_alignment_bonus_max: int = int(os.getenv("ICP_ALIGNMENT_BONUS_MAX", "8"))
    enable_self_healing: bool = os.getenv("ENABLE_SELF_HEALING", "true").lower() == "true"
    stage_retry_attempts: int = int(os.getenv("STAGE_RETRY_ATTEMPTS", "2"))
    stage_retry_backoff_sec: float = float(os.getenv("STAGE_RETRY_BACKOFF_SEC", "1.0"))

    runs_dir: Path = BASE_DIR / os.getenv("RUNS_DIR", "runs")
    data_dir: Path = BASE_DIR / os.getenv("DATA_DIR", "data")
    config_dir: Path = BASE_DIR / os.getenv("CONFIG_DIR", "configs")
    knowledge_dir: Path = BASE_DIR / os.getenv("KNOWLEDGE_DIR", "knowledge")
    enable_progressive_cycles: bool = os.getenv("ENABLE_PROGRESSIVE_CYCLES", "true").lower() == "true"
    enable_logo_diffusion: bool = os.getenv("ENABLE_LOGO_DIFFUSION", "false").lower() == "true"
    logo_model_id: str = os.getenv("LOGO_MODEL_ID", "runwayml/stable-diffusion-v1-5")
    logo_image_size: int = int(os.getenv("LOGO_IMAGE_SIZE", "512"))
    logo_steps: int = int(os.getenv("LOGO_STEPS", "28"))
    logo_guidance: float = float(os.getenv("LOGO_GUIDANCE", "7.0"))
    logo_seed: int = int(os.getenv("LOGO_SEED", "0"))
    logo_device: str = os.getenv("LOGO_DEVICE", "cuda")

    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    ui_host: str = os.getenv("UI_HOST", "127.0.0.1")
    ui_port: int = int(os.getenv("UI_PORT", "8501"))
    ui_password: str = os.getenv("UI_PASSWORD", "")
    ui_password_prev: str = os.getenv("UI_PASSWORD_PREV", "")
    ui_password_prev_expires_at: str = os.getenv("UI_PASSWORD_PREV_EXPIRES_AT", "")
    kill_threshold: int = int(os.getenv("KILL_THRESHOLD", "55"))
    api_key: str = os.getenv("API_KEY", "")
    api_key_prev: str = os.getenv("API_KEY_PREV", "")
    api_key_prev_expires_at: str = os.getenv("API_KEY_PREV_EXPIRES_AT", "")
    enforce_key_rotation: bool = os.getenv("ENFORCE_KEY_ROTATION", "true").lower() == "true"
    prod_mode: bool = os.getenv("PROD_MODE", "false").lower() == "true"
    require_prod_checklist: bool = os.getenv("REQUIRE_PROD_CHECKLIST", "true").lower() == "true"
    run_rate_limit_per_min: int = int(os.getenv("RUN_RATE_LIMIT_PER_MIN", "6"))
    run_rate_limit_burst: int = int(os.getenv("RUN_RATE_LIMIT_BURST", "3"))
    run_retention_days: int = int(os.getenv("RUN_RETENTION_DAYS", "30"))
    run_max_count: int = int(os.getenv("RUN_MAX_COUNT", "200"))
    run_compress_after_days: int = int(os.getenv("RUN_COMPRESS_AFTER_DAYS", "7"))
    run_maintenance_interval_min: int = int(os.getenv("RUN_MAINTENANCE_INTERVAL_MIN", "60"))
    run_archive_dirs: str = os.getenv(
        "RUN_ARCHIVE_DIRS",
        "repo_skeleton,landing_page,content_pack,mvp_repo,mvp_cycles,project_build",
    )
    backup_dir: str = os.getenv("BACKUP_DIR", "data/backups")
    backup_retention_days: int = int(os.getenv("BACKUP_RETENTION_DAYS", "14"))
    audit_log_file: str = os.getenv("AUDIT_LOG_FILE", "data/audit.log")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    rq_queue_name: str = os.getenv("RQ_QUEUE_NAME", "asmblr")
    rq_default_timeout: int = int(os.getenv("RQ_DEFAULT_TIMEOUT", "7200"))
    run_max_concurrent: int = int(os.getenv("RUN_MAX_CONCURRENT", "1"))
    run_queue_backoff_sec: int = int(os.getenv("RUN_QUEUE_BACKOFF_SEC", "30"))
    worker_port: int = int(os.getenv("WORKER_PORT", "8001"))
    enable_app_packaging: bool = os.getenv("ENABLE_APP_PACKAGING", "true").lower() == "true"
    app_package_targets: str = os.getenv(
        "APP_PACKAGE_TARGETS",
        "mvp_repo,landing_page,content_pack,distribution,hosting,brand_direction.md,brand_identity.json,logo.svg,launch_checklist.md,prd.md,tech_spec.md",
    )
    enable_distribution: bool = os.getenv("ENABLE_DISTRIBUTION", "true").lower() == "true"
    campaign_auto_expand_assets: bool = os.getenv("CAMPAIGN_AUTO_EXPAND_ASSETS", "true").lower() == "true"
    campaign_target_assets: int = int(os.getenv("CAMPAIGN_TARGET_ASSETS", "30"))
    campaign_posts_target: int = int(os.getenv("CAMPAIGN_POSTS_TARGET", "12"))
    campaign_ads_target: int = int(os.getenv("CAMPAIGN_ADS_TARGET", "12"))
    campaign_outreach_target: int = int(os.getenv("CAMPAIGN_OUTREACH_TARGET", "4"))
    campaign_videos_target: int = int(os.getenv("CAMPAIGN_VIDEOS_TARGET", "2"))
    campaign_boost_from_organic: bool = os.getenv("CAMPAIGN_BOOST_FROM_ORGANIC", "true").lower() == "true"
    campaign_organic_top_assets: int = int(os.getenv("CAMPAIGN_ORGANIC_TOP_ASSETS", "6"))
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "")
    public_base_domain: str = os.getenv("PUBLIC_BASE_DOMAIN", "")
    public_url_template: str = os.getenv("PUBLIC_URL_TEMPLATE", "https://{slug}.{domain}")
    offline_creation: bool = os.getenv("OFFLINE_CREATION", "false").lower() == "true"
    enable_local_social_images: bool = os.getenv("ENABLE_LOCAL_SOCIAL_IMAGES", "true").lower() == "true"
    social_image_model_id: str = os.getenv("SOCIAL_IMAGE_MODEL_ID", "runwayml/stable-diffusion-v1-5")
    social_image_size: int = int(os.getenv("SOCIAL_IMAGE_SIZE", "768"))
    social_image_steps: int = int(os.getenv("SOCIAL_IMAGE_STEPS", "28"))
    social_image_guidance: float = float(os.getenv("SOCIAL_IMAGE_GUIDANCE", "7.0"))
    social_image_seed: int = int(os.getenv("SOCIAL_IMAGE_SEED", "0"))
    enable_local_video: bool = os.getenv("ENABLE_LOCAL_VIDEO", "true").lower() == "true"
    local_video_model_id: str = os.getenv(
        "LOCAL_VIDEO_MODEL_ID",
        "stabilityai/stable-video-diffusion-img2vid-xt",
    )
    local_video_frames: int = int(os.getenv("LOCAL_VIDEO_FRAMES", "24"))
    local_video_fps: int = int(os.getenv("LOCAL_VIDEO_FPS", "8"))
    enable_video_generation: bool = os.getenv("ENABLE_VIDEO_GENERATION", "true").lower() == "true"
    veo3_api_base: str = os.getenv("VEO3_API_BASE", "")
    veo3_api_key: str = os.getenv("VEO3_API_KEY", "")
    veo3_timeout_s: int = int(os.getenv("VEO3_TIMEOUT_S", "120"))
    veo3_poll_interval_s: int = int(os.getenv("VEO3_POLL_INTERVAL_S", "5"))
    veo3_submit_path: str = os.getenv("VEO3_SUBMIT_PATH", "/generate")
    veo3_status_path: str = os.getenv("VEO3_STATUS_PATH", "/status/{job_id}")
    veo3_download_path: str = os.getenv("VEO3_DOWNLOAD_PATH", "/download/{job_id}")
    enable_publishing: bool = os.getenv("ENABLE_PUBLISHING", "true").lower() == "true"
    publish_dry_run: bool = os.getenv("PUBLISH_DRY_RUN", "true").lower() == "true"
    publish_timeout_s: int = int(os.getenv("PUBLISH_TIMEOUT_S", "30"))
    linkedin_token: str = os.getenv("LINKEDIN_TOKEN", "")
    linkedin_author: str = os.getenv("LINKEDIN_AUTHOR", "")
    x_bearer_token: str = os.getenv("X_BEARER_TOKEN", "")
    x_user_id: str = os.getenv("X_USER_ID", "")
    youtube_token: str = os.getenv("YOUTUBE_TOKEN", "")
    youtube_channel_id: str = os.getenv("YOUTUBE_CHANNEL_ID", "")
    instagram_token: str = os.getenv("INSTAGRAM_TOKEN", "")
    instagram_account_id: str = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
    enable_ads: bool = os.getenv("ENABLE_ADS", "false").lower() == "true"
    ads_dry_run: bool = os.getenv("ADS_DRY_RUN", "true").lower() == "true"
    ads_timeout_s: int = int(os.getenv("ADS_TIMEOUT_S", "30"))
    ads_budget_usd: int = int(os.getenv("ADS_BUDGET_USD", "100"))
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
    enable_hosting: bool = os.getenv("ENABLE_HOSTING", "true").lower() == "true"
    hosting_provider: str = os.getenv("HOSTING_PROVIDER", "aws_apprunner")
    hosting_domain: str = os.getenv("HOSTING_DOMAIN", "")
    hosting_subdomain_template: str = os.getenv("HOSTING_SUBDOMAIN_TEMPLATE", "{slug}.{domain}")
    enable_deploy: bool = os.getenv("ENABLE_DEPLOY", "false").lower() == "true"
    deploy_dry_run: bool = os.getenv("DEPLOY_DRY_RUN", "true").lower() == "true"
    deploy_timeout_s: int = int(os.getenv("DEPLOY_TIMEOUT_S", "600"))


def get_settings() -> Settings:
    return Settings()


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
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{1,3}$',  # 2024-01-31T12:34:56.789
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{1,3}Z$',  # 2024-01-31T12:34:56.789Z
    ]
    
    if not any(re.match(pattern, value) for pattern in iso_patterns):
        return None
    
    try:
        # Use datetime.fromisoformat which handles most ISO 8601 formats
        parsed = datetime.fromisoformat(value)
        
        # Additional validation: check if the parsed date is reasonable
        now = datetime.now(timezone.utc)
        # Don't allow dates more than 10 years in the past
        past_boundary = now.replace(year=now.year - 10)
        # Ensure both datetimes are timezone-aware for comparison
        if parsed.tzinfo is None:
            parsed_utc = parsed.replace(tzinfo=timezone.utc)
        else:
            parsed_utc = parsed.astimezone(timezone.utc)
            
        if parsed_utc < past_boundary.replace(tzinfo=timezone.utc):
            return None
        # Don't allow dates more than 10 years in the future
        future_boundary = now.replace(year=now.year + 10)
        if parsed_utc > future_boundary.replace(tzinfo=timezone.utc):
            return None
        
        # Ensure timezone is set, default to UTC if not
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
            
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
    now = datetime.now(timezone.utc)
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
    if len(value) <= 6:
        return "***"
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
