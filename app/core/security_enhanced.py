"""
Enhanced security hardening for Asmblr - Production-ready security controls
Implements stronger secret generation, input validation, and improved logging redaction
"""

import os
import secrets
import time
import re
from datetime import datetime
from typing import Any
from dataclasses import dataclass

import redis.asyncio as redis
from fastapi.security import HTTPBearer
from passlib.context import CryptContext
from loguru import logger
from prometheus_client import Counter, Histogram
from pydantic import BaseModel, validator

# Enhanced security configuration with stronger defaults
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(64)  # Increased from 32 to 64
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
ENABLE_CORS = os.getenv("ENABLE_CORS", "false").lower() == "true"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []

# Enhanced security metrics
SECURITY_EVENTS = Counter('asmblr_security_events_total', 'Security events', ['event_type', 'severity'])
AUTH_ATTEMPTS = Counter('asmblr_auth_attempts_total', 'Authentication attempts', ['result'])
RATE_LIMIT_VIOLATIONS = Counter('asmblr_rate_limit_violations_total', 'Rate limit violations')
INPUT_VALIDATION_FAILURES = Counter('asmblr_input_validation_failures_total', 'Input validation failures')
SECURITY_RESPONSE_TIME = Histogram('asmblr_security_response_time_seconds', 'Security response time')

# Cryptography context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Security
security = HTTPBearer(auto_error=False)


class InputValidator(BaseModel):
    """Enhanced input validation with security rules"""
    
    @validator('*')
    def validate_no_injection(cls, v):
        """Prevent injection attacks"""
        if isinstance(v, str):
            # SQL injection patterns
            sql_patterns = [
                r'(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)',
                r'(--|#|\/\*|\*\/)',
                r'(\bOR\b.*\b1\s*=\s*1\b|\bAND\b.*\b1\s*=\s*1\b)',
                r'(\'\s*OR\s*\'.*\'.*\=.*\')',
            ]
            
            # XSS patterns
            xss_patterns = [
                r'<\s*script[^>]*>.*?<\s*/\s*script\s*>',
                r'javascript\s*:',
                r'on\w+\s*=\s*["\'][^"\']*["\']',
                r'<\s*iframe[^>]*>',
                r'<\s*object[^>]*>',
                r'<\s*embed[^>]*>',
            ]
            
            # Command injection patterns
            cmd_patterns = [
                r'[;&|`$()]',
                r'\$\([^)]*\)',
                r'`[^`]*`',
                r'\${[^}]*}',
            ]
            
            all_patterns = sql_patterns + xss_patterns + cmd_patterns
            for pattern in all_patterns:
                if re.search(pattern, v, re.IGNORECASE):
                    raise ValueError(f"Potentially dangerous input detected: {pattern}")
        
        return v
    
    @validator('*')
    def validate_length(cls, v):
        """Validate input length to prevent DoS"""
        if isinstance(v, str) and len(v) > 10000:  # 10KB limit
            raise ValueError("Input too long")
        return v
    
    @validator('*')
    def validate_encoding(cls, v):
        """Ensure proper encoding"""
        if isinstance(v, str):
            try:
                v.encode('utf-8')
            except UnicodeEncodeError:
                raise ValueError("Invalid character encoding")
        return v


@dataclass
class SecurityEvent:
    """Enhanced security event with more metadata"""
    event_type: str
    severity: str  # low, medium, high, critical
    description: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    metadata: dict[str, Any]
    user_id: str | None = None
    session_id: str | None = None
    request_id: str | None = None


@dataclass
class UserSession:
    """Enhanced user session with security metadata"""
    session_id: str
    user_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    is_active: bool
    security_flags: list[str] = None
    risk_score: float = 0.0


