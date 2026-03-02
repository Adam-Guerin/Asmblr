# Guide de Déploiement du Monitoring Complet pour Asmblr

## 📊 Vue d'Ensemble

Ce guide décrit le déploiement complet de la solution de monitoring et d'observabilité pour Asmblr, incluant:

- ✅ **Métriques Prometheus** - Collecte et stockage des métriques
- ✅ **Logs ELK Stack** - Centralisation et analyse des logs
- ✅ **Dashboards Grafana** - Visualisation des métriques et logs
- ✅ **Alerting Alertmanager** - Notifications automatiques
- ✅ **Tracing Jaeger** - Tracing distribué
- ✅ **Health Checks** - Monitoring de la santé du système

## 🚀 Démarrage Rapide

### 1. Prérequis

```bash
# Docker et Docker Compose
docker --version
docker-compose --version

# Ports requis (doivent être libres)
3001  # Grafana
9090  # Prometheus
9093  # Alertmanager
9200  # Elasticsearch
5601  # Kibana
16686 # Jaeger
```

### 2. Déploiement

```bash
# Cloner le repository (si nécessaire)
git clone <repository-url>
cd Asmblr

# Démarrer la stack de monitoring complète
docker-compose -f docker-compose.monitoring-complete.yml up -d

# Vérifier le statut
docker-compose -f docker-compose.monitoring-complete.yml ps
```

### 3. Accès aux Services

| Service | URL | Utilisateur | Mot de passe |
|---------|-----|-------------|--------------|
| Grafana | http://localhost:3001 | admin | admin123 |
| Prometheus | http://localhost:9090 | - | - |
| Alertmanager | http://localhost:9093 | - | - |
| Kibana | http://localhost:5601 | - | - |
| Jaeger | http://localhost:16686 | - | - |

## 📋 Configuration Détaillée

### Configuration Prometheus

**Fichier**: `monitoring/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

scrape_configs:
  # Métriques Asmblr
  - job_name: 'asmblr-api'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

### Configuration Alertmanager

**Fichier**: `monitoring/alertmanager/alertmanager.yml`

```yaml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@asmblr.local'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
```

### Configuration Grafana

**Dashboards pré-configurés**:
- Vue d'ensemble Asmblr
- Métriques système
- Performance des pipelines
- Logs et erreurs

**Data Sources**:
- Prometheus (http://prometheus:9090)
- Elasticsearch (http://elasticsearch:9200)

## 🔧 Intégration avec l'Application

### 1. Métriques Prometheus

```python
from app.monitoring.prometheus_metrics import AsmblrMetrics

# Initialiser les métriques
metrics = AsmblrMetrics()

# Enregistrer une requête
metrics.record_request("GET", "/api/test", 200, 0.1)

# Enregistrer une pipeline
metrics.business_metrics.record_pipeline_start("venture_creation")
```

### 2. Logs Structurés

```python
from app.monitoring.structured_logger import StructuredLogger

# Initialiser le logger
logger = StructuredLogger("asmblr-api", "system")

# Logger avec contexte
logger.system("Application started", version="1.0.0")
logger.business("Pipeline completed", pipeline_id="123", duration=45.2)
```

### 3. Alerting

```python
from app.monitoring.alerting import AlertManager, AlertSeverity

# Initialiser l'alert manager
alert_manager = AlertManager(settings, metrics)

# Créer une alerte
await alert_manager.create_alert(
    name="HighErrorRate",
    severity=AlertSeverity.WARNING,
    message="Error rate is 15%",
    description="Application error rate is above threshold"
)
```

### 4. Tracing Distribué

```python
from app.monitoring.distributed_tracing import trace_function, trace_llm_request

# Tracer une fonction
@trace_function(name="process_idea", kind=SpanKind.BUSINESS)
async def process_idea(idea_data):
    # Traitement de l'idée
    pass

# Tracer une requête LLM
@trace_llm_request(model="llama3.1:8b", operation="generation")
async def generate_content(prompt):
    # Génération de contenu
    pass
```

### 5. Health Checks

```python
from app.monitoring.health_checks import HealthChecker

# Initialiser les health checks
health_checker = HealthChecker(settings, metrics, logger)

# Exécuter tous les checks
results = await health_checker.run_all_checks()

# Endpoint FastAPI
@app.get("/health")
async def health_check():
    return await health_endpoint(health_checker)
