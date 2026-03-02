"""
Système d'alerting et de notifications pour Asmblr
Intégration avec Alertmanager, Slack, Email, et Webhooks
"""

import asyncio
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from loguru import logger

from app.core.config import Settings
from app.monitoring.prometheus_metrics import AsmblrMetrics


class AlertSeverity(Enum):
    """Niveaux de sévérité des alertes"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Statuts des alertes"""
    FIRING = "firing"
    RESOLVED = "resolved"


@dataclass
class Alert:
    """Structure d'une alerte"""
    name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    description: str
    labels: dict[str, str]
    annotations: dict[str, str]
    timestamp: float
    resolved_timestamp: float | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convertir l'alerte en dictionnaire"""
        data = asdict(self)
        data["severity"] = self.severity.value
        data["status"] = self.status.value
        return data


class NotificationChannel:
    """Classe de base pour les canaux de notification"""
    
    def __init__(self, name: str, config: dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
    
    async def send_alert(self, alert: Alert) -> bool:
        """Envoyer une alerte"""
        if not self.enabled:
            logger.warning(f"Channel {self.name} is disabled")
            return False
        
        try:
            return await self._send_alert(alert)
        except Exception as e:
            logger.error(f"Failed to send alert via {self.name}: {e}")
            return False
    
    async def _send_alert(self, alert: Alert) -> bool:
        """Méthode à implémenter par les sous-classes"""
        raise NotImplementedError


class SlackNotificationChannel(NotificationChannel):
    """Canal de notification Slack"""
    
    async def _send_alert(self, alert: Alert) -> bool:
        """Envoyer une alerte via Slack webhook"""
        webhook_url = self.config.get("webhook_url")
        if not webhook_url:
            logger.error("Slack webhook URL not configured")
            return False
        
        # Déterminer la couleur selon la sévérité
        color_map = {
            AlertSeverity.INFO: "#36a64f",      # green
            AlertSeverity.WARNING: "#ff9500",   # orange
            AlertSeverity.CRITICAL: "#ff0000"   # red
        }
        
        color = color_map.get(alert.severity, "#808080")
        
        # Construire le message Slack
        payload = {
            "channel": self.config.get("channel", "#alerts"),
            "username": "Asmblr Alert",
            "icon_emoji": ":warning:",
            "attachments": [
                {
                    "color": color,
                    "title": f"[{alert.severity.value.upper()}] {alert.name}",
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Description",
                            "value": alert.description,
                            "short": False
                        },
                        {
                            "title": "Status",
                            "value": alert.status.value,
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(alert.timestamp)),
                            "short": True
                        }
                    ],
                    "footer": "Asmblr Monitoring",
                    "ts": int(alert.timestamp)
                }
            ]
        }
        
        # Ajouter les labels
        if alert.labels:
            labels_text = "\n".join([f"• {k}: {v}" for k, v in alert.labels.items()])
            payload["attachments"][0]["fields"].append({
                "title": "Labels",
                "value": labels_text,
                "short": False
            })
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                return response.status == 200


class EmailNotificationChannel(NotificationChannel):
    """Canal de notification Email"""
    
    async def _send_alert(self, alert: Alert) -> bool:
        """Envoyer une alerte par email"""
        smtp_config = self.config.get("smtp", {})
        recipients = self.config.get("recipients", [])
        
        if not recipients:
            logger.error("No email recipients configured")
            return False
        
        # Construire l'email
        subject = f"[{alert.severity.value.upper()}] Asmblr Alert: {alert.name}"
        
        # Corps HTML
        html_body = f"""
        <html>
        <body>
            <h2 style="color: {'red' if alert.severity == AlertSeverity.CRITICAL else 'orange' if alert.severity == AlertSeverity.WARNING else 'green'}">
                {alert.severity.value.upper()}: {alert.name}
            </h2>
            <p><strong>Status:</strong> {alert.status.value}</p>
            <p><strong>Message:</strong> {alert.message}</p>
            <p><strong>Description:</strong> {alert.description}</p>
            <p><strong>Timestamp:</strong> {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(alert.timestamp))}</p>
            
            {f'<h3>Labels:</h3><ul>' + ''.join([f'<li><strong>{k}:</strong> {v}</li>' for k, v in alert.labels.items()]) + '</ul>' if alert.labels else ''}
            
            {f'<h3>Annotations:</h3><ul>' + ''.join([f'<li><strong>{k}:</strong> {v}</li>' for k, v in alert.annotations.items()]) + '</ul>' if alert.annotations else ''}
            
            <hr>
            <p><em>Generated by Asmblr Monitoring System</em></p>
        </body>
        </html>
        """
        
        # Envoyer l'email
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_config.get("from", "alerts@asmblr.local")
            msg["To"] = ", ".join(recipients)
            
            # Ajouter les parties HTML et texte
            text_part = MIMEText(f"{subject}\n\n{alert.message}\n\n{alert.description}", "plain")
            html_part = MIMEText(html_body, "html")
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Envoyer via SMTP
            with smtplib.SMTP(
                smtp_config.get("host", "localhost"),
                smtp_config.get("port", 587)
            ) as server:
                if smtp_config.get("use_tls", True):
                    server.starttls()
                
                if smtp_config.get("username") and smtp_config.get("password"):
                    server.login(
                        smtp_config["username"],
                        smtp_config["password"]
                    )
                
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


