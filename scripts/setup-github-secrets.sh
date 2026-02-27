#!/bin/bash

# Script de configuration pour les secrets dans GitHub Actions
# Utilisation de GitHub Secrets pour la CI/CD

set -e

echo "🔐 Configuration des secrets GitHub Actions pour Asmblr..."

# Vérifier si gh CLI est installé
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI n'est pas installé"
    echo "Installation de GitHub CLI..."
    
    # Installation pour Linux
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update
        sudo apt-get install -y curl
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y gh
    # Installation pour macOS
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install gh
        else
            echo "❌ Veuillez installer Homebrew d'abord"
            exit 1
        fi
    else
        echo "❌ OS non supporté pour l'installation automatique"
        exit 1
    fi
fi

# Vérifier l'authentification
if ! gh auth status &> /dev/null; then
    echo "❌ Non authentifié à GitHub"
    echo "Veuillez vous authentifier:"
    echo "  gh auth login"
    exit 1
fi

# Variables de configuration
REPO_NAME=${REPO_NAME:-$(git config --get remote.origin.url | sed 's/.*:\/\/github.com\///' | sed 's/\.git$//')}
ENVIRONMENT=${ENVIRONMENT:-"production"}

echo "🏗️  Configuration pour le repository: $REPO_NAME"
echo "🌍 Environnement: $ENVIRONMENT"

# Fonction pour créer un secret
create_secret() {
    local secret_name=$1
    local secret_value=$2
    local description=$3
    
    echo "🔧 Création du secret: $secret_name"
    
    # Vérifier si le secret existe déjà
    if gh secret list --repo $REPO_NAME | grep -q "^$secret_name$"; then
        echo "⚠️  Secret $secret_name existe déjà, mise à jour..."
        echo "$secret_value" | gh secret set $secret_name --repo $REPO_NAME
    else
        echo "$secret_value" | gh secret set $secret_name --repo $REPO_NAME
    fi
    
    echo "✅ Secret $secret_name configuré"
}

# Secrets de base de données
echo "🗄️  Configuration des secrets de base de données..."
DB_PASSWORD=$(openssl rand -base64 32)
create_secret "DATABASE_PASSWORD" "$DB_PASSWORD" "Database password for Asmblr"

# Secrets API
echo "🔑 Configuration des secrets API..."
SECRET_KEY=$(openssl rand -base64 64)
JWT_SECRET=$(openssl rand -base64 32)
create_secret "SECRET_KEY" "$SECRET_KEY" "Secret key for API"
create_secret "JWT_SECRET" "$JWT_SECRET" "JWT secret for authentication"

# Secrets Docker
echo "🐳 Configuration des secrets Docker..."
DOCKER_USERNAME=${DOCKER_USERNAME:-"asmblr"}
DOCKER_PASSWORD=$(openssl rand -base64 32)
create_secret "DOCKER_USERNAME" "$DOCKER_USERNAME" "Docker Hub username"
create_secret "DOCKER_PASSWORD" "$DOCKER_PASSWORD" "Docker Hub password"

# Secrets AWS (si applicable)
echo "☁️  Configuration des secrets AWS..."
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    create_secret "AWS_ACCESS_KEY_ID" "$AWS_ACCESS_KEY_ID" "AWS Access Key ID"
    create_secret "AWS_SECRET_ACCESS_KEY" "$AWS_SECRET_ACCESS_KEY" "AWS Secret Access Key"
    create_secret "AWS_REGION" "${AWS_REGION:-us-east-1}" "AWS Region"
    create_secret "S3_BUCKET" "${S3_BUCKET:-asmblr-backups}" "S3 bucket for backups"
else
    echo "⚠️  Credentials AWS non fournis, secrets AWS non configurés"
fi

# Secrets Monitoring
echo "📊 Configuration des secrets Monitoring..."
GRAFANA_PASSWORD=$(openssl rand -base64 16)
create_secret "GRAFANA_PASSWORD" "$GRAFANA_PASSWORD" "Grafana admin password"

