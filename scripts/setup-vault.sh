#!/bin/bash

# Script de configuration pour HashiCorp Vault
# Installation et configuration pour la gestion des secrets

set -e

echo "🔐 Configuration de HashiCorp Vault pour Asmblr..."

# Vérifier si Vault est déjà installé
if command -v vault &> /dev/null; then
    echo "✅ Vault est déjà installé"
    vault version
else
    echo "📦 Installation de Vault..."
    
    # Ajouter le repository HashiCorp
    curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
    sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
    
    # Installer Vault
    sudo apt-get update
    sudo apt-get install -y vault
    
    echo "✅ Vault installé avec succès"
fi

# Créer le répertoire de configuration
sudo mkdir -p /etc/vault.d
sudo mkdir -p /opt/vault/data

# Créer le fichier de configuration Vault
sudo tee /etc/vault.d/vault.hcl > /dev/null <<EOF
# Configuration Vault pour Asmblr
ui = true

# Stockage local pour le développement
storage "file" {
  path = "/opt/vault/data"
}

# Configuration réseau
listener "tcp" {
  address = "0.0.0.0:8200"
  tls_disable = 1
}

# Configuration API
api_addr = "http://127.0.0.1:8200"
cluster_addr = "http://127.0.0.1:8201"

# Configuration du log
log_level = "INFO"
log_file = "/var/log/vault.log"

# Activer le mTLS pour la production
# disable_mlock = true
EOF

# Créer le service systemd
sudo tee /etc/systemd/system/vault.service > /dev/null <<EOF
[Unit]
Description=Vault
Documentation=https://www.vaultproject.io/docs/
After=network.target

[Service]
ExecStart=/usr/bin/vault server -config=/etc/vault.d/vault.hcl
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=process
KillSignal=SIGINT
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
StartLimitInterval=60
StartLimitBurst=3
LimitNOFILE=65536
LimitMEMLOCK=infinity

[Install]
WantedBy=multi-user.target
EOF

# Configurer les permissions
sudo useradd --system --home /etc/vault.d --shell /bin/false vault || true
sudo chown -R vault:vault /etc/vault.d /opt/vault/data
sudo chmod -R 750 /etc/vault.d /opt/vault/data

# Démarrer et activer le service
sudo systemctl daemon-reload
sudo systemctl enable vault
sudo systemctl start vault

# Attendre que Vault démarre
echo "⏳ Attente du démarrage de Vault..."
sleep 5

# Vérifier le statut
if sudo systemctl is-active --quiet vault; then
    echo "✅ Vault est en cours d'exécution"
else
    echo "❌ Vault n'a pas pu démarrer"
    sudo systemctl status vault
    exit 1
fi

# Initialiser Vault
echo "🔑 Initialisation de Vault..."
export VAULT_ADDR=http://127.0.0.1:8200

# Vérifier si Vault est déjà initialisé
if vault operator init -status > /dev/null 2>&1; then
    echo "✅ Vault est déjà initialisé"
else
    echo "🔐 Initialisation de Vault..."
    vault operator init -key-shares=5 -key-threshold=3 > /tmp/vault-init.txt
    
    echo "⚠️  Clés de récupération sauvegardées dans /tmp/vault-init.txt"
    echo "📋 Conservez ces clés en sécurité!"
    
    # Extraire les clés
    ROOT_TOKEN=$(grep "Initial Root Token:" /tmp/vault-init.txt | awk '{print $4}')
    UNSEAL_KEYS=$(grep "Unseal Key" /tmp/vault-init.txt | awk '{print $4}' | head -3)
    
    echo "🔓 Unsealing Vault..."
    for key in $UNSEAL_KEYS; do
        vault operator unseal $key
    done
    
    # Configurer le token root
    vault login $ROOT_TOKEN
    
    echo "✅ Vault initialisé et unsealed"
fi

# Activer les secrets engines
echo "🔧 Configuration des secrets engines..."

# Activer KV store
vault secrets enable -path=asmblr kv

# Activer Transit pour le chiffrement
vault secrets enable transit

# Activer AWS (optionnel)
vault secrets enable aws

# Créer les politiques
vault policy write asmblr-admin - <<EOF
# Politique d'administrateur pour Asmblr
path "asmblr/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

path "sys/leases/renew" {
  capabilities = ["update"]
}

path "sys/leases/revoke" {
  capabilities = ["update"]
}

path "sys/renew" {
  capabilities = ["update"]
}
EOF

vault policy write asmblr-app - <<EOF
# Politique pour les applications Asmblr
path "asmblr/data/*" {
  capabilities = ["read", "update"]
}

path "asmblr/metadata/*" {
  capabilities = ["read", "list"]
}

path "transit/encrypt/asmblr" {
  capabilities = ["update"]
}

path "transit/decrypt/asmblr" {
  capabilities = ["update"]
}
EOF

# Créer les rôles et tokens
vault auth enable userpass
vault write auth/userpass/users/asmblr-admin password=$(openssl rand -base64 32) policies=asmblr-admin
vault write auth/userpass/users/asmblr-app password=$(openssl rand -base64 32) policies=asmblr-app

