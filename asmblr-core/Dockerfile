# Dockerfile pour asmblr-core
FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY requirements/requirements.txt ./
COPY asmblr-core/requirements-core.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-core.txt

# Copier le code de l'application
COPY service_security.py .
COPY app/ ./app/
COPY asmblr-core/ ./asmblr-core/

# Créer le répertoire de données
RUN mkdir -p /app/data

# Définir les variables d'environnement
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Exposer le port
EXPOSE 8001

# Commande de démarrage
CMD ["python", "-m", "uvicorn", "main:app", "--app-dir", "/app/asmblr-core", "--host", "0.0.0.0", "--port", "8001"]
