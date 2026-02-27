#!/bin/bash

# Script de configuration pour AWS Secrets Manager
# Alternative à Vault pour la gestion des secrets

set -e

echo "🔐 Configuration d'AWS Secrets Manager pour Asmblr..."

# Vérifier les prérequis
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI n'est pas installé"
    echo "Installation d'AWS CLI..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
fi

# Vérifier les credentials AWS
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Credentials AWS non configurés"
    echo "Veuillez configurer vos credentials AWS:"
    echo "  aws configure"
    exit 1
fi

echo "✅ AWS CLI configuré"

# Variables de configuration
AWS_REGION=${AWS_REGION:-"us-east-1"}
PROJECT_NAME="asmblr"
ENVIRONMENT=${ENVIRONMENT:-"development"}

echo "🌍 Configuration pour la région: $AWS_REGION"
echo "🏗️  Environnement: $ENVIRONMENT"

# Créer les secrets
echo "📝 Création des secrets dans AWS Secrets Manager..."

# Secret de base de données
echo "🗄️  Création du secret de base de données..."
DB_PASSWORD=$(openssl rand -base64 32)
aws secretsmanager create-secret \
    --name "${PROJECT_NAME}/${ENVIRONMENT}/database" \
    --description "Database credentials for Asmblr ${ENVIRONMENT}" \
    --secret-string "{\"username\":\"asmblr\",\"password\":\"${DB_PASSWORD}\",\"host\":\"localhost\",\"port\":\"5432\"}" \
    --region $AWS_REGION || \
    aws secretsmanager update-secret \
        --secret-id "${PROJECT_NAME}/${ENVIRONMENT}/database" \
        --secret-string "{\"username\":\"asmblr\",\"password\":\"${DB_PASSWORD}\",\"host\":\"localhost\",\"port\":\"5432\"}" \
        --region $AWS_REGION

# Secret API
echo "🔑 Création du secret API..."
API_SECRET_KEY=$(openssl rand -base64 64)
JWT_SECRET=$(openssl rand -base64 32)
aws secretsmanager create-secret \
    --name "${PROJECT_NAME}/${ENVIRONMENT}/api" \
    --description "API secrets for Asmblr ${ENVIRONMENT}" \
    --secret-string "{\"secret_key\":\"${API_SECRET_KEY}\",\"jwt_secret\":\"${JWT_SECRET}\"}" \
    --region $AWS_REGION || \
    aws secretsmanager update-secret \
        --secret-id "${PROJECT_NAME}/${ENVIRONMENT}/api" \
        --secret-string "{\"secret_key\":\"${API_SECRET_KEY}\",\"jwt_secret\":\"${JWT_SECRET}\"}" \
        --region $AWS_REGION

# Secret Docker Registry
echo "🐳 Création du secret Docker Registry..."
DOCKER_PASSWORD=$(openssl rand -base64 32)
aws secretsmanager create-secret \
    --name "${PROJECT_NAME}/${ENVIRONMENT}/docker" \
    --description "Docker registry credentials for Asmblr ${ENVIRONMENT}" \
    --secret-string "{\"username\":\"asmblr\",\"password\":\"${DOCKER_PASSWORD}\"}" \
    --region $AWS_REGION || \
    aws secretsmanager update-secret \
        --secret-id "${PROJECT_NAME}/${ENVIRONMENT}/docker" \
        --secret-string "{\"username\":\"asmblr\",\"password\":\"${DOCKER_PASSWORD}\"}" \
        --region $AWS_REGION

# Secret Monitoring
echo "📊 Création du secret Monitoring..."
GRAFANA_PASSWORD=$(openssl rand -base64 16)
aws secretsmanager create-secret \
    --name "${PROJECT_NAME}/${ENVIRONMENT}/monitoring" \
    --description "Monitoring credentials for Asmblr ${ENVIRONMENT}" \
    --secret-string "{\"grafana_password\":\"${GRAFANA_PASSWORD}\"}" \
    --region $AWS_REGION || \
    aws secretsmanager update-secret \
        --secret-id "${PROJECT_NAME}/${ENVIRONMENT}/monitoring" \
        --secret-string "{\"grafana_password\":\"${GRAFANA_PASSWORD}\"}" \
        --region $AWS_REGION