# Stocker les secrets initiaux
echo "📝 Stockage des secrets initiaux..."

# Secrets de base de données
vault kv put asmblr/database \
    username=asmblr \
    password=$(openssl rand -base64 32) \
    host=localhost \
    port=5432

# Secrets API
vault kv put asmblr/api \
    secret_key=$(openssl rand -base64 64) \
    jwt_secret=$(openssl rand -base64 32)

# Secrets Docker
vault kv put asmblr/docker \
    registry_username=asmblr \
    registry_password=$(openssl rand -base64 32)

# Secrets monitoring
vault kv put asmblr/monitoring \
    grafana_password=$(openssl rand -base64 16)

# Configuration de l'auto-unseal (optionnel, pour la production)
echo "🔧 Configuration de l'auto-unseal..."
cat > /tmp/vault-auto-unseal.hcl <<EOF
# Configuration auto-unseal avec AWS KMS
seal "awskms" {
  region     = "us-east-1"
  kms_key_id = "alias/vault-key"
}

# Alternative: Configuration auto-unseal avec Azure Key Vault
# seal "azurekeyvault" {
#   tenant_id = "..."
#   client_id = "..."
#   client_secret = "..."
#   vault_name = "vault-kms"
# }
EOF

# Créer le script de récupération des secrets pour les applications
cat > /usr/local/bin/vault-get-secret.sh <<'EOF'
#!/bin/bash

# Script pour récupérer les secrets depuis Vault
# Usage: vault-get-secret.sh <path> <key>

set -e

VAULT_ADDR=${VAULT_ADDR:-"http://127.0.0.1:8200"}
VAULT_TOKEN=${VAULT_TOKEN:-""}

if [ -z "$VAULT_TOKEN" ]; then
    echo "❌ VAULT_TOKEN n'est pas défini"
    exit 1
fi

if [ $# -ne 2 ]; then
    echo "Usage: $0 <path> <key>"
    echo "Example: $0 asmblr/database password"
    exit 1
fi

PATH=$1
KEY=$2

# Récupérer le secret
SECRET=$(vault kv get -field=$KEY $PATH 2>/dev/null)

if [ $? -eq 0 ]; then
    echo $SECRET
else
    echo "❌ Impossible de récupérer le secret: $PATH/$KEY"
    exit 1
fi
EOF

chmod +x /usr/local/bin/vault-get-secret.sh

# Créer le script de configuration des applications
cat > /usr/local/bin/vault-configure-app.sh <<'EOF'
#!/bin/bash

# Script pour configurer les variables d'environnement depuis Vault
# Usage: vault-configure-app.sh <app-name>

set -e

VAULT_ADDR=${VAULT_ADDR:-"http://127.0.0.1:8200"}
VAULT_TOKEN=${VAULT_TOKEN:-""}

if [ -z "$VAULT_TOKEN" ]; then
    echo "❌ VAULT_TOKEN n'est pas défini"
    exit 1
fi

if [ $# -ne 1 ]; then
    echo "Usage: $0 <app-name>"
    echo "Example: $0 asmblr-api"
    exit 1
fi

APP_NAME=$1

# Récupérer et exporter les secrets
echo "🔧 Configuration des secrets pour $APP_NAME..."

# Base de données
DB_PASSWORD=$(vault kv get -field=password asmblr/database)
export DATABASE_PASSWORD=$DB_PASSWORD

# API
SECRET_KEY=$(vault kv get -field=secret_key asmblr/api)
export SECRET_KEY=$SECRET_KEY

# Monitoring
GRAFANA_PASSWORD=$(vault kv get -field=grafana_password asmblr/monitoring)
export GRAFANA_PASSWORD=$GRAFANA_PASSWORD

echo "✅ Secrets configurés pour $APP_NAME"
echo "📋 Variables d'environnement exportées:"
env | grep -E "(DATABASE_PASSWORD|SECRET_KEY|GRAFANA_PASSWORD)"
EOF

chmod +x /usr/local/bin/vault-configure-app.sh

# Créer le fichier d'environnement pour Docker Compose
cat > .env.vault <<EOF
# Configuration Vault pour Docker Compose
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=$(vault print token)

# Configuration des applications
VAULT_ROLE=asmblr-app
VAULT_AUTH_METHOD=userpass
VAULT_USERNAME=asmblr-app
EOF

echo "✅ Configuration Vault terminée!"
echo ""
echo "📋 Informations importantes:"
echo "  - URL Vault: http://127.0.0.1:8200"
echo "  - UI Vault: http://127.0.0.1:8200/ui"
echo "  - Fichier d'initialisation: /tmp/vault-init.txt"
echo "  - Script de récupération: vault-get-secret.sh"
echo "  - Script de configuration: vault-configure-app.sh"
echo ""
echo "⚠️  Actions requises:"
echo "  1. Sauvegardez les clés de récupération dans /tmp/vault-init.txt"
echo "  2. Configurez les tokens dans vos applications"
echo "  3. Activez l'auto-unseal pour la production"
echo ""
echo "🔗 Documentation: https://www.vaultproject.io/docs/"