# Secrets Staging
echo "🚀 Configuration des secrets Staging..."
STAGING_DB_PASSWORD=$(openssl rand -base64 32)
STAGING_SECRET_KEY=$(openssl rand -base64 64)
STAGING_GRAFANA_PASSWORD=$(openssl rand -base64 16)

create_secret "STAGING_DATABASE_PASSWORD" "$STAGING_DB_PASSWORD" "Staging database password"
create_secret "STAGING_SECRET_KEY" "$STAGING_SECRET_KEY" "Staging secret key"
create_secret "STAGING_GRAFANA_PASSWORD" "$STAGING_GRAFANA_PASSWORD" "Staging Grafana password"

# Secrets Production
echo "🏭 Configuration des secrets Production..."
PROD_DB_PASSWORD=$(openssl rand -base64 32)
PROD_REPLICATION_PASSWORD=$(openssl rand -base64 32)

create_secret "PRODUCTION_DATABASE_PASSWORD" "$PROD_DB_PASSWORD" "Production database password"
create_secret "REPLICATION_PASSWORD" "$PROD_REPLICATION_PASSWORD" "Database replication password"

# Secrets Notification
echo "📬 Configuration des secrets Notification..."
SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL:-""}
if [ -n "$SLACK_WEBHOOK_URL" ]; then
    create_secret "SLACK_WEBHOOK_URL" "$SLACK_WEBHOOK_URL" "Slack webhook URL for notifications"
fi

# Email configuration
SMTP_USERNAME=${SMTP_USERNAME:-""}
SMTP_PASSWORD=${SMTP_PASSWORD:-""}
if [ -n "$SMTP_USERNAME" ] && [ -n "$SMTP_PASSWORD" ]; then
    create_secret "SMTP_USERNAME" "$SMTP_USERNAME" "SMTP username for email notifications"
    create_secret "SMTP_PASSWORD" "$SMTP_PASSWORD" "SMTP password for email notifications"
fi

# Secrets pour les tests
echo "🧪 Configuration des secrets pour les tests..."
TEST_DATABASE_URL="sqlite:///./test.db"
create_secret "TEST_DATABASE_URL" "$TEST_DATABASE_URL" "Test database URL"

# Créer le script de gestion des secrets
cat > /usr/local/bin/gh-manage-secrets.sh <<'EOF'
#!/bin/bash

# Script pour gérer les secrets GitHub Actions
# Usage: gh-manage-secrets.sh <action> [secret-name]

set -e

REPO_NAME=${REPO_NAME:-$(git config --get remote.origin.url | sed 's/.*:\/\/github.com\///' | sed 's/\.git$//')}

if [ $# -lt 1 ]; then
    echo "Usage: $0 <action> [secret-name]"
    echo "Actions:"
    echo "  list - Lister tous les secrets"
    echo "  get <secret-name> - Afficher la valeur d'un secret"
    echo "  set <secret-name> - Définir un nouveau secret"
    echo "  delete <secret-name> - Supprimer un secret"
    echo "  rotate <secret-name> - Faire la rotation d'un secret"
    exit 1
fi

ACTION=$1
SECRET_NAME=$2

case $ACTION in
    "list")
        echo "📋 Secrets pour $REPO_NAME:"
        gh secret list --repo $REPO_NAME
        ;;
    "get")
        if [ -z "$SECRET_NAME" ]; then
            echo "❌ Nom du secret requis"
            exit 1
        fi
        echo "🔍 Valeur du secret '$SECRET_NAME':"
        gh secret view $SECRET_NAME --repo $REPO_NAME
        ;;
    "set")
        if [ -z "$SECRET_NAME" ]; then
            echo "❌ Nom du secret requis"
            exit 1
        fi
        echo "🔧 Définition du secret '$SECRET_NAME':"
        echo "Entrez la valeur du secret (Ctrl+D pour terminer):"
        VALUE=$(cat)
        echo "$VALUE" | gh secret set $SECRET_NAME --repo $REPO_NAME
        echo "✅ Secret '$SECRET_NAME' défini"
        ;;
    "delete")
        if [ -z "$SECRET_NAME" ]; then
            echo "❌ Nom du secret requis"
            exit 1
        fi
        echo "⚠️  Suppression du secret '$SECRET_NAME'..."
        read -p "Êtes-vous sûr? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            gh secret delete $SECRET_NAME --repo $REPO_NAME
            echo "✅ Secret '$SECRET_NAME' supprimé"
        else
            echo "❌ Opération annulée"
        fi
        ;;
    "rotate")
        if [ -z "$SECRET_NAME" ]; then
            echo "❌ Nom du secret requis"
            exit 1
        fi
        echo "🔄 Rotation du secret '$SECRET_NAME'..."
        
        # Générer une nouvelle valeur selon le type de secret
        case $SECRET_NAME in
            *"PASSWORD" | *"password")
                NEW_VALUE=$(openssl rand -base64 32)
                ;;
            *"SECRET" | *"secret")
                NEW_VALUE=$(openssl rand -base64 64)
                ;;
            *"KEY" | *"key")
                NEW_VALUE=$(openssl rand -base64 32)
                ;;
            *)
                echo "❌ Type de secret non reconnu pour la rotation automatique"
                echo "Veuillez utiliser la commande 'set' pour définir manuellement"
                exit 1
                ;;
        esac
        
        echo "$NEW_VALUE" | gh secret set $SECRET_NAME --repo $REPO_NAME
        echo "✅ Secret '$SECRET_NAME' mis à jour"
        ;;
    *)
        echo "❌ Action non reconnue: $ACTION"
        exit 1
        ;;
