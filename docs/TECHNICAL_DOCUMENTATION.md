# 📚 Asmblr Technical Documentation

**Version 2.0** | *Last Updated: 2026-02-27*

## 📖 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [System Components](#system-components)
3. [API Documentation](#api-documentation)
4. [Database Schema](#database-schema)
5. [Configuration](#configuration)
6. [Deployment](#deployment)
7. [Monitoring & Logging](#monitoring--logging)
8. [Security](#security)
9. [Performance](#performance)
10. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture Overview

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web UI        │    │   CLI Interface │    │   API Gateway   │
│   (Streamlit)   │    │   (Python)      │    │   (FastAPI)     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │     Core Services         │
                    │  ┌─────────────────────┐  │
                    │  │   Run Manager       │  │
                    │  │   LLM Integration   │  │
                    │  │   Quality Gates     │  │
                    │  │   Auto-fix Engine   │  │
                    │  └─────────────────────┘  │
                    └─────────────┬─────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
┌─────────┴───────┐    ┌─────────┴───────┐    ┌─────────┴───────┐
│   Ollama LLM    │    │   PostgreSQL    │    │   Redis Cache   │
│   (Local)       │    │   Database      │    │   (Memory)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Design Principles

1. **Modular Architecture**: Each component is independent and replaceable
2. **AI-First**: LLM integration at the core of all operations
3. **Quality-Driven**: Built-in quality gates and auto-fixing
4. **Scalable**: Designed for horizontal scaling
5. **Observable**: Comprehensive monitoring and logging

### Technology Stack

#### Backend
- **Python 3.8+**: Core language
- **FastAPI**: REST API framework
- **CrewAI**: AI agent framework
- **LangChain**: LLM integration
- **SQLAlchemy**: Database ORM
- **Redis**: Caching and session storage

#### Frontend
- **Streamlit**: Web interface
- **HTML5/CSS3**: Modern UI components
- **JavaScript**: Interactive elements

#### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy and load balancing
- **PostgreSQL**: Primary database
- **Ollama**: Local LLM service

#### Monitoring
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Loki**: Log aggregation
- **Custom monitoring**: Application-specific metrics

---

## 🔧 System Components

### Core Services

#### Run Manager (`app/core/run_manager.py`)
**Purpose**: Central orchestration of venture creation runs

**Key Features**:
- Run lifecycle management
- State persistence
- Resource allocation
- Progress tracking

**API**:
```python
class RunManager:
    def create_run(topic: str) -> str
    def get_run(run_id: str) -> Dict
    def update_run(run_id: str, updates: Dict) -> bool
    def list_runs(limit: int = 50) -> List[Dict]
    def delete_run(run_id: str) -> bool
```

#### LLM Integration (`app/core/llm.py`)
**Purpose**: Unified interface for LLM operations

**Key Features**:
- Model selection and fallback
- Response caching
- Rate limiting
- Error handling

**API**:
```python
class LLMManager:
    def generate_response(prompt: str, model: str = None) -> str
    def check_ollama_status() -> bool
    def list_models() -> List[str]
    def get_model_info(model: str) -> Dict
```

#### Quality Gates (`app/core/quality.py`)
**Purpose**: Automated quality assessment and validation

**Key Features**:
- Code quality analysis
- Security scanning
- Performance validation
- Compliance checking

**API**:
```python
class QualityGate:
    def run_checks(run_id: str) -> Dict
    def get_score(run_id: str) -> float
    def get_issues(run_id: str) -> List[Dict]
    def auto_fix_issues(run_id: str) -> bool
```

### Agent System

#### Config Agent (`app/agents/config_agent.py`)
**Purpose**: Dynamic configuration optimization

**Responsibilities**:
- Resource allocation
- Threshold tuning
- Performance optimization
- Adaptation to system constraints

#### Signal Engine (`app/agents/signal_engine.py`)
**Purpose**: Market research and signal processing

**Responsibilities**:
- Web scraping
- Data analysis
- Signal quality assessment
- Competitive analysis

#### MVP Builder (`app/mvp_cycles.py`)
**Purpose**: Automated MVP development

**Responsibilities**:
- Code generation
- Testing
- Deployment
- Quality assurance

---

## 🌐 API Documentation

### REST API Endpoints

#### Health Checks
```http
GET /health
```
**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-27T10:00:00Z",
  "version": "2.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "ollama": "healthy"
  }
}
```

#### Run Management
```http
POST /api/runs
Content-Type: application/json

{
  "topic": "AI-powered expense tracking",
  "n_ideas": 3,
  "fast_mode": true,
  "execution_profile": "quick",
  "seed_inputs": {
    "icp": "Freelancers",
    "pains": ["Manual tracking", "Tax complexity"],
    "competitors": ["QuickBooks", "FreshBooks"],
    "context": "Remote work trend"
  }
}
```

**Response**:
```json
{
  "run_id": "20260227_100000_123456",
  "status": "created",
  "topic": "AI-powered expense tracking",
  "created_at": "2026-02-27T10:00:00Z"
}
```

```http
GET /api/runs/{run_id}
```

**Response**:
```json
{
  "run_id": "20260227_100000_123456",
  "status": "running",
  "stage": "signal_engine",
  "progress": 45,
  "created_at": "2026-02-27T10:00:00Z",
  "updated_at": "2026-02-27T10:15:00Z",
  "metrics": {
    "ideas_generated": 3,
    "quality_score": 0.85,
    "errors": 0
  }
}
```

```http
GET /api/runs
```

**Query Parameters**:
- `status`: Filter by status (created, running, completed, failed)
- `limit`: Maximum number of runs (default: 50)
- `offset`: Pagination offset (default: 0)

#### Quality Metrics
```http
GET /api/quality/{run_id}
```

**Response**:
```json
{
  "run_id": "20260227_100000_123456",
  "overall_score": 0.87,
  "categories": {
    "code_quality": 0.92,
    "security": 0.95,
    "performance": 0.78,
    "documentation": 0.85
  },
  "issues": [
    {
      "type": "warning",
      "category": "performance",
      "message": "High memory usage detected",
      "file": "src/main.py",
      "line": 45
    }
  ],
  "recommendations": [
    "Optimize database queries",
    "Add input validation",
    "Improve error handling"
  ]
}
```

#### System Status
```http
GET /api/status
```

**Response**:
```json
{
  "system": {
    "cpu_percent": 25.4,
    "memory_percent": 67.8,
    "disk_percent": 45.2,
    "active_runs": 2,
    "total_runs": 156
  },
  "services": {
    "database": {
      "status": "healthy",
      "connections": 8,
      "response_time": 12
    },
    "redis": {
      "status": "healthy",
      "memory_usage": "45MB",
      "hit_rate": 0.87
    },
    "ollama": {
      "status": "healthy",
      "models_loaded": 3,
      "queue_size": 0
    }
  },
  "performance": {
    "avg_response_time": 0.23,
    "requests_per_minute": 45,
    "error_rate": 0.02
  }
}
```

### WebSocket API

#### Real-time Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/updates/{run_id}');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};

// Message format:
{
  "type": "progress_update",
  "run_id": "20260227_100000_123456",
  "stage": "signal_engine",
  "progress": 67,
  "message": "Analyzing market signals...",
  "timestamp": "2026-02-27T10:20:00Z"
}
```

---

## 🗄️ Database Schema

### Tables Overview

#### runs
```sql
CREATE TABLE runs (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('created', 'running', 'completed', 'failed')),
    stage TEXT,
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    output_dir TEXT,
    metadata JSON
);
```

#### quality_metrics
```sql
CREATE TABLE quality_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    category TEXT NOT NULL,
    score REAL NOT NULL CHECK (score >= 0 AND score <= 1),
    details JSON,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);
```

#### audit_log
```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    action TEXT NOT NULL,
    details JSON,
    user_agent TEXT,
    ip_address TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);
```

#### system_metrics
```sql
CREATE TABLE system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    unit TEXT,
    tags JSON,
    created_at TEXT NOT NULL
);
```

### Indexes
```sql
-- Performance indexes
CREATE INDEX idx_runs_created_at ON runs(created_at);
CREATE INDEX idx_runs_status ON runs(status);
CREATE INDEX idx_runs_updated_at ON runs(updated_at);
CREATE INDEX idx_quality_metrics_run_id ON quality_metrics(run_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX idx_system_metrics_name_created ON system_metrics(metric_name, created_at);
```

---

## ⚙️ Configuration

### Environment Variables

#### Core Configuration
```bash
# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/asmblr
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your-redis-password

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_LLM_MODEL=llama3.1:8b
CODE_MODEL=qwen2.5-coder:7b
LLM_TIMEOUT=60
LLM_MAX_RETRIES=3

# Performance
WORKERS=4
MAX_CONNECTIONS=100
CACHE_SIZE=1024
CACHE_TTL=3600

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30
```

#### UI Configuration
```bash
# Streamlit
UI_HOST=0.0.0.0
UI_PORT=8501
UI_TITLE="Asmblr AI Venture Factory"

# Feature Flags
ENABLE_QUALITY_DASHBOARD=true
ENABLE_ADVANCED_FEATURES=true
ENABLE_BETA_FEATURES=false
```

#### Security Configuration
```bash
# Security
CORS_ORIGINS=["http://localhost:3000", "https://asmblr.ai"]
ALLOWED_HOSTS=["localhost", "asmblr.ai"]
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true

# Authentication
AUTH_ENABLED=false
OAUTH_PROVIDER=google
OAUTH_CLIENT_ID=your-oauth-client-id
OAUTH_CLIENT_SECRET=your-oauth-client-secret
```

### Configuration Files

#### docker-compose.production.yml
```yaml
version: "3.9"
services:
  asmblr:
    build: .
    environment:
      - ENVIRONMENT=production
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - ollama
```

#### nginx.conf
```nginx
upstream asmblr {
    server asmblr:8000;
}

upstream streamlit {
    server streamlit:8501;
}

server {
    listen 443 ssl http2;
    server_name asmblr.ai;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location /api/ {
        proxy_pass http://asmblr;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        proxy_pass http://streamlit;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🚀 Deployment

### Production Deployment

#### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 20GB+ disk space
- SSL certificates

#### Quick Deploy
```bash
# Clone repository
git clone https://github.com/asmblr/asmblr.git
cd asmblr

# Configure environment
cp .env.example .env.production
# Edit .env.production with your values

# Deploy
chmod +x deploy.sh
./deploy.sh
```

#### Manual Deploy
```bash
# Build images
docker-compose -f docker-compose.production.yml build

# Start services
docker-compose -f docker-compose.production.yml up -d

# Verify deployment
curl http://localhost:8000/health
```

### Scaling

#### Horizontal Scaling
```bash
# Scale API services
docker-compose -f docker-compose.production.yml up -d --scale asmblr=3

# Add load balancer
docker-compose -f docker-compose.production.yml up -d nginx
```

#### Database Scaling
```bash
# Enable read replicas
DATABASE_URL=postgresql://user:pass@master:5432/asmblr
DATABASE_READ_URLS=postgresql://user:pass@replica1:5432/asmblr,postgresql://user:pass@replica2:5432/asmblr
```

### Monitoring Deployment

#### Health Checks
```bash
# Check all services
docker-compose -f docker-compose.production.yml ps

# Check logs
docker-compose -f docker-compose.production.yml logs -f asmblr

# Monitor resources
docker stats
```

#### Automated Monitoring
```bash
# Start monitoring
python monitoring/production_monitoring.py --interval 60

# Check metrics
curl http://localhost:9090/metrics
```

---

## 📊 Monitoring & Logging

### Metrics Collection

#### System Metrics
- CPU usage
- Memory usage
- Disk usage
- Network I/O
- Process count

#### Application Metrics
- Request count
- Response time
- Error rate
- Active runs
- Queue sizes

#### Business Metrics
- Runs created per hour
- Success rate
- Average run duration
- Quality scores

### Logging Strategy

#### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General information messages
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

#### Log Formats
```json
{
  "timestamp": "2026-02-27T10:00:00Z",
  "level": "INFO",
  "service": "asmblr",
  "run_id": "20260227_100000_123456",
  "message": "Run created successfully",
  "context": {
    "topic": "AI expense tracking",
    "user_id": "user123"
  }
}
```

#### Log Destinations
- **File**: Local file system
- **Elasticsearch**: Centralized logging
- **Loki**: Grafana stack
- **Cloud**: AWS CloudWatch, GCP Cloud Logging

### Alerting

#### Alert Types
- **System**: CPU, memory, disk alerts
- **Application**: Error rate, response time
- **Business**: Failed runs, quality issues

#### Alert Channels
- **Email**: SMTP notifications
- **Slack**: Webhook integration
- **PagerDuty**: Critical alerts
- **Custom**: Webhook endpoints

#### Alert Configuration
```yaml
alerts:
  - name: "High CPU Usage"
    condition: "cpu_percent > 90"
    duration: "5m"
    severity: "critical"
    channels: ["email", "slack"]
  
  - name: "API Error Rate"
    condition: "error_rate > 10"
    duration: "2m"
    severity: "warning"
    channels: ["slack"]
```

---

## 🔒 Security

### Authentication & Authorization

#### JWT Authentication
```python
# Generate token
token = create_access_token(
    data={"sub": user_id, "exp": datetime.utcnow() + timedelta(hours=24)}
)

# Verify token
payload = verify_jwt_token(token)
user_id = payload.get("sub")
```

#### Role-Based Access Control
```python
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

class Permission(str, Enum):
    READ_RUNS = "read:runs"
    WRITE_RUNS = "write:runs"
    DELETE_RUNS = "delete:runs"
    ADMIN = "admin"
```

### Data Protection

#### Encryption at Rest
```python
# Database encryption
from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)
encrypted_data = cipher.encrypt(sensitive_data.encode())
```

#### Encryption in Transit
```python
# HTTPS enforcement
if not request.is_secure:
    return redirect(request.url.replace('http://', 'https://'))
```

#### Input Validation
```python
# Sanitize inputs
from bleach import clean
cleaned_input = clean(user_input, tags=[], strip=True)

# Validate schemas
from pydantic import BaseModel, validator

class RunRequest(BaseModel):
    topic: str
    n_ideas: int = Field(ge=1, le=10)
    
    @validator('topic')
    def validate_topic(cls, v):
        if len(v) < 3 or len(v) > 200:
            raise ValueError('Topic must be 3-200 characters')
        return v
```

### Security Headers
```python
# Security middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

### Audit Logging
```python
# Audit events
def log_audit_event(action: str, details: Dict, user_id: str = None):
    audit_entry = {
        "action": action,
        "details": details,
        "user_id": user_id,
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "timestamp": datetime.utcnow().isoformat()
    }
    # Store in audit log
```

---

## ⚡ Performance

### Optimization Strategies

#### Database Optimization
```python
# Connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)

# Query optimization
from sqlalchemy.orm import joinedload

query = session.query(Run).options(
    joinedload(Run.quality_metrics),
    joinedload(Run.audit_events)
)
```

#### Caching Strategy
```python
# Redis caching
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

@cache.memoize(timeout=300)
def get_run_metrics(run_id: str):
    # Expensive computation
    return compute_metrics(run_id)

# LLM response caching
def cached_llm_call(prompt: str, model: str):
    cache_key = f"llm:{hash(prompt)}:{model}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    response = llm.generate(prompt, model)
    redis_client.setex(cache_key, 3600, json.dumps(response))
    return response
```

#### Async Processing
```python
# Background tasks
from celery import Celery

celery_app = Celery('asmblr')

@celery_app.task
def process_run_async(run_id: str):
    # Long-running processing
    pass

# Async endpoints
from fastapi import BackgroundTasks

@app.post("/api/runs")
async def create_run(request: RunRequest, background_tasks: BackgroundTasks):
    run_id = create_run(request.topic)
    background_tasks.add_task(process_run_async, run_id)
    return {"run_id": run_id}
```

### Performance Monitoring

#### Response Time Tracking
```python
import time
from functools import wraps

def track_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            record_metric("response_time", duration, {"endpoint": func.__name__})
            return result
        except Exception as e:
            duration = time.time() - start_time
            record_metric("error_time", duration, {"endpoint": func.__name__})
            raise
    return wrapper
```

#### Resource Usage Monitoring
```python
# Memory monitoring
import psutil

def check_memory_usage():
    process = psutil.Process()
    memory_mb = process.memory_info().rss / (1024**2)
    if memory_mb > 500:  # 500MB threshold
        logger.warning(f"High memory usage: {memory_mb:.1f}MB")
        # Trigger cleanup or alert
```

---

## 🔧 Troubleshooting

### Common Issues

#### High Memory Usage
**Symptoms**: Slow response times, OOM errors
**Causes**: Memory leaks, large objects, inefficient caching
**Solutions**:
```python
# Monitor memory
import tracemalloc
tracemalloc.start()

# Check memory usage
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

# Cleanup
import gc
gc.collect()
```

#### Database Connection Issues
**Symptoms**: Connection timeouts, connection pool exhaustion
**Causes**: Too many connections, long-running queries
**Solutions**:
```python
# Connection pool tuning
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 20,
    "max_overflow": 10,
    "pool_timeout": 30,
    "pool_recycle": 3600
}

# Query optimization
from sqlalchemy import text

# Use EXPLAIN ANALYZE
result = session.execute(text("EXPLAIN ANALYZE SELECT * FROM runs"))
```

#### LLM Service Issues
**Symptoms**: Slow responses, timeouts, model errors
**Causes**: Ollama down, model not loaded, resource constraints
**Solutions**:
```python
# Health check
def check_ollama_health():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

# Fallback models
FALLBACK_MODELS = {
    "llama3.1:8b": ["llama3:8b", "qwen2.5:7b"],
    "qwen2.5-coder:7b": ["qwen2.5:7b", "stable-code:3b"]
}
```

### Debugging Tools

#### Logging Configuration
```python
# Debug logging
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
```

#### Performance Profiling
```python
# Profile decorator
import cProfile
import pstats

def profile_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        result = func(*args, **kwargs)
        pr.disable()
        
        stats = pstats.Stats(pr)
        stats.sort_stats('cumulative')
        stats.print_stats(10)
        
        return result
    return wrapper
```

#### Health Check Endpoints
```python
@app.get("/debug/health")
async def debug_health():
    return {
        "database": check_database_health(),
        "redis": check_redis_health(),
        "ollama": check_ollama_health(),
        "memory": psutil.virtual_memory()._asdict(),
        "disk": psutil.disk_usage('/')._asdict()
    }
```

### Recovery Procedures

#### Database Recovery
```bash
# Backup database
docker-compose exec postgres pg_dump -U asmblr asmblr > backup.sql

# Restore database
docker-compose exec -T postgres psql -U asmblr asmblr < backup.sql

# Check consistency
docker-compose exec postgres pg_dump -U asmblr asmblr | head
```

#### Service Recovery
```bash
# Restart services
docker-compose restart asmblr

# Check logs
docker-compose logs asmblr

# Scale down/up
docker-compose up -d --scale asmblr=0
docker-compose up -d --scale asmblr=2
```

#### Data Recovery
```python
# Recover from backup
def recover_run(run_id: str):
    backup_path = f"backups/{run_id}"
    if os.path.exists(backup_path):
        shutil.copytree(backup_path, f"runs/{run_id}")
        return True
    return False
```

---

## 📞 Support

### Getting Help

1. **Documentation**: Check this technical guide first
2. **API Docs**: Visit `/docs` endpoint
3. **Health Checks**: Use `/debug/health` endpoint
4. **Logs**: Check `logs/` directory
5. **Community**: Join our Discord
6. **Issues**: Report bugs on GitHub

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for technical contribution guidelines.

### License

Asmblr is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

**Technical Documentation v2.0**  
*Built with ❤️ by the Asmblr Team*