# Secret S3
echo "📦 Création du secret S3..."
S3_ACCESS_KEY=$(openssl rand -base64 32)
S3_SECRET_KEY=$(openssl rand -base64 32)
aws secretsmanager create-secret \
    --name "${PROJECT_NAME}/${ENVIRONMENT}/s3" \
    --description "S3 credentials for Asmblr ${ENVIRONMENT}" \
    --secret-string "{\"access_key\":\"${S3_ACCESS_KEY}\",\"secret_key\":\"${S3_SECRET_KEY}\"}" \
    --region $AWS_REGION || \
    aws secretsmanager update-secret \
        --secret-id "${PROJECT_NAME}/${ENVIRONMENT}/s3" \
        --secret-string "{\"access_key\":\"${S3_ACCESS_KEY}\",\"secret_key\":\"${S3_SECRET_KEY}\"}" \
        --region $AWS_REGION

# Créer les politiques IAM
echo "🔐 Création des politiques IAM..."

# Politique pour lire les secrets
cat > /tmp/asmblr-secrets-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": [
                "arn:aws:secretsmanager:${AWS_REGION}:*:${PROJECT_NAME}/${ENVIRONMENT}/*"
            ]
        }
    ]
}
EOF

# Créer la politique
aws iam create-policy \
    --policy-name "${PROJECT_NAME}-${ENVIRONMENT}-secrets-policy" \
    --policy-document file:///tmp/asmblr-secrets-policy.json \
    --region $AWS_REGION || echo "Politique déjà existante"

# Créer le rôle pour les applications EC2
cat > /tmp/asmblr-trust-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# Créer le rôle
aws iam create-role \
    --role-name "${PROJECT_NAME}-${ENVIRONMENT}-secrets-role" \
    --assume-role-policy-document file:///tmp/asmblr-trust-policy.json \
    --region $AWS_REGION || echo "Rôle déjà existant"

# Attacher la politique au rôle
aws iam attach-role-policy \
    --role-name "${PROJECT_NAME}-${ENVIRONMENT}-secrets-role" \
    --policy-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/${PROJECT_NAME}-${ENVIRONMENT}-secrets-policy"

# Créer le profil d'instance
aws iam create-instance-profile \
    --instance-profile-name "${PROJECT_NAME}-${ENVIRONMENT}-secrets-profile" \
    --region $AWS_REGION || echo "Profil déjà existant"

# Attacher le rôle au profil
aws iam add-role-to-instance-profile \
    --instance-profile-name "${PROJECT_NAME}-${ENVIRONMENT}-secrets-profile" \
    --role-name "${PROJECT_NAME}-${ENVIRONMENT}-secrets-role"

# Créer le script de récupération des secrets
cat > /usr/local/bin/aws-get-secret.sh <<'EOF'
#!/bin/bash

# Script pour récupérer les secrets depuis AWS Secrets Manager
# Usage: aws-get-secret.sh <secret-name> [key]

set -e

AWS_REGION=${AWS_REGION:-"us-east-1"}
PROJECT_NAME=${PROJECT_NAME:-"asmblr"}
ENVIRONMENT=${ENVIRONMENT:-"development"}