esac
EOF

chmod +x /usr/local/bin/gh-manage-secrets.sh

# Créer le script de backup des secrets
cat > /usr/local/bin/gh-backup-secrets.sh <<'EOF'
#!/bin/bash

# Script pour sauvegarder les secrets GitHub Actions
# Usage: gh-backup-secrets.sh [output-file]

set -e

REPO_NAME=${REPO_NAME:-$(git config --get remote.origin.url | sed 's/.*:\/\/github.com\///' | sed 's/\.git$//')}
OUTPUT_FILE=${1:-"secrets-backup-$(date +%Y%m%d-%H%M%S).json"}

echo "📦 Sauvegarde des secrets pour $REPO_NAME..."

# Créer le fichier JSON de backup
echo "{" > $OUTPUT_FILE
echo "  \"repository\": \"$REPO_NAME\"," >> $OUTPUT_FILE
echo "  \"timestamp\": \"$(date -Iseconds)\"," >> $OUTPUT_FILE
echo "  \"secrets\": {" >> $OUTPUT_FILE

# Récupérer tous les secrets
SECRETS=$(gh secret list --repo $REPO_NAME | tail -n +2 | awk '{print $1}')
FIRST=true

for SECRET in $SECRETS; do
    if [ "$FIRST" = true ]; then
        FIRST=false
    else
        echo "," >> $OUTPUT_FILE
    fi
    
    VALUE=$(gh secret view $SECRET --repo $REPO_NAME)
    # Échapper les guillemets dans la valeur
    VALUE=$(echo "$VALUE" | sed 's/"/\\"/g')
    echo "    \"$SECRET\": \"$VALUE\"" >> $OUTPUT_FILE
done

echo "" >> $OUTPUT_FILE
echo "  }" >> $OUTPUT_FILE
echo "}" >> $OUTPUT_FILE

echo "✅ Sauvegarde terminée: $OUTPUT_FILE"
echo "⚠️  Ce fichier contient des secrets sensibles, stockez-le en sécurité!"
EOF

chmod +x /usr/local/bin/gh-backup-secrets.sh

# Créer le script de restauration des secrets
cat > /usr/local/bin/gh-restore-secrets.sh <<'EOF'
#!/bin/bash

# Script pour restaurer les secrets depuis un fichier de backup
# Usage: gh-restore-secrets.sh <backup-file>

set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup-file>"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Fichier de backup non trouvé: $BACKUP_FILE"
    exit 1
fi

echo "🔄 Restauration des secrets depuis $BACKUP_FILE..."

# Vérifier que le fichier est un JSON valide
if ! jq empty "$BACKUP_FILE" 2>/dev/null; then
    echo "❌ Fichier JSON invalide"
    exit 1