class WebhookNotificationChannel(NotificationChannel):
    """Canal de notification Webhook"""
    
    async def _send_alert(self, alert: Alert) -> bool:
        """Envoyer une alerte via webhook"""
        webhook_url = self.config.get("url")
        if not webhook_url:
            logger.error("Webhook URL not configured")
            return False
        
        # Construire le payload
        payload = {
            "alert": alert.to_dict(),
            "timestamp": time.time(),
            "source": "asmblr-monitoring"
        }
        
        # Headers personnalisés
        headers = self.config.get("headers", {})
        headers.setdefault("Content-Type", "application/json")
        
        async with aiohttp.ClientSession() as session, session.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            return response.status < 400


class AlertManager:
    """Gestionnaire d'alertes pour Asmblr"""
    
    def __init__(self, settings: Settings, metrics: AsmblrMetrics):
        self.settings = settings
        self.metrics = metrics
        self.channels: dict[str, NotificationChannel] = {}
        self.active_alerts: dict[str, Alert] = {}
        self.alert_history: list[Alert] = []
        self._running = False
        
        # Charger la configuration
        self._load_configuration()
    
    def _load_configuration(self):
        """Charger la configuration des alertes"""
        alert_config = self.settings.__dict__.get("alerts", {})
        
        # Configurer les canaux
        channels_config = alert_config.get("channels", {})
        
        # Canal Slack
        if "slack" in channels_config:
            self.channels["slack"] = SlackNotificationChannel(
                "slack", channels_config["slack"]
            )
        
        # Canal Email
        if "email" in channels_config:
            self.channels["email"] = EmailNotificationChannel(
                "email", channels_config["email"]
            )
        
        # Canal Webhook
        if "webhook" in channels_config:
            self.channels["webhook"] = WebhookNotificationChannel(
                "webhook", channels_config["webhook"]
            )
        
        logger.info(f"Loaded {len(self.channels)} notification channels")
    
    async def start(self):
        """Démarrer le gestionnaire d'alertes"""
        if self._running:
            return
        
        self._running = True
        logger.info("Alert manager started")
    
    async def stop(self):
        """Arrêter le gestionnaire d'alertes"""
        self._running = False
        logger.info("Alert manager stopped")
    
    async def create_alert(
        self,
        name: str,
        severity: AlertSeverity,
        message: str,
        description: str,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None
    ) -> Alert:
        """Créer une nouvelle alerte"""
        
        # Vérifier si une alerte similaire existe déjà
        alert_key = f"{name}:{severity.value}"
        if alert_key in self.active_alerts:
            existing_alert = self.active_alerts[alert_key]
            if existing_alert.status == AlertStatus.FIRING:
                logger.debug(f"Alert {alert_key} already firing, updating")
                existing_alert.message = message
                existing_alert.description = description
                existing_alert.timestamp = time.time()
                return existing_alert
        
        # Créer la nouvelle alerte
        alert = Alert(
            name=name,
            severity=severity,
            status=AlertStatus.FIRING,
            message=message,
            description=description,
            labels=labels or {},
            annotations=annotations or {},
            timestamp=time.time()
        )
        
        # Ajouter aux alertes actives
        self.active_alerts[alert_key] = alert
        self.alert_history.append(alert)
        
        # Mettre à jour les métriques
        self.metrics.business_metrics.record_alert(
            name, severity.value, "firing"
        )
        
        logger.info(f"Created alert: {name} ({severity.value})")
        
        # Envoyer les notifications
        await self._send_notifications(alert)
        
        return alert
    
    async def resolve_alert(self, name: str, severity: AlertSeverity) -> bool:
        """Résoudre une alerte"""
        alert_key = f"{name}:{severity.value}"
        
        if alert_key not in self.active_alerts:
            logger.warning(f"Alert {alert_key} not found")
            return False
        
        alert = self.active_alerts[alert_key]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_timestamp = time.time()
        
        # Retirer des alertes actives
        del self.active_alerts[alert_key]
        
        # Mettre à jour les métriques
        self.metrics.business_metrics.record_alert(
            name, severity.value, "resolved"
        )
        
        logger.info(f"Resolved alert: {name} ({severity.value})")
        
        # Envoyer les notifications de résolution
        await self._send_notifications(alert)
        
        return True
    
    async def _send_notifications(self, alert: Alert):
        """Envoyer les alertes à tous les canaux configurés"""
        tasks = []
        
        for channel_name, channel in self.channels.items():
            # Filtrer par sévérité si configuré
            channel_severity = channel.config.get("severity_filter", [])
            if channel_severity and alert.severity.value not in channel_severity:
                continue
            
            task = asyncio.create_task(channel.send_alert(alert))
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful = sum(1 for r in results if r is True)
            total = len(tasks)
            
            logger.info(f"Alert notifications sent: {successful}/{total} successful")
    
    def get_active_alerts(self) -> list[Alert]:
        """Obtenir les alertes actives"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> list[Alert]:
        """Obtenir l'historique des alertes"""
        return self.alert_history[-limit:]
    
    def get_alert_stats(self) -> dict[str, Any]:
        """Obtenir les statistiques des alertes"""
        active_by_severity = {}
        for alert in self.active_alerts.values():
            severity = alert.severity.value
            active_by_severity[severity] = active_by_severity.get(severity, 0) + 1
        
        recent_alerts = [
            alert for alert in self.alert_history
            if time.time() - alert.timestamp < 3600  # Dernière heure
        ]
        
        recent_by_severity = {}
        for alert in recent_alerts:
            severity = alert.severity.value
            recent_by_severity[severity] = recent_by_severity.get(severity, 0) + 1
        
        return {
            "active_alerts": len(self.active_alerts),
            "active_by_severity": active_by_severity,
            "recent_alerts": len(recent_alerts),
            "recent_by_severity": recent_by_severity,
            "total_history": len(self.alert_history),
            "channels_configured": len(self.channels)
        }


