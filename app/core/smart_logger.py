"""
Logger intelligent pour Asmblr
Réduit le bruit et focus sur les informations importantes
"""

import sys
import json
import time
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from loguru import logger


class LogLevel(Enum):
    """Niveaux de log intelligents"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    DEBUG = "DEBUG"


class LogCategory(Enum):
    """Catégories de log pour filtrage intelligent"""
    SYSTEM = "system"
    NETWORK = "network"
    LLM = "llm"
    PERFORMANCE = "performance"
    USER_ACTION = "user_action"
    ERROR = "error"
    BUSINESS = "business"
    DEBUG = "debug"


@dataclass
class SmartLogEntry:
    """Entrée de log structurée"""
    timestamp: str
    level: LogLevel
    category: LogCategory
    operation: str
    message: str
    metadata: Dict[str, Any]
    user_facing: bool = False
    correlation_id: Optional[str] = None


class LogFilter:
    """
    Filtre intelligent pour réduire le bruit dans les logs
    """
    
    def __init__(self):
        # Messages à filtrer (bruit courant)
        self.noise_patterns = {
            # Cache hits (trop fréquents)
            "cache_hit",
            "cache_miss", 
            "cached artifact",
            "evicted.*cache",
            
            # Événements réseau normaux
            "web_fetch ok",
            "rate_limit.*tokens",
            
            # Événements système normaux
            "worker started",
            "health check",
            "ping successful",
            
            # Debug excessif
            "traceback",
            "stack trace",
            "debug.*iteration",
            
            # Progression normale
            "processing.*item",
            "step.*completed",
            "iteration.*progress"
        }
        
        # Catégories à réduire en mode normal
        self.category_limits = {
            LogCategory.DEBUG: 0,      # Pas de debug en normal
            LogCategory.SYSTEM: 10,     # 10 messages max par heure
            LogCategory.NETWORK: 20,    # 20 messages max par heure
            LogCategory.LLM: 15,        # 15 messages max par heure
            LogCategory.PERFORMANCE: 5,  # 5 messages max par heure
        }
        
        # Compteurs pour les limites
        self.category_counters = {}
        self.last_reset = time.time()
        self.reset_interval = 3600  # 1 heure
        
        # Messages importants à toujours garder
        self.important_patterns = {
            "critical",
            "fatal",
            "security",
            "breach",
            "corruption",
            "data loss",
            "authentication failed",
            "authorization failed",
            "service unavailable",
            "degraded performance"
        }
    
    def should_log(self, entry: SmartLogEntry) -> bool:
        """
        Détermine si une entrée de log doit être conservée
        
        Args:
            entry: Entrée de log à évaluer
            
        Returns:
            True si le message doit être loggé
        """
        # Toujours logger les messages critiques
        if entry.level == LogLevel.CRITICAL:
            return True
        
        # Toujours logger les messages importants
        message_lower = entry.message.lower()
        if any(pattern in message_lower for pattern in self.important_patterns):
            return True
        
        # Toujours logger les messages face utilisateur
        if entry.user_facing:
            return True
        
        # Filtrer le bruit connu
        if self._is_noise(entry.message):
            return False
        
        # Appliquer les limites de catégorie
        if not self._check_category_limit(entry.category):
            return False
        
        return True
    
    def _is_noise(self, message: str) -> bool:
        """Vérifie si le message correspond à un pattern de bruit"""
        message_lower = message.lower()
        for pattern in self.noise_patterns:
            if pattern in message_lower:
                return True
        return False
    
    def _check_category_limit(self, category: LogCategory) -> bool:
        """Vérifie les limites de catégorie"""
        current_time = time.time()
        
        # Réinitialiser les compteurs si nécessaire
        if current_time - self.last_reset > self.reset_interval:
            self.category_counters.clear()
            self.last_reset = current_time
        
        # Incrémenter le compteur
        self.category_counters[category] = self.category_counters.get(category, 0) + 1
        
        # Vérifier la limite
        limit = self.category_limits.get(category, 100)
        return self.category_counters[category] <= limit


class SmartLogger:
    """
    Logger intelligent qui réduit le bruit et focus sur l'important
    """
    
    def __init__(self, 
                 enable_filtering: bool = True,
                 log_file: Optional[Path] = None,
                 max_entries: int = 10000):
        self.enable_filtering = enable_filtering
        self.log_file = log_file
        self.max_entries = max_entries
        
        self.filter = LogFilter()
        self.log_entries: List[SmartLogEntry] = []
        self.correlation_ids: Set[str] = set()
        
        # Configuration du logger loguru
        self._configure_loguru()
    
    def _configure_loguru(self) -> None:
        """Configure loguru pour une sortie intelligente"""
        # Supprimer les handlers par défaut
        logger.remove()
        
        # Handler console avec format intelligent
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[category]}</cyan> | <level>{message}</level>",
            level="INFO",
            filter=self._loguru_filter
        )
        
        # Handler fichier si spécifié
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            logger.add(
                str(self.log_file),
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[category]} | {message}",
                level="DEBUG",
                rotation="10 MB",
                retention="7 days",
                filter=self._loguru_filter
            )
    
    def _loguru_filter(self, record: Dict[str, Any]) -> bool:
        """Filtre loguru pour réduire le bruit"""
        if not self.enable_filtering:
            return True
        
        # Créer une entrée de log temporaire
        entry = SmartLogEntry(
            timestamp=record["time"].isoformat(),
            level=LogLevel(record["level"].name),
            category=LogCategory(record["extra"].get("category", "system")),
            operation=record["extra"].get("operation", "unknown"),
            message=record["message"],
            metadata=record.get("extra", {}),
            user_facing=record["extra"].get("user_facing", False),
            correlation_id=record["extra"].get("correlation_id")
        )
        
        return self.filter.should_log(entry)
    
    def log(self, 
             level: LogLevel,
             category: LogCategory,
             operation: str,
             message: str,
             metadata: Optional[Dict[str, Any]] = None,
             user_facing: bool = False,
             correlation_id: Optional[str] = None) -> None:
        """
        Enregistre une entrée de log intelligente
        
        Args:
            level: Niveau de log
            category: Catégorie
            operation: Opération concernée
            message: Message à logger
            metadata: Métadonnées additionnelles
            user_facing: Si le message est destiné à l'utilisateur
            correlation_id: ID de corrélation pour suivre une opération
        """
        entry = SmartLogEntry(
            timestamp=self._get_timestamp(),
            level=level,
            category=category,
            operation=operation,
            message=message,
            metadata=metadata or {},
            user_facing=user_facing,
            correlation_id=correlation_id
        )
        
        # Stocker l'entrée
        self._store_entry(entry)
        
        # Logger avec loguru
        logger.bind(
            category=category.value,
            operation=operation,
            user_facing=user_facing,
            correlation_id=correlation_id,
            **(metadata or {})
        ).log(level.value, message)
    
    def _store_entry(self, entry: SmartLogEntry) -> None:
        """Stocke une entrée de log"""
        self.log_entries.append(entry)
        
        # Limiter le nombre d'entrées
        if len(self.log_entries) > self.max_entries:
            self.log_entries = self.log_entries[-self.max_entries:]
        
        # Suivre les IDs de corrélation
        if entry.correlation_id:
            self.correlation_ids.add(entry.correlation_id)
    
    def _get_timestamp(self) -> str:
        """Génère un timestamp ISO"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    # Méthodes pratiques par niveau
    def critical(self, category: LogCategory, operation: str, message: str, **kwargs) -> None:
        """Log critique"""
        self.log(LogLevel.CRITICAL, category, operation, message, **kwargs)
    
    def high(self, category: LogCategory, operation: str, message: str, **kwargs) -> None:
        """Log haute priorité"""
        self.log(LogLevel.HIGH, category, operation, message, **kwargs)
    
    def medium(self, category: LogCategory, operation: str, message: str, **kwargs) -> None:
        """Log moyenne priorité"""
        self.log(LogLevel.MEDIUM, category, operation, message, **kwargs)
    
    def low(self, category: LogCategory, operation: str, message: str, **kwargs) -> None:
        """Log basse priorité"""
        self.log(LogLevel.LOW, category, operation, message, **kwargs)
    
    def debug(self, category: LogCategory, operation: str, message: str, **kwargs) -> None:
        """Log debug"""
        self.log(LogLevel.DEBUG, category, operation, message, **kwargs)
    
    # Méthodes pratiques par catégorie
    def system(self, level: LogLevel, operation: str, message: str, **kwargs) -> None:
        """Log système"""
        self.log(level, LogCategory.SYSTEM, operation, message, **kwargs)
    
    def network(self, level: LogLevel, operation: str, message: str, **kwargs) -> None:
        """Log réseau"""
        self.log(level, LogCategory.NETWORK, operation, message, **kwargs)
    
    def llm(self, level: LogLevel, operation: str, message: str, **kwargs) -> None:
        """Log LLM"""
        self.log(level, LogCategory.LLM, operation, message, **kwargs)
    
    def performance(self, level: LogLevel, operation: str, message: str, **kwargs) -> None:
        """Log performance"""
        self.log(level, LogCategory.PERFORMANCE, operation, message, **kwargs)
    
    def user_action(self, operation: str, message: str, **kwargs) -> None:
        """Log action utilisateur"""
        self.log(LogLevel.MEDIUM, LogCategory.USER_ACTION, operation, message, user_facing=True, **kwargs)
    
    def error(self, operation: str, message: str, **kwargs) -> None:
        """Log erreur"""
        self.log(LogLevel.HIGH, LogCategory.ERROR, operation, message, **kwargs)
    
    def business(self, level: LogLevel, operation: str, message: str, **kwargs) -> None:
        """Log business"""
        self.log(level, LogCategory.BUSINESS, operation, message, **kwargs)
    
    def start_operation(self, operation: str, correlation_id: Optional[str] = None, **metadata) -> None:
        """Démarre le logging d'une opération"""
        self.low(LogCategory.SYSTEM, operation, f"Début opération: {operation}", 
                correlation_id=correlation_id, **metadata)
    
    def end_operation(self, operation: str, correlation_id: Optional[str] = None, 
                     success: bool = True, **metadata) -> None:
        """Termine le logging d'une opération"""
        status = "succès" if success else "échec"
        level = LogLevel.MEDIUM if success else LogLevel.HIGH
        self.low(LogCategory.SYSTEM, operation, f"Fin opération: {operation} ({status})", 
                correlation_id=correlation_id, success=success, **metadata)
    
    def get_operation_logs(self, correlation_id: str) -> List[SmartLogEntry]:
        """Récupère tous les logs pour une opération"""
        return [entry for entry in self.log_entries if entry.correlation_id == correlation_id]
    
    def get_recent_logs(self, 
                       minutes: int = 60,
                       categories: Optional[List[LogCategory]] = None,
                       levels: Optional[List[LogLevel]] = None) -> List[SmartLogEntry]:
        """
        Récupère les logs récents avec filtres
        
        Args:
            minutes: Nombre de minutes à regarder en arrière
            categories: Filtrer par catégories
            levels: Filtrer par niveaux
            
        Returns:
            Liste des entrées de log filtrées
        """
        from datetime import datetime, timezone, timedelta
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        
        filtered = []
        for entry in self.log_entries:
            entry_time = datetime.fromisoformat(entry.timestamp)
            
            # Filtrer par temps
            if entry_time < cutoff_time:
                continue
            
            # Filtrer par catégorie
            if categories and entry.category not in categories:
                continue
            
            # Filtrer par niveau
            if levels and entry.level not in levels:
                continue
            
            filtered.append(entry)
        
        return filtered
    
    def get_log_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Retourne un résumé des logs"""
        recent_logs = self.get_recent_logs(minutes=hours * 60)
        
        # Compter par catégorie et niveau
        by_category = {}
        by_level = {}
        by_operation = {}
        
        for entry in recent_logs:
            by_category[entry.category.value] = by_category.get(entry.category.value, 0) + 1
            by_level[entry.level.value] = by_level.get(entry.level.value, 0) + 1
            by_operation[entry.operation] = by_operation.get(entry.operation, 0) + 1
        
        # Identifier les erreurs critiques
        critical_errors = [
            entry for entry in recent_logs 
            if entry.level == LogLevel.CRITICAL
        ]
        
        # Identifier les opérations avec le plus d'erreurs
        error_operations = [
            entry for entry in recent_logs 
            if entry.category == LogCategory.ERROR
        ]
        
        return {
            "total_entries": len(recent_logs),
            "timeframe_hours": hours,
            "by_category": by_category,
            "by_level": by_level,
            "top_operations": dict(sorted(by_operation.items(), key=lambda x: x[1], reverse=True)[:10]),
            "critical_errors": len(critical_errors),
            "error_rate": len(error_operations) / len(recent_logs) if recent_logs else 0,
            "filtering_enabled": self.enable_filtering,
            "entries_filtered": len(self.log_entries) - len(recent_logs)
        }
    
    def export_logs(self, 
                   format_type: str = "json",
                   hours: int = 24,
                   categories: Optional[List[LogCategory]] = None) -> str:
        """Exporte les logs filtrés"""
        logs = self.get_recent_logs(minutes=hours * 60, categories=categories)
        
        if format_type == "json":
            return json.dumps([asdict(entry) for entry in logs], indent=2)
        
        elif format_type == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=asdict(logs[0]).keys())
                writer.writeheader()
                for entry in logs:
                    writer.writerow(asdict(entry))
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Format non supporté: {format_type}")


# Instance globale du logger intelligent
_smart_logger: Optional[SmartLogger] = None


def get_smart_logger() -> SmartLogger:
    """Récupère l'instance globale du logger intelligent"""
    global _smart_logger
    if _smart_logger is None:
        # Créer avec le fichier de log par défaut
        log_file = Path("data") / "smart.log"
        _smart_logger = SmartLogger(log_file=log_file)
    return _smart_logger


# Fonctions pratiques pour le logging intelligent
def log_critical(category: LogCategory, operation: str, message: str, **kwargs):
    """Log critique"""
    get_smart_logger().critical(category, operation, message, **kwargs)


def log_error(operation: str, message: str, **kwargs):
    """Log erreur"""
    get_smart_logger().error(operation, message, **kwargs)


def log_performance(operation: str, message: str, **kwargs):
    """Log performance"""
    get_smart_logger().performance(LogLevel.MEDIUM, operation, message, **kwargs)


def log_user_action(operation: str, message: str, **kwargs):
    """Log action utilisateur"""
    get_smart_logger().user_action(operation, message, **kwargs)


def start_operation(operation: str, correlation_id: Optional[str] = None, **kwargs):
    """Démarre le logging d'une opération"""
    get_smart_logger().start_operation(operation, correlation_id, **kwargs)


def end_operation(operation: str, correlation_id: Optional[str] = None, success: bool = True, **kwargs):
    """Termine le logging d'une opération"""
    get_smart_logger().end_operation(operation, correlation_id, success, **kwargs)