if [ $# -lt 1 ]; then
    echo "Usage: $0 <secret-name> [key]"
    echo "Example: $0 database password"
    echo "Example: $0 api"
    exit 1
fi

SECRET_NAME=$1
KEY=$2

# Construire le nom complet du secret
FULL_SECRET_NAME="${PROJECT_NAME}/${ENVIRONMENT}/${SECRET_NAME}"

# Récupérer le secret
SECRET=$(aws secretsmanager get-secret-value \
    --secret-id $FULL_SECRET_NAME \
    --region $AWS_REGION \
    --query SecretString \
    --output text 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "❌ Impossible de récupérer le secret: $FULL_SECRET_NAME"
    exit 1
fi

# Si une clé est spécifiée, extraire cette valeur
if [ -n "$KEY" ]; then
    VALUE=$(echo $SECRET | jq -r ".$KEY" 2>/dev/null)
    if [ $? -eq 0 ] && [ "$VALUE" != "null" ]; then
        echo $VALUE
    else
        echo "❌ Clé '$KEY' non trouvée dans le secret"
        exit 1
    fi
else
    # Afficher tout le secret
    echo $SECRET
fi
EOF

chmod +x /usr/local/bin/aws-get-secret.sh

# Créer le script de configuration des applications
cat > /usr/local/bin/aws-configure-app.sh <<'EOF'
#!/bin/bash

# Script pour configurer les variables d'environnement depuis AWS Secrets Manager
# Usage: aws-configure-app.sh <app-name>

set -e

AWS_REGION=${AWS_REGION:-"us-east-1"}
PROJECT_NAME=${PROJECT_NAME:-"asmblr"}
ENVIRONMENT=${ENVIRONMENT:-"development"}

if [ $# -ne 1 ]; then
    echo "Usage: $0 <app-name>"
    echo "Example: $0 asmblr-api"
    exit 1
fi

APP_NAME=$1

# Récupérer et exporter les secrets
echo "🔧 Configuration des secrets pour $APP_NAME..."

# Base de données
DB_PASSWORD=$(aws-get-secret.sh database password)
export DATABASE_PASSWORD=$DB_PASSWORD

# API
SECRET_KEY=$(aws-get-secret.sh api secret_key)
export SECRET_KEY=$SECRET_KEY

JWT_SECRET=$(aws-get-secret.sh api jwt_secret)
export JWT_SECRET=$JWT_SECRET

# Monitoring
GRAFANA_PASSWORD=$(aws-get-secret.sh monitoring grafana_password)
export GRAFANA_PASSWORD=$GRAFANA_PASSWORD

# Docker
DOCKER_PASSWORD=$(aws-get-secret.sh docker password)
export DOCKER_PASSWORD=$DOCKER_PASSWORD

echo "✅ Secrets configurés pour $APP_NAME"
echo "📋 Variables d'environnement exportées:"
env | grep -E "(DATABASE_PASSWORD|SECRET_KEY|JWT_SECRET|GRAFANA_PASSWORD|DOCKER_PASSWORD)"
EOF

chmod +x /usr/local/bin/aws-configure-app.sh

# Créer le script de rotation des secrets
cat > /usr/local/bin/aws-rotate-secrets.sh <<'EOF'
#!/bin/bash

# Script pour faire la rotation automatique des secrets
# Usage: aws-rotate-secrets.sh [secret-name]

set -e

AWS_REGION=${AWS_REGION:-"us-east-1"}
PROJECT_NAME=${PROJECT_NAME:-"asmblr"}
ENVIRONMENT=${ENVIRONMENT:-"development"}

if [ $# -eq 0 ]; then
    echo "🔄 Rotation de tous les secrets..."
    SECRETS=("database" "api" "docker" "monitoring" "s3")
else
    SECRETS=("$1")
fi

for SECRET_NAME in "${SECRETS[@]}"; do
    echo "🔄 Rotation du secret: $SECRET_NAME"
    
    # Générer de nouvelles valeurs
    case $SECRET_NAME in
        "database")
            NEW_PASSWORD=$(openssl rand -base64 32)
            NEW_SECRET="{\"username\":\"asmblr\",\"password\":\"${NEW_PASSWORD}\",\"host\":\"localhost\",\"port\":\"5432\"}"
            ;;
        "api")
            NEW_SECRET_KEY=$(openssl rand -base64 64)
            NEW_JWT_SECRET=$(openssl rand -base64 32)
            NEW_SECRET="{\"secret_key\":\"${NEW_SECRET_KEY}\",\"jwt_secret\":\"${NEW_JWT_SECRET}\"}"
            ;;
        "docker")
            NEW_PASSWORD=$(openssl rand -base64 32)
            NEW_SECRET="{\"username\":\"asmblr\",\"password\":\"${NEW_PASSWORD}\"}"
            ;;
        "monitoring")
            NEW_PASSWORD=$(openssl rand -base64 16)
            NEW_SECRET="{\"grafana_password\":\"${NEW_PASSWORD}\"}"
            ;;
        "s3")
            NEW_ACCESS_KEY=$(openssl rand -base64 32)
            NEW_SECRET_KEY=$(openssl rand -base64 32)
            NEW_SECRET="{\"access_key\":\"${NEW_ACCESS_KEY}\",\"secret_key\":\"${NEW_SECRET_KEY}\"}"
            ;;
        *)
            echo "❌ Secret non reconnu: $SECRET_NAME"
            continue
            ;;
    esac
    
    # Mettre à jour le secret
    FULL_SECRET_NAME="${PROJECT_NAME}/${ENVIRONMENT}/${SECRET_NAME}"
    aws secretsmanager update-secret \
        --secret-id $FULL_SECRET_NAME \
        --secret-string "$NEW_SECRET" \
        --region $AWS_REGION
    
    echo "✅ Secret $SECRET_NAME mis à jour"