# Fonctions utilitaires pour l'intégration
async def check_system_alerts(alert_manager: AlertManager, metrics: AsmblrMetrics):
    """Vérifier les alertes système"""
    stats = metrics.get_metrics_summary()
    
    # Vérifier l'utilisation CPU
    if "cpu_usage" in stats and stats["cpu_usage"] > 90:
        await alert_manager.create_alert(
            name="HighCPUUsage",
            severity=AlertSeverity.CRITICAL,
            message=f"CPU usage is {stats['cpu_usage']}%",
            description="System CPU usage is critically high",
            labels={"component": "system", "metric": "cpu_usage"}
        )
    elif "cpu_usage" in stats and stats["cpu_usage"] > 80:
        await alert_manager.create_alert(
            name="HighCPUUsage",
            severity=AlertSeverity.WARNING,
            message=f"CPU usage is {stats['cpu_usage']}%",
            description="System CPU usage is high",
            labels={"component": "system", "metric": "cpu_usage"}
        )
    
    # Vérifier l'utilisation mémoire
    if "memory_usage" in stats and stats["memory_usage"] > 90:
        await alert_manager.create_alert(
            name="HighMemoryUsage",
            severity=AlertSeverity.CRITICAL,
            message=f"Memory usage is {stats['memory_usage']}%",
            description="System memory usage is critically high",
            labels={"component": "system", "metric": "memory_usage"}
        )
    
    # Vérifier les erreurs
    if "error_rate" in stats and stats["error_rate"] > 0.1:
        await alert_manager.create_alert(
            name="HighErrorRate",
            severity=AlertSeverity.WARNING,
            message=f"Error rate is {stats['error_rate']:.1%}",
            description="Application error rate is high",
            labels={"component": "application", "metric": "error_rate"}
        )


# Configuration par défaut
DEFAULT_ALERT_CONFIG = {
    "channels": {
        "slack": {
            "enabled": False,
            "webhook_url": "",
            "channel": "#asmblr-alerts",
            "severity_filter": ["warning", "critical"]
        },
        "email": {
            "enabled": False,
            "smtp": {
                "host": "localhost",
                "port": 587,
                "use_tls": True,
                "from": "alerts@asmblr.local",
                "username": "",
                "password": ""
            },
            "recipients": ["admin@asmblr.local"],
            "severity_filter": ["critical"]
        },
        "webhook": {
            "enabled": False,
            "url": "",
            "headers": {},
            "severity_filter": ["warning", "critical"]
        }
    }
}