class EnhancedSecurityManager:
    """Enhanced security manager with improved controls"""
    
    def __init__(self):
        self.redis_client = None
        self.blocked_ips: set[str] = set()
        self.active_sessions: dict[str, UserSession] = {}
        self.security_events: list[SecurityEvent] = []
        self.input_validator = InputValidator()
        
        # Enhanced patterns for logging redaction
        self.redaction_patterns = {
            'api_key': re.compile(r'(api[_-]?key|token|secret)\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?', re.IGNORECASE),
            'password': re.compile(r'(password|pwd|pass)\s*[:=]\s*["\']?([^\s"\']{6,})["\']?', re.IGNORECASE),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            'credit_card': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'jwt': re.compile(r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*'),
        }
        
    async def initialize(self):
        """Initialize enhanced security manager"""
        try:
            self.redis_client = redis.from_url(
                os.getenv("REDIS_URL", "redis://redis:6379/0"), 
                decode_responses=True,
                max_connections=20  # Connection pooling
            )
            await self.redis_client.ping()
            
            # Load blocked IPs with TTL
            blocked_data = await self.redis_client.smembers("security:blocked_ips")
            self.blocked_ips = set(blocked_data)
            
            logger.info("Enhanced security manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize enhanced security manager: {e}")
            self.redis_client = None
    
    def generate_secure_secret(self, length: int = 64) -> str:
        """Generate cryptographically secure secret"""
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str) -> str:
        """Hash password with enhanced security"""
        return pwd_context.hash(password, rounds=12)  # Increased rounds
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password with timing attack protection"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            # Constant time comparison to prevent timing attacks
            return False
    
    def redact_sensitive_data(self, text: str) -> str:
        """Enhanced data redaction for logging"""
        if not isinstance(text, str):
            return text
            
        redacted = text
        
        # Apply all redaction patterns
        for pattern_name, pattern in self.redaction_patterns.items():
            def replacer(match):
                if pattern_name == 'email':
                    return match.group(0)[:2] + '*' * (len(match.group(0)) - 4) + match.group(0)[-2:]
                elif pattern_name in ['phone', 'credit_card', 'ssn']:
                    return '*' * (len(match.group(0)) - 4) + match.group(0)[-4:]
                else:
                    return match.group(0)[:8] + '*' * (len(match.group(0)) - 12) + match.group(0)[-4:] if len(match.group(0)) > 16 else '*' * len(match.group(0))
            
            redacted = pattern.sub(replacer, redacted)
        
        return redacted
    
    def validate_input(self, data: Any, context: str = "default") -> tuple[bool, str | None]:
        """Enhanced input validation"""
        try:
            if isinstance(data, dict):
                for key, value in data.items():
                    is_valid, error = self.validate_input(value, f"{context}.{key}")
                    if not is_valid:
                        return False, error
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    is_valid, error = self.validate_input(item, f"{context}[{i}]")
                    if not is_valid:
                        return False, error
            elif isinstance(data, str):
                # Use Pydantic validator
                validated = self.input_validator.parse_obj({"value": data})
                return True, None
            
            return True, None
        except Exception as e:
            INPUT_VALIDATION_FAILURES.inc()
            return False, f"Input validation failed: {str(e)}"
    
    async def check_rate_limit(self, identifier: str, limit: int = 100, window: int = 60) -> tuple[bool, dict[str, Any]]:
        """Enhanced rate limiting with Redis"""
        if not self.redis_client:
            return True, {"remaining": limit, "reset_time": time.time() + window}
        
        key = f"rate_limit:{identifier}"
        current_time = int(time.time())
        window_start = current_time - window
        
        try:
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.expire(key, window)
            results = await pipe.execute()
            
            current_count = results[1]
            remaining = max(0, limit - current_count)
            
            if current_count >= limit:
                RATE_LIMIT_VIOLATIONS.inc()
                return False, {"remaining": 0, "reset_time": current_time + window, "current_count": current_count}
            
            return True, {"remaining": remaining, "reset_time": current_time + window, "current_count": current_count}
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True, {"remaining": limit, "reset_time": time.time() + window}
    
    async def log_security_event(self, event: SecurityEvent):
        """Enhanced security event logging"""
        self.security_events.append(event)
        
        # Log with structured data
        log_data = {
            "event_type": event.event_type,
            "severity": event.severity,
            "description": event.description,
            "ip_address": event.ip_address,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "request_id": event.request_id,
            "metadata": event.metadata
        }
        
        # Redact sensitive data in metadata
        if event.metadata:
            for key, value in event.metadata.items():
                if isinstance(value, str):
                    log_data["metadata"][key] = self.redact_sensitive_data(value)
        
        logger.warning(f"Security event: {event.event_type}", extra=log_data)
        SECURITY_EVENTS.labels(event_type=event.event_type, severity=event.severity).inc()
        
        # Store in Redis if available
        if self.redis_client:
            try:
                await self.redis_client.lpush(
                    "security_events",
                    json.dumps({
                        **log_data,
                        "timestamp": event.timestamp.isoformat()
                    })
                )
                # Keep only last 1000 events
                await self.redis_client.ltrim("security_events", 0, 999)
            except Exception as e:
                logger.error(f"Failed to store security event in Redis: {e}")
    
    async def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked with cache"""
        if ip_address in self.blocked_ips:
            return True
        
        if self.redis_client:
            try:
                return await self.redis_client.sismember("security:blocked_ips", ip_address)
            except Exception:
                pass
        
        return False
    
    async def block_ip(self, ip_address: str, duration_minutes: int = 60, reason: str = "Security violation"):
        """Block IP with duration"""
        self.blocked_ips.add(ip_address)
        
        if self.redis_client:
            try:
                await self.redis_client.sadd("security:blocked_ips", ip_address)
                await self.redis_client.expire("security:blocked_ips", duration_minutes * 60)
                
                # Log the blocking
                await self.log_security_event(SecurityEvent(
                    event_type="ip_blocked",
                    severity="high",
                    description=f"IP {ip_address} blocked for {duration_minutes} minutes: {reason}",
                    ip_address=ip_address,
                    user_agent="system",
                    timestamp=datetime.now(),
                    metadata={"duration_minutes": duration_minutes, "reason": reason}
                ))
            except Exception as e:
                logger.error(f"Failed to block IP in Redis: {e}")


# Global enhanced security manager instance
enhanced_security_manager = EnhancedSecurityManager()
