# Dockerfile pour l'API Gateway/Orchestrator
FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY requirements.txt .
COPY requirements-gateway.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-gateway.txt

# Copier le code de l'application
COPY app/ ./app/
COPY shared/ ./shared/

# Définir les variables d'environnement
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Exposer le port
EXPOSE 8000

# Commande de démarrage
CMD ["python", "-m", "app.orchestrator.main"]