```

## 📊 Dashboards Grafana

### Dashboard Vue d'Ensemble

**Métriques incluses**:
- Statut des services
- Requêtes par minute
- Taux d'erreur
- Pipelines actives
- Utilisateurs actifs
- Temps de réponse moyen

### Dashboard Performance

**Métriques incluses**:
- Performance des pipelines
- Métriques LLM
- Performance du cache
- Utilisation CPU/Mémoire
- Latence réseau

### Dashboard Logs

**Visualisations**:
- Logs par catégorie
- Erreurs et exceptions
- Performance des requêtes
- Traces distribuées

## 🚨 Alertes Configurées

### Alertes Système

- **Service Down**: Service indisponible
- **High Error Rate**: Taux d'erreur > 10%
- **High Latency**: Latence > 2s
- **High CPU Usage**: CPU > 80%
- **High Memory Usage**: Mémoire > 85%
- **Low Disk Space**: Disque < 20%

### Alertes Métier

- **No Ideas Generated**: Aucune idée depuis 2h
- **Low Idea Generation Rate**: < 1 idée/heure
- **No MVP Builds**: Aucun MVP depuis 6h
- **High Token Usage**: > 10k tokens/heure

### Canaux de Notification

- **Slack**: Pour les alertes warning et critical
- **Email**: Pour les alertes critical uniquement
- **Webhook**: Pour intégrations personnalisées

## 🔍 Monitoring des Logs

### Configuration ELK

**Elasticsearch**: Stockage des logs et métriques
**Logstash**: Traitement et parsing des logs
**Kibana**: Visualisation et recherche
**Filebeat**: Collecte des logs depuis l'application

### Patterns de Logs

```json
{
  "timestamp": "2026-02-26T18:00:00Z",
  "level": "INFO",
  "category": "business",
  "message": "Pipeline completed",
  "trace_id": "abc123",
  "span_id": "def456",
  "user_id": "user123",
  "pipeline_id": "pipeline456",
  "duration_ms": 4500
}
```

### Requêtes Kibana

```json
// Logs d'erreurs
{
  "query": {
    "match": {
      "level": "ERROR"
    }
  }
}

// Logs par utilisateur
{
  "query": {
    "term": {
      "user_id": "user123"
    }
  }
}
```

## 🌐 Tracing Distribué

### Configuration Jaeger

**Collector**: http://localhost:14268
**UI**: http://localhost:16686
**Storage**: Elasticsearch

### Spans Tracés

- **HTTP Requests**: Requêtes API
- **LLM Calls**: Appels aux modèles LLM
- **Pipeline Operations**: Étapes des pipelines
- **Cache Operations**: Accès au cache
- **Database Queries**: Requêtes base de données

### Visualisation

- **Trace View**: Vue détaillée des traces
- **Service Map**: Architecture des services
- **Dependency Graph**: Dépendances entre services
- **Performance Metrics**: Métriques de performance

## 🏥 Health Checks

### Checks Inclus

**Système**:
- CPU, Mémoire, Disque
- Réseau et connectivité

**Application**:
- Configuration valide
- Cache fonctionnel
- Logs opérationnels

**Externes**:
- Service Ollama
- Base de données
- Services externes

### Endpoints

- `/health` - Tous les checks
- `/ready` - Checks critiques seulement
- `/live` - Vérification minimale

## 📈 Monitoring de Performance

### Métriques Clés

**Application**:
- Requêtes par seconde
- Temps de réponse moyen
- Taux d'erreur
- Durée des pipelines

**Système**:
- Utilisation CPU
- Utilisation mémoire
- Espace disque
- Traffic réseau

**Business**:
- Idées générées
- MVP construits
- Tokens utilisés
- Utilisateurs actifs

### SLAs

- **Disponibilité**: > 99.9%
- **Temps de réponse**: < 2s (95th percentile)
- **Taux d'erreur**: < 1%
- **Temps de pipeline**: < 30s

## 🛠️ Maintenance

### Sauvegarde des Données

```bash
# Prometheus
docker exec asmblr-prometheus tar czf /tmp/prometheus_backup.tar.gz /prometheus

# Elasticsearch
docker exec asmblr-elasticsearch bin/elasticsearch-backup create

# Grafana
docker exec asmblr-grafana tar czf /tmp/grafana_backup.tar.gz /var/lib/grafana
```

### Mise à Jour

```bash
# Mettre à jour les images
docker-compose -f docker-compose.monitoring-complete.yml pull

# Redémarrer avec nouvelle configuration
docker-compose -f docker-compose.monitoring-complete.yml up -d
```

### Dépannage

```bash
# Vérifier les logs
docker-compose -f docker-compose.monitoring-complete.yml logs -f prometheus

# Vérifier la connectivité
docker exec asmblr-prometheus wget -qO- http://localhost:9090/metrics

# Tester les alertes
curl -XPOST http://localhost:9093/api/v1/alerts
```

## 🔐 Sécurité

### Configuration

- **Authentication**: Grafana avec LDAP/OAuth
- **Authorization**: Rôles et permissions
- **Network**: Isolation des services
- **TLS**: HTTPS pour tous les services

### Bonnes Pratiques

- Changer les mots de passe par défaut
- Utiliser des secrets Docker
- Limiter l'accès réseau
- Surveiller les accès

## 📚 Ressources Additionnelles

### Documentation

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [ELK Stack Guide](https://www.elastic.co/guide/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)

### Communautés

- [Prometheus Slack](https://prometheus.io/community/)
- [Grafana Community](https://community.grafana.com/)
- [Elastic Discuss](https://discuss.elastic.co/)

---

## 🎯 Prochaines Étapes

1. **Configurer les notifications** (Slack, Email)
2. **Personnaliser les dashboards** selon vos besoins
3. **Ajouter des métriques métier** spécifiques
4. **Intégrer avec votre CI/CD**
5. **Automatiser la sauvegarde** des données

Pour toute question ou problème, consultez les logs des services ou contactez l'équipe de monitoring.
