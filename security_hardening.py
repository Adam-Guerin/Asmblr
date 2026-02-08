"""
Security Hardening pour Asmblr - Protection avancée
Sécurité renforcée pour la production
"""

import os
import asyncio
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import HTTPException, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from loguru import logger
from prometheus_client import Counter, Histogram

# Configuration de sécurité
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
ENABLE_CORS = os.getenv("ENABLE_CORS", "false").lower() == "true"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []

# Métriques de sécurité
SECURITY_EVENTS = Counter('asmblr_security_events_total', 'Security events', ['event_type'])
AUTH_ATTEMPTS = Counter('asmblr_auth_attempts_total', 'Authentication attempts', ['result'])
RATE_LIMIT_VIOLATIONS = Counter('asmblr_rate_limit_violations_total', 'Rate limit violations')
SECURITY_RESPONSE_TIME = Histogram('asmblr_security_response_time_seconds', 'Security response time')

# Contexte de cryptographie
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Sécurité HTTP
security = HTTPBearer(auto_error=False)


@dataclass
class SecurityEvent:
    """Événement de sécurité"""
    event_type: str
    severity: str  # low, medium, high, critical
    description: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class UserSession:
    """Session utilisateur"""
    session_id: str
    user_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    is_active: bool


class SecurityManager:
    """Gestionnaire de sécurité"""
    
    def __init__(self):
        self.redis_client = None
        self.blocked_ips: Set[str] = set()
        self.active_sessions: Dict[str, UserSession] = {}
        self.security_events: List[SecurityEvent] = []
        
    async def initialize(self):
        """Initialise le gestionnaire de sécurité"""
        try:
            self.redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)
            await self.redis_client.ping()
            
            # Charger les IPs bloquées
            blocked_data = await self.redis_client.smembers("security:blocked_ips")
            self.blocked_ips = set(blocked_data)
            
            logger.info("Security manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize security manager: {e}")
            self.redis_client = None
    
    def hash_password(self, password: str) -> str:
        """Hash un mot de passe"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Vérifie un mot de passe"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Crée un token d'accès JWT"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Crée un token de rafraîchissement"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Vérifie un token JWT"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            await self.log_security_event(
                "invalid_token",
                "medium",
                f"Invalid JWT token: {str(e)}",
                "unknown",
                "unknown"
            )
            return None
    
    async def authenticate_user(self, username: str, password: str, ip_address: str, user_agent: str) -> Optional[Dict[str, Any]]:
        """Authentifie un utilisateur"""
        start_time = time.time()
        
        try:
            # Vérifier si l'IP est bloquée
            if await self.is_ip_blocked(ip_address):
                await self.log_security_event(
                    "blocked_ip_login_attempt",
                    "high",
                    f"Login attempt from blocked IP: {ip_address}",
                    ip_address,
                    user_agent
                )
                AUTH_ATTEMPTS.labels(result="blocked_ip").inc()
                return None
            
            # Vérifier les tentatives de connexion
            if await self.too_many_login_attempts(ip_address):
                await self.log_security_event(
                    "rate_limit_login",
                    "medium",
                    f"Too many login attempts from IP: {ip_address}",
                    ip_address,
                    user_agent
                )
                AUTH_ATTEMPTS.labels(result="rate_limited").inc()
                return None
            
            # Simulation de vérification d'utilisateur (en production, utiliser une vraie base de données)
            # Pour la démo, on accepte admin/admin123
            if username == "admin" and password == "admin123":
                # Enregistrer la connexion réussie
                await self.record_login_attempt(ip_address, success=True)
                
                # Créer les tokens
                access_token = self.create_access_token(data={"sub": username, "role": "admin"})
                refresh_token = self.create_refresh_token(data={"sub": username})
                
                # Créer la session
                session_id = secrets.token_urlsafe(32)
                session = UserSession(
                    session_id=session_id,
                    user_id=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_at=datetime.utcnow(),
                    last_activity=datetime.utcnow(),
                    is_active=True
                )
                
                await self.create_session(session)
                
                AUTH_ATTEMPTS.labels(result="success").inc()
                SECURITY_RESPONSE_TIME.observe(time.time() - start_time)
                
                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "session_id": session_id,
                    "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
                }
            else:
                # Enregistrer l'échec
                await self.record_login_attempt(ip_address, success=False)
                AUTH_ATTEMPTS.labels(result="invalid_credentials").inc()
                return None
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            AUTH_ATTEMPTS.labels(result="error").inc()
            return None
    
    async def is_ip_blocked(self, ip_address: str) -> bool:
        """Vérifie si une IP est bloquée"""
        if ip_address in self.blocked_ips:
            return True
        
        if self.redis_client:
            return await self.redis_client.sismember("security:blocked_ips", ip_address)
        
        return False
    
    async def block_ip(self, ip_address: str, duration_minutes: int = 60) -> None:
        """Bloque une IP"""
        self.blocked_ips.add(ip_address)
        
        if self.redis_client:
            await self.redis_client.sadd("security:blocked_ips", ip_address)
            await self.redis_client.expire(f"security:blocked_ips:{ip_address}", duration_minutes * 60)
        
        await self.log_security_event(
            "ip_blocked",
            "high",
            f"IP blocked: {ip_address} for {duration_minutes} minutes",
            ip_address,
            "system"
        )
        
        SECURITY_EVENTS.labels(event_type="ip_blocked").inc()
    
    async def too_many_login_attempts(self, ip_address: str) -> bool:
        """Vérifie s'il y a trop de tentatives de connexion"""
        if not self.redis_client:
            return False
        
        key = f"security:login_attempts:{ip_address}"
        attempts = await self.redis_client.get(key) or "0"
        
        return int(attempts) >= MAX_LOGIN_ATTEMPTS
    
    async def record_login_attempt(self, ip_address: str, success: bool) -> None:
        """Enregistre une tentative de connexion"""
        if not self.redis_client:
            return
        
        key = f"security:login_attempts:{ip_address}"
        
        if success:
            # Réinitialiser les tentatives en cas de succès
            await self.redis_client.delete(key)
        else:
            # Incrémenter les tentatives
            attempts = await self.redis_client.incr(key)
            await self.redis_client.expire(key, LOCKOUT_DURATION_MINUTES * 60)
            
            # Bloquer l'IP si trop de tentatives
            if attempts >= MAX_LOGIN_ATTEMPTS:
                await self.block_ip(ip_address, LOCKOUT_DURATION_MINUTES)
    
    async def create_session(self, session: UserSession) -> None:
        """Crée une session utilisateur"""
        self.active_sessions[session.session_id] = session
        
        if self.redis_client:
            session_data = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "is_active": "true"
            }
            
            await self.redis_client.hset(
                f"security:session:{session.session_id}",
                mapping=session_data
            )
            await self.redis_client.expire(f"security:session:{session.session_id}", ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    
    async def validate_session(self, session_id: str, ip_address: str) -> bool:
        """Valide une session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Vérifier l'IP
            if session.ip_address != ip_address:
                await self.log_security_event(
                    "session_hijack_attempt",
                    "critical",
                    f"Session hijack attempt: {session_id}",
                    ip_address,
                    "unknown"
                )
                return False
            
            # Mettre à jour la dernière activité
            session.last_activity = datetime.utcnow()
            
            return True
        
        if self.redis_client:
            session_data = await self.redis_client.hgetall(f"security:session:{session_id}")
            if session_data and session_data.get("is_active") == "true":
                # Vérifier l'IP
                if session_data.get("ip_address") != ip_address:
                    await self.log_security_event(
                        "session_hijack_attempt",
                        "critical",
                        f"Session hijack attempt: {session_id}",
                        ip_address,
                        "unknown"
                    )
                    return False
                
                # Mettre à jour la dernière activité
                await self.redis_client.hset(
                    f"security:session:{session_id}",
                    "last_activity",
                    datetime.utcnow().isoformat()
                )
                
                return True
        
        return False
    
    async def revoke_session(self, session_id: str) -> None:
        """Révoque une session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].is_active = False
            del self.active_sessions[session_id]
        
        if self.redis_client:
            await self.redis_client.delete(f"security:session:{session_id}")
        
        await self.log_security_event(
            "session_revoked",
            "medium",
            f"Session revoked: {session_id}",
            "unknown",
            "system"
        )
    
    async def check_rate_limit(self, ip_address: str, endpoint: str, limit: int = None, window: int = None) -> bool:
        """Vérifie le rate limiting"""
        limit = limit or RATE_LIMIT_REQUESTS
        window = window or RATE_LIMIT_WINDOW
        
        if not self.redis_client:
            return True
        
        key = f"security:rate_limit:{ip_address}:{endpoint}"
        
        current = await self.redis_client.incr(key)
        if current == 1:
            await self.redis_client.expire(key, window)
        
        if current > limit:
            RATE_LIMIT_VIOLATIONS.inc()
            await self.log_security_event(
                "rate_limit_exceeded",
                "medium",
                f"Rate limit exceeded for {endpoint}: {current}/{limit}",
                ip_address,
                "unknown"
            )
            return False
        
        return True
    
    async def log_security_event(self, event_type: str, severity: str, description: str, 
                               ip_address: str, user_agent: str, metadata: Dict[str, Any] = None) -> None:
        """Enregistre un événement de sécurité"""
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        self.security_events.append(event)
        
        # Garder seulement les 1000 derniers événements
        if len(self.security_events) > 1000:
            self.security_events = self.security_events[-1000:]
        
        # Stocker dans Redis
        if self.redis_client:
            event_data = {
                "event_type": event_type,
                "severity": severity,
                "description": description,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": event.timestamp.isoformat(),
                "metadata": metadata or {}
            }
            
            await self.redis_client.lpush("security:events", json.dumps(event_data))
            await self.redis_client.ltrim("security:events", 0, 1000)
        
        SECURITY_EVENTS.labels(event_type=event_type).inc()
        
        # Logger selon la sévérité
        if severity == "critical":
            logger.error(f"SECURITY CRITICAL: {description}")
        elif severity == "high":
            logger.warning(f"SECURITY HIGH: {description}")
        elif severity == "medium":
            logger.info(f"SECURITY MEDIUM: {description}")
        else:
            logger.debug(f"SECURITY LOW: {description}")
    
    async def get_security_status(self) -> Dict[str, Any]:
        """Récupère le statut de sécurité"""
        try:
            # Statistiques des événements récents
            recent_events = []
            if self.redis_client:
                event_data = await self.redis_client.lrange("security:events", 0, 9)
                recent_events = [json.loads(event) for event in event_data]
            
            # Compteurs par type
            event_counts = {}
            for event in self.security_events[-100:]:  # Derniers 100 événements
                event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
            
            return {
                "status": "active",
                "blocked_ips_count": len(self.blocked_ips),
                "active_sessions_count": len(self.active_sessions),
                "recent_events": recent_events,
                "event_counts": event_counts,
                "security_events_total": len(self.security_events),
                "configuration": {
                    "max_login_attempts": MAX_LOGIN_ATTEMPTS,
                    "lockout_duration_minutes": LOCKOUT_DURATION_MINUTES,
                    "rate_limit_requests": RATE_LIMIT_REQUESTS,
                    "rate_limit_window": RATE_LIMIT_WINDOW,
                    "cors_enabled": ENABLE_CORS,
                    "allowed_origins": ALLOWED_ORIGINS
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get security status: {e}")
            return {"error": str(e)}


# Instance globale
security_manager = SecurityManager()


# Middleware de sécurité
async def security_middleware(request: Request, call_next):
    """Middleware de sécurité pour FastAPI"""
    start_time = time.time()
    
    # Extraire les informations de la requête
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    endpoint = request.url.path
    
    # Vérifier si l'IP est bloquée
    if await security_manager.is_ip_blocked(ip_address):
        await security_manager.log_security_event(
            "blocked_request",
            "high",
            f"Request from blocked IP: {ip_address}",
            ip_address,
            user_agent
        )
        raise HTTPException(status_code=403, detail="IP address blocked")
    
    # Vérifier le rate limiting
    if not await security_manager.check_rate_limit(ip_address, endpoint):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Valider le token si présent
    authorization = request.headers.get("authorization")
    if authorization:
        try:
            scheme, token = authorization.split(" ")
            if scheme.lower() == "bearer":
                payload = await security_manager.verify_token(token)
                if payload:
                    request.state.user = payload
        except ValueError:
            pass
    
    # Continuer la requête
    response = await call_next(request)
    
    # Ajouter les headers de sécurité
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    # Logger les événements de sécurité
    if response.status_code == 401:
        await security_manager.log_security_event(
            "unauthorized_access",
            "medium",
            f"Unauthorized access attempt to {endpoint}",
            ip_address,
            user_agent
        )
    elif response.status_code == 403:
        await security_manager.log_security_event(
            "forbidden_access",
            "medium",
            f"Forbidden access attempt to {endpoint}",
            ip_address,
            user_agent
        )
    
    SECURITY_RESPONSE_TIME.observe(time.time() - start_time)
    
    return response


# Décorateurs de sécurité
def require_auth(required_role: str = None):
    """Décorateur pour exiger l'authentification"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request or not hasattr(request.state, 'user'):
                raise HTTPException(status_code=401, detail="Authentication required")
            
            if required_role:
                user_role = request.state.user.get("role")
                if user_role != required_role:
                    raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_rate_limit(limit: int, window: int):
    """Décorateur pour un rate limiting personnalisé"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request:
                ip_address = request.client.host
                endpoint = request.url.path
                
                if not await security_manager.check_rate_limit(ip_address, endpoint, limit, window):
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Point d'entrée pour le service de sécurité
if __name__ == "__main__":
    async def main():
        await security_manager.initialize()
        
        # Démarrer le monitoring de sécurité
        while True:
            try:
                status = await security_manager.get_security_status()
                logger.info(f"Security status: {status['blocked_ips_count']} blocked IPs, {status['active_sessions_count']} active sessions")
                await asyncio.sleep(300)  # 5 minutes
            except Exception as e:
                logger.error(f"Security monitoring error: {e}")
                await asyncio.sleep(60)
    
    asyncio.run(main())
