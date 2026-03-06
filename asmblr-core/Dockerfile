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
COPY requirements/requirements-core.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-core.txt

# Copier le code de l'application
COPY app/ ./app/
COPY shared/ ./shared/

# Créer le répertoire de données
RUN mkdir -p /app/data

# Définir les variables d'environnement
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Exposer le port
EXPOSE 8001

# Commande de démarrage
CMD ["python", "-m", "app.core.main"]