done

echo "🎉 Rotation terminée"
EOF

chmod +x /usr/local/bin/aws-rotate-secrets.sh

# Créer le fichier d'environnement pour Docker Compose
cat > .env.aws-secrets <<EOF
# Configuration AWS Secrets Manager pour Docker Compose
AWS_REGION=$AWS_REGION
PROJECT_NAME=$PROJECT_NAME
ENVIRONMENT=$ENVIRONMENT

# Utiliser les scripts de récupération
DATABASE_PASSWORD=\$(aws-get-secret.sh database password)
SECRET_KEY=\$(aws-get-secret.sh api secret_key)
JWT_SECRET=\$(aws-get-secret.sh api jwt_secret)
GRAFANA_PASSWORD=\$(aws-get-secret.sh monitoring grafana_password)
DOCKER_PASSWORD=\$(aws-get-secret.sh docker password)
EOF

# Nettoyer les fichiers temporaires
rm -f /tmp/asmblr-secrets-policy.json /tmp/asmblr-trust-policy.json

echo "✅ Configuration AWS Secrets Manager terminée!"
echo ""
echo "📋 Informations importantes:"
echo "  - Région AWS: $AWS_REGION"
echo "  - Nom du projet: $PROJECT_NAME"
echo "  - Environnement: $ENVIRONMENT"
echo "  - Script de récupération: aws-get-secret.sh"
echo "  - Script de configuration: aws-configure-app.sh"
echo "  - Script de rotation: aws-rotate-secrets.sh"
echo ""
echo "🔗 Secrets créés:"
echo "  - ${PROJECT_NAME}/${ENVIRONMENT}/database"
echo "  - ${PROJECT_NAME}/${ENVIRONMENT}/api"
echo "  - ${PROJECT_NAME}/${ENVIRONMENT}/docker"
echo "  - ${PROJECT_NAME}/${ENVIRONMENT}/monitoring"
echo "  - ${PROJECT_NAME}/${ENVIRONMENT}/s3"
echo ""
echo "🔗 Documentation: https://docs.aws.amazon.com/secretsmanager/"
echo ""
echo "⚠️  Actions requises:"
echo "  1. Attachez le profil d'instance IAM à vos instances EC2"
echo "  2. Configurez la rotation automatique des secrets si nécessaire"
echo "  3. Utilisez les scripts dans vos applications"
