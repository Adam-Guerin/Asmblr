# 📚 Asmblr - Guide Utilisateur Complet

## Table des Matières

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Interface Utilisateur](#interface-utilisateur)
5. [Génération de MVP](#génération-de-mvp)
6. [Monitoring et Alertes](#monitoring-et-alertes)
7. [Exports et Rapports](#exports-et-rapports)
8. [Dépannage](#dépannage)
9. [Bonnes Pratiques](#bonnes-pratiques)

---

## 🚀 Introduction

Asmblr est un générateur de MVP (Minimum Viable Product) alimenté par l'IA qui utilise des agents multi-agents pour analyser des idées, générer des spécifications et créer des prototypes fonctionnels.

### Fonctionnalités Principales

- **🤖 Agents IA Multi-agents** : Recherche, analyse, génération de produits
- **📊 Analyse de Marché** : Scraping intelligent et identification de pain points
- **🎯 Génération d'Idées** : Création et évaluation d'idées innovantes
- **📋 Spécifications Techniques** : PRD et tech specs automatiques
- **🏗️ Prototypage Rapide** : Génération de code MVP avec Next.js
- **📈 Monitoring en Temps Réel** : Suivi des métriques et alertes
- **🎨 Interface Personnalisable** : Thèmes multiples et responsive design

---

## 🛠️ Installation

### Prérequis

- Python 3.11 ou supérieur
- Ollama (pour les modèles LLM locaux)
- Git (pour le versioning des MVPs)

### Installation Automatisée

```bash
# Cloner le repository
git clone https://github.com/votre-org/asmblr.git
cd asmblr

# Exécuter le script d'installation
python setup.py

# Démarrer l'interface
streamlit run app/ui.py
```

### Installation Manuelle

```bash
# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\\Scripts\\activate  # Windows

# Installer les dépendances
pip install -r requirements_updated.txt

# Configurer Ollama
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b

# Démarrer Ollama
ollama serve

# Lancer l'application
streamlit run app/ui.py
```

---

## ⚙️ Configuration

### Variables d'Environnement

Créez un fichier `.env` à la racine du projet :

```bash
# Configuration Ollama
OLLAMA_BASE_URL=http://localhost:11434
GENERAL_MODEL=llama3.1:8b
CODE_MODEL=qwen2.5-coder:7b

# Configuration Pipeline
MAX_SOURCES=8
MIN_PAGES=3
MIN_PAINS=5
MARKET_SIGNAL_THRESHOLD=40
SIGNAL_QUALITY_THRESHOLD=45

# ICP (Ideal Customer Profile)
PRIMARY_ICP="Founders B2B SaaS pre-seed"
PRIMARY_ICP_KEYWORDS="founder,founders,b2b,saas,pre-seed,startup"
ICP_ALIGNMENT_BONUS_MAX=8

# Monitoring et Alertes
ALERT_EMAIL_ENABLED=false
ALERT_SMTP_SERVER=smtp.gmail.com
ALERT_SMTP_PORT=587
ALERT_EMAIL_USERNAME=votre-email@gmail.com
ALERT_EMAIL_PASSWORD=votre-mot-de-passe
ALERT_EMAIL_FROM=votre-email@gmail.com
ALERT_EMAIL_TO=alerte@votre-entreprise.com

# Slack (optionnel)
ALERT_SLACK_ENABLED=false
ALERT_SLACK_WEBHOOK_URL=votre-webhook-url
ALERT_SLACK_CHANNEL=#alerts

# Discord (optionnel)
ALERT_DISCORD_ENABLED=false
ALERT_DISCORD_WEBHOOK_URL=votre-webhook-url
```

### Configuration des Sources

Éditez `configs/sources.yaml` pour configurer les sources de scraping :

```yaml
sources:
  - name: "Product Hunt"
    url: "https://www.producthunt.com"
    type: "product_discovery"
    enabled: true
  
  - name: "Hacker News"
    url: "https://news.ycombinator.com"
    type: "tech_news"
    enabled: true
  
  - name: "Reddit"
    url: "https://www.reddit.com/r/startups"
    type: "community"
    enabled: true
```

---

## 🖥️ Interface Utilisateur

### Vue d'Ensemble

L'interface Asmblr est composée de trois onglets principaux :

1. **🎯 Generate MVP** : Génération de MVP
2. **📊 Dashboard** : Monitoring et métriques
3. **📤 Exports** : Export des résultats

### Personnalisation

#### Thèmes

Choisissez parmi 4 thèmes disponibles dans la sidebar :

- **☀️ Clair** : Thème par défaut, lumineux et professionnel
- **🌙 Sombre** : Thème sombre pour réduire la fatigue oculaire
- **💙 Bleu** : Variant bleue pour une ambiance corporate
- **💚 Vert** : Variant verte pour une touche de fraîcheur

#### Configuration du Pipeline

- **Topic/Domain** : Sujet à analyser (ex: "productivity tools for remote teams")
- **Number of Ideas** : Nombre d'idées à générer (3-15)
- **Execution Mode** :
  - **Standard** : Analyse complète et détaillée
  - **Fast** : Génération rapide avec moins de détails
  - **Validation Sprint 7 jours** : Optimisé pour validation rapide

#### Données Avancées (Seed Data)

Dans la section "Advanced Seed Inputs", vous pouvez fournir :

- **Ideal Customer Profile** : Description de votre cible
- **Context** : Informations supplémentaires sur le marché
- **Pain Points** : Listes de problèmes à résoudre
- **Competitors** : Liste de concurrents directs

---

## 🚀 Génération de MVP

### Étape 1 : Configuration

1. **Définir le Topic** : Soyez spécifique mais concis
   - ✅ Bon : "AI-powered compliance automation for fintech"
   - ❌ Mauvais : "AI stuff"

2. **Choisir le Mode d'Exécution** :
   - **Fast** : Pour tester rapidement une idée
   - **Standard** : Pour une analyse complète
   - **Validation Sprint** : Pour un MVP en 7 jours

3. **Paramétrer les Idées** : 3-15 idées selon vos besoins

### Étape 2 : Surveillance de la Progression

Pendant l'exécution, suivez en temps réel :

- **🔄 Initialisation** : Démarrage du pipeline
- **🔍 Scraping** : Collecte des données de marché
- **📊 Analyse** : Traitement des informations
- **💡 Génération** : Création des idées
- **🎯 Évaluation** : Scoring des idées
- **📋 PRD** : Génération des spécifications
- **🛠️ Tech Spec** : Spécifications techniques
- **🏗️ MVP** : Construction du prototype
- **📝 Contenu** : Génération du contenu marketing

### Étape 3 : Analyse des Résultats

#### Résumé

- **💡 Idées Générées** : Nombre et score moyen
- **🏆 Meilleur Score** : L'idée la plus prometteuse
- **⏱️ Temps d'Exécution** : Durée totale du pipeline

#### Visualisations

- **📊 Graphique des Scores** : Comparaison visuelle des idées
- **🎯 Jauge de Confiance** : Score de confiance global
- **📈 Signaux de Marché** : Forces des signaux collectés

#### Détails Techniques

- **Product Requirements Document** : Spécifications complètes
- **Technical Specifications** : Architecture et stack technique
- **Repository** : Lien vers le code généré

---

## 📊 Monitoring et Alertes

### Tableau de Bord Qualité

Le dashboard affiche en temps réel :

#### Métriques Globales
- **🚀 Total Runs** : Nombre total d'exécutions
- **✅ Taux de Succès** : Pourcentage de pipelines réussis
- **⚡ Temps Moyen** : Durée moyenne d'exécution
- **🎯 Score Confiance** : Score de confiance moyen

#### Exécutions Récentes
- **Run ID** : Identifiant unique
- **Topic** : Sujet analysé
- **Status** : ✅ Completed / ❌ Failed
- **Confidence** : Score de confiance
- **Time** : Durée d'exécution

### Système d'Alertes

#### Types d'Alertes

1. **🔧 Système**
   - CPU > 80%
   - Mémoire > 85%
   - Disque > 90%

2. **📊 Pipeline**
   - Taux d'échec > 10%
   - Temps d'exécution > 5 minutes
   - Échec de génération

3. **🎯 Qualité**
   - Score de confiance < 50%
   - Peu de signaux de marché
   - Idées de faible qualité

#### Configuration des Alertes

Les alertes peuvent être envoyées via :

- **📧 Email** : Notifications SMTP détaillées
- **🔗 Webhook** : Appels HTTP personnalisés
- **💬 Slack** : Messages dans un canal dédié
- **🎮 Discord** : Notifications sur serveur Discord
- **🖥️ Console** : Affichage en temps réel

### Métriques Détaillées

#### Métriques de Pipeline
- **Temps par étape** : Durée de chaque phase
- **Taux de conversion** : Idées → MVP
- **Qualité des outputs** : Scores et évaluations

#### Métriques Système
- **Utilisation CPU** : Pourcentage d'utilisation
- **Mémoire** : RAM utilisée vs disponible
- **Disque** : Espace de stockage
- **Réseau** : Traffic et latence

---

## 📤 Exports et Rapports

### Formats Disponibles

#### 📄 JSON
- **Contenu** : Données brutes complètes
- **Usage** : Intégration API, traitement automatisé
- **Structure** : Hiérarchique avec métadonnées

#### 📊 CSV
- **Contenu** : Données tabulaires (idées, scores)
- **Usage** : Analyse dans Excel/Google Sheets
- **Structure** : Tableau plat avec colonnes standardisées

#### 📝 Markdown
- **Contenu** : Rapport lisible par humains
- **Usage** : Documentation, partage
- **Structure** : Formaté avec titres et listes

#### 📋 PDF
- **Contenu** : Rapport professionnel
- **Usage** : Présentations, archives
- **Structure** : Mise en page formattée

#### 📦 ZIP (Complet)
- **Contenu** : Tous les formats + artefacts
- **Usage** : Archive complète, sauvegarde
- **Structure** : Dossiers organisés par type

### Export Automatisé

#### Configuration

```python
# Exemple d'export programmatique
from app.ui.export_manager import get_export_manager

export_manager = get_export_manager()
results = {...}  # Vos résultats
run_id = "20240207_120000"

# Exporter en JSON
json_data = export_manager.export_results(results, "json", run_id)

# Exporter en ZIP
zip_data = export_manager.export_results(results, "zip", run_id)
```

#### Intégration CI/CD

```yaml
# GitHub Actions example
- name: Export Results
  run: |
    python -c "
    from app.ui.export_manager import get_export_manager
    export_manager = get_export_manager()
    # Export logic here
    "
```

---

## 🔧 Dépannage

### Problèmes Courants

#### ❌ Ollama Non Disponible

**Symptôme** : "Ollama not reachable"

**Solutions** :
1. Vérifiez qu'Ollama est installé : `ollama --version`
2. Démarrez le service : `ollama serve`
3. Vérifiez les modèles : `ollama list`
4. Téléchargez les modèles manquants :
   ```bash
   ollama pull llama3.1:8b
   ollama pull qwen2.5-coder:7b
   ```

#### ⏱️ Pipeline Lent

**Symptôme** : Temps d'exécution > 30 minutes

**Solutions** :
1. Passez en mode Fast
2. Réduisez le nombre d'idées
3. Limitez les sources de scraping
4. Vérifiez votre connexion internet

#### 📊 Scores Faibles

**Symptôme** : Scores d'idées < 50

**Solutions** :
1. Affinez votre topic
2. Ajoutez des seed data pertinentes
3. Vérifiez la qualité des sources
4. Utilisez un ICP spécifique

#### 🚨 Alertes Non Reçues

**Symptôme** : Pas de notifications d'alertes

**Solutions** :
1. Vérifiez la configuration `.env`
2. Testez les notifications : `python -m app test-alerts`
3. Vérifiez les logs d'erreurs
4. Confirmez les credentials (email, webhook)

### Logs et Debugging

#### Activer les Logs Détaillés

```bash
# Logs JSON structurés
export LOG_JSON=true

# Niveau de log détaillé
export LOG_LEVEL=DEBUG

# Redémarrer l'application
streamlit run app/ui.py
```

#### Emplacement des Logs

- **Application** : `data/audit.log`
- **Pipeline** : `runs/<run_id>/progress.log`
- **Erreurs** : `runs/<run_id>/error.log`
- **Métriques** : `data/metrics.log`

#### Commandes de Diagnostic

```bash
# Vérifier l'environnement
python -m app doctor

# Tester les composants
python -m app test-ollama
python -m app test-scraping
python -m app test-alerts

# Nettoyer les caches
python -m app cleanup --cache
```

---

## 💡 Bonnes Pratiques

### Optimisation des Résultats

#### 1. Topics Efficaces

✅ **Bons exemples** :
- "AI-powered expense tracking for freelancers"
- "Automated compliance checking for healthcare"
- "Smart scheduling tool for distributed teams"

❌ **Mauvais exemples** :
- "AI startup"
- "Something with blockchain"
- "Revolutionary app"

#### 2. Seed Data Qualité

**ICP (Ideal Customer Profile)** :
```
Freelance developers aged 25-40, working remotely,
earning $50k-$150k annually, struggling with
time tracking and invoicing
```

**Pain Points** :
```
- Manual time tracking is tedious
- Invoicing takes too much time
- Difficult to track project profitability
- Currency conversion headaches
```

#### 3. Configuration Optimale

**Pour le Proof of Concept** :
- Mode : Fast
- Idées : 3-5
- Sources : 3-5

**Pour l'Analyse Complète** :
- Mode : Standard
- Idées : 8-12
- Sources : 8-10

**Pour la Production** :
- Mode : Validation Sprint
- Idées : 10-15
- Sources : 10-12

### Monitoring Proactif

#### Alertes Essentielles

Configurez au minimum :
- **Email** : Pour les alertes critiques
- **Console** : Pour le debugging en temps réel
- **Webhook** : Pour l'intégration avec vos outils

#### KPIs à Surveiller

- **Taux de succès** : > 80%
- **Temps moyen** : < 15 minutes (mode standard)
- **Score de confiance** : > 70%
- **Taux d'alertes** : < 5% par jour

### Sécurité et Conformité

#### Données Sensibles

- **Jamais** de credentials dans le code
- **Toujours** utiliser les variables d'environnement
- **Réduire** l'accès aux données personnelles
- **Auditer** régulièrement les logs

#### Performance

- **Monitorer** l'utilisation CPU/mémoire
- **Limiter** les exécutions parallèles
- **Nettoyer** les anciens runs
- **Optimiser** les tailles de cache

---

## 📞 Support et Communauté

### Obtenir de l'Aide

1. **Documentation** : Consultez ce guide d'abord
2. **Logs** : Analysez les logs d'erreurs
3. **Diagnostics** : Utilisez `python -m app doctor`
4. **Community** : Rejoignez notre Discord/Slack
5. **Issues** : Signalez les problèmes sur GitHub

### Contribuer

Nous welcome les contributions ! Voir `CONTRIBUTING.md` pour :
- Report de bugs
- Demandes de fonctionnalités
- Pull requests
- Documentation

---

*Ce guide est maintenu par l'équipe Asmblr. Dernière mise à jour : Février 2024*