fi

REPO_NAME=$(jq -r '.repository' "$BACKUP_FILE")
TIMESTAMP=$(jq -r '.timestamp' "$BACKUP_FILE")

echo "🏗️  Repository: $REPO_NAME"
echo "📅 Backup du: $TIMESTAMP"

# Confirmer la restauration
read -p "⚠️  Cette action va écraser les secrets existants. Continuer? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Opération annulée"
    exit 1
fi

# Restaurer chaque secret
jq -r '.secrets | to_entries[] | "\(.key)=\(.value)"' "$BACKUP_FILE" | while IFS='=' read -r key value; do
    echo "🔧 Restauration du secret: $key"
    echo "$value" | gh secret set "$key" --repo "$REPO_NAME"
    echo "✅ Secret $key restauré"
done

echo "🎉 Restauration terminée!"
EOF

chmod +x /usr/local/bin/gh-restore-secrets.sh

# Créer le fichier de configuration pour les environnements
cat > .env.github-secrets <<EOF
# Configuration GitHub Secrets pour les environnements

# Production
DATABASE_PASSWORD=\${{ secrets.DATABASE_PASSWORD }}
SECRET_KEY=\${{ secrets.SECRET_KEY }}
JWT_SECRET=\${{ secrets.JWT_SECRET }}
GRAFANA_PASSWORD=\${{ secrets.GRAFANA_PASSWORD }}

# Docker
DOCKER_USERNAME=\${{ secrets.DOCKER_USERNAME }}
DOCKER_PASSWORD=\${{ secrets.DOCKER_PASSWORD }}

# AWS (optionnel)
AWS_ACCESS_KEY_ID=\${{ secrets.AWS_ACCESS_KEY_ID }}
AWS_SECRET_ACCESS_KEY=\${{ secrets.AWS_SECRET_ACCESS_KEY }}
AWS_REGION=\${{ secrets.AWS_REGION }}
S3_BUCKET=\${{ secrets.S3_BUCKET }}

# Staging
STAGING_DATABASE_PASSWORD=\${{ secrets.STAGING_DATABASE_PASSWORD }}
STAGING_SECRET_KEY=\${{ secrets.STAGING_SECRET_KEY }}
STAGING_GRAFANA_PASSWORD=\${{ secrets.STAGING_GRAFANA_PASSWORD }}

# Production
PRODUCTION_DATABASE_PASSWORD=\${{ secrets.PRODUCTION_DATABASE_PASSWORD }}
REPLICATION_PASSWORD=\${{ secrets.REPLICATION_PASSWORD }}

# Notifications
SLACK_WEBHOOK_URL=\${{ secrets.SLACK_WEBHOOK_URL }}
SMTP_USERNAME=\${{ secrets.SMTP_USERNAME }}
SMTP_PASSWORD=\${{ secrets.SMTP_PASSWORD }}

# Tests
TEST_DATABASE_URL=\${{ secrets.TEST_DATABASE_URL }}
EOF

echo "✅ Configuration GitHub Secrets terminée!"
echo ""
echo "📋 Informations importantes:"
echo "  - Repository: $REPO_NAME"
echo "  - Script de gestion: gh-manage-secrets.sh"
echo "  - Script de backup: gh-backup-secrets.sh"
echo "  - Script de restauration: gh-restore-secrets.sh"
echo ""
echo "🔗 Secrets configurés:"
echo "  - DATABASE_PASSWORD"
echo "  - SECRET_KEY"
echo "  - JWT_SECRET"
echo "  - DOCKER_USERNAME/DOCKER_PASSWORD"
echo "  - GRAFANA_PASSWORD"
echo "  - STAGING_* (pour l'environnement staging)"
echo "  - PRODUCTION_* (pour l'environnement production)"
echo ""
echo "⚠️  Actions requises:"
echo "  1. Vérifiez les secrets dans les settings du repository GitHub"
echo "  2. Mettez à jour vos workflows pour utiliser les secrets"
echo "  3. Configurez la rotation régulière des secrets"
echo ""
echo "🔗 Documentation: https://docs.github.com/en/actions/security-guides"
