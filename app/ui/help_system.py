"""Contextual help system for Asmblr UI."""

from __future__ import annotations
import streamlit as st
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class HelpCategory(Enum):
    """Help content categories."""
    GETTING_STARTED = "getting_started"
    PIPELINE = "pipeline"
    CONFIGURATION = "configuration"
    MONITORING = "monitoring"
    EXPORTS = "exports"
    TROUBLESHOOTING = "troubleshooting"


@dataclass
class HelpContent:
    """Help content structure."""
    title: str
    content: str
    category: HelpCategory
    related_topics: List[str]
    tips: List[str]
    video_url: Optional[str] = None
    external_links: List[str] = None
    
    def __post_init__(self):
        if self.external_links is None:
            self.external_links = []


class HelpSystem:
    """Manages contextual help content and display."""
    
    def __init__(self):
        self.help_contents = self._initialize_help_contents()
        self.current_context = None
    
    def _initialize_help_contents(self) -> Dict[str, HelpContent]:
        """Initialize all help content."""
        return {
            # Getting Started
            "welcome": HelpContent(
                title="🚀 Bienvenue dans Asmblr",
                category=HelpCategory.GETTING_STARTED,
                content=(
                    "Asmblr est un générateur de MVP (Minimum Viable Product) alimenté par l'IA "
                    "qui analyse des idées de marché et génère des prototypes fonctionnels.\n\n"
                    "**Points clés :**\n"
                    "- Analyse automatisée du marché\n"
                    "- Génération d'idées avec IA\n"
                    "- Création de MVP techniques\n"
                    "- Monitoring en temps réel\n\n"
                    "**Pour commencer :**\n"
                    "1. Configurez votre topic dans la sidebar\n"
                    "2. Choisissez le mode d'exécution\n"
                    "3. Cliquez sur 'Start Generation'"
                ),
                related_topics=["first_run", "ollama_setup", "topic_selection"],
                tips=[
                    "Commencez avec le mode Fast pour vos premiers tests",
                    "Soyez spécifique dans votre description de topic",
                    "Utilisez les seed data pour de meilleurs résultats"
                ]
            ),
            
            "first_run": HelpContent(
                title="🎯 Première Exécution",
                category=HelpCategory.GETTING_STARTED,
                content="""
                **Étapes pour votre premier MVP :**
                
                1. **Vérifier Ollama** : Assurez-vous qu'Ollama est en cours d'exécution
                2. **Définir le Topic** : Soyez spécifique mais concis
                3. **Choisir le Mode** : Fast pour commencer, Standard pour plus de détails
                4. **Lancer** : Cliquez sur "Start Generation"
                5. **Surveiller** : Suivez la progression en temps réel
                
                **Exemple de topic efficace :**
                "AI-powered expense tracking for freelancers"
                """,
                related_topics=["topic_selection", "execution_modes", "progress_tracking"],
                tips=[
                    "Un topic spécifique donne de meilleurs résultats",
                    "Le mode Fast est idéal pour les premiers tests",
                    "La progression s'affiche en temps réel"
                ]
            ),
            
            "ollama_setup": HelpContent(
                title="🤖 Configuration d'Ollama",
                category=HelpCategory.CONFIGURATION,
                content="""
                **Ollama est requis pour faire fonctionner Asmblr.**
                
                **Installation :**
                ```bash
                # Télécharger depuis https://ollama.ai/download
                # Installer selon votre OS
                
                # Démarrer le service
                ollama serve
                
                # Télécharger les modèles requis
                ollama pull llama3.1:8b
                ollama pull qwen2.5-coder:7b
                ```
                
                **Vérification :**
                ```bash
                ollama list  # Vérifier les modèles installés
                ollama --version  # Vérifier la version
                ```
                
                **Dépannage :**
                - Si "connection refused" : Vérifiez qu'Ollama est démarré
                - Si "model not found" : Téléchargez les modèles manquants
                - Port par défaut : 11434
                """,
                related_topics=["first_run", "troubleshooting_connection"],
                tips=[
                    "Gardez Ollama en cours d'exécution pendant l'utilisation",
                    "Les modèles prennent de la place : prévoyez 10GB minimum",
                    "Redémarrez Ollama si vous rencontrez des erreurs"
                ]
            ),
            
            # Pipeline
            "topic_selection": HelpContent(
                title="📝 Sélection de Topic",
                category=HelpCategory.PIPELINE,
                content=(
                    "**Un bon topic est la clé du succès.**\n\n"
                    "**✅ Bons exemples :**\n"
                    "- 'AI-powered compliance automation for healthcare'\n"
                    "- 'Smart scheduling tool for distributed teams'\n"
                    "- 'Automated expense tracking for freelancers'\n\n"
                    "**❌ Mauvais exemples :**\n"
                    "- 'AI startup'\n"
                    "- 'Something revolutionary'\n"
                    "- 'App for everyone'\n\n"
                    "**Conseils :**\n"
                    "- Soyez spécifique sur le domaine cible\n"
                    "- Mentionnez la technologie principale si pertinente\n"
                    "- Décrivez le problème à résoudre\n"
                    "- Ciblez un segment de marché clair"
                ),
                related_topics=["first_run", "seed_data", "execution_modes"],
                tips=[
                    "Plus le topic est spécifique, meilleurs sont les résultats",
                    "Pensez 'problème-solution' plutôt que 'technologie'",
                    "Considérez votre expérience personnelle ou professionnelle"
                ]
            ),
            
            "execution_modes": HelpContent(
                title="⚡ Modes d'Exécution",
                category=HelpCategory.PIPELINE,
                content="""
                Asmblr offre trois modes d'exécution adaptés à différents besoins.
                
                **🏃 Fast Mode**
                - **Durée** : 5-10 minutes
                - **Idées** : 3 maximum
                - **Sources** : 3-5 sources
                - **Usage** : Tests rapides, validation d'idée
                
                **🚶 Standard Mode**
                - **Durée** : 20-40 minutes
                - **Idées** : 5-10 idées
                - **Sources** : 8-10 sources
                - **Usage** : Analyse complète, MVP détaillé
                
                **🏃‍♂️ Validation Sprint**
                - **Durée** : 15-25 minutes
                - **Focus** : Validation 7 jours
                - **Sortie** : Plan d'action priorisé
                - **Usage** : Validation rapide de marché
                
                **Recommandation :**
                Commencez avec Fast Mode, puis passez à Standard pour les projets prometteurs.
                """,
                related_topics=["topic_selection", "progress_tracking", "pipeline_stages"],
                tips=[
                    "Fast Mode est parfait pour itérer rapidement",
                    "Standard Mode donne les résultats les plus complets",
                    "Validation Sprint est idéal pour les entrepreneurs"
                ]
            ),
            
            "seed_data": HelpContent(
                title="🌱 Données Avancées (Seed Data)",
                category=HelpCategory.CONFIGURATION,
                content="""
                Les seed data aident Asmblr à mieux comprendre votre contexte.
                
                **ICP (Ideal Customer Profile) :**
                Décrivez votre client cible :
                ```
                Freelance developers aged 25-40, 
                working remotely, earning $50k-$150k annually,
                struggling with time tracking and invoicing
                ```
                
                **Pain Points :**
                Listez les problèmes spécifiques :
                ```
                Manual time tracking is tedious
                Invoicing takes too much time
                Difficult to track project profitability
                Currency conversion headaches
                ```
                
                **Competitors :**
                Mentionnez vos concurrents directs :
                ```
                Harvest
                Toggl
                FreshBooks
                ```
                
                **Impact :**
                Les seed data peuvent améliorer les résultats de 30-50% !
                """,
                related_topics=["topic_selection", "execution_modes"],
                tips=[
                    "Soyez spécifique dans votre ICP",
                    "Listez les pain points réels, pas supposés",
                    "Inclure les concurrents connus du marché"
                ]
            ),
            
            "progress_tracking": HelpContent(
                title="📊 Suivi de Progression",
                category=HelpCategory.PIPELINE,
                content="""
                Suivez votre pipeline en temps réel avec notre système de progression.
                
                **Étapes du Pipeline :**
                1. **🔄 Initialisation** : Préparation du pipeline
                2. **🔍 Scraping** : Collecte des données de marché
                3. **📊 Analyse** : Traitement des informations
                4. **💡 Génération** : Création des idées
                5. **🎯 Évaluation** : Scoring des idées
                6. **📋 PRD** : Spécifications produit
                7. **🛠️ Tech Spec** : Architecture technique
                8. **🏗️ MVP** : Construction du prototype
                9. **📝 Contenu** : Génération marketing
                10. **✅ Finalisation** : Compilation des résultats
                
                **Indicateurs :**
                - **Barre de progression** : Avancement global (0-100%)
                - **Étape actuelle** : Phase en cours
                - **Messages détaillés** : Informations contextuelles
                - **Durée estimée** : Temps restant approximatif
                
                **En cas d'erreur :**
                Le système affiche automatiquement des solutions adaptées.
                """,
                related_topics=["execution_modes", "troubleshooting_pipeline"],
                tips=[
                    "La progression est mise à jour en temps réel",
                    "Chaque étape a une durée variable",
                    "Les erreurs sont gérées automatiquement"
                ]
            ),
            
            # Monitoring
            "dashboard_overview": HelpContent(
                title="📈 Tableau de Bord",
                category=HelpCategory.MONITORING,
                content="""
                Le dashboard vous donne une vue d'ensemble de l'activité Asmblr.
                
                **Métriques Principales :**
                - **🚀 Total Runs** : Nombre d'exécutions totales
                - **✅ Taux de Succès** : Pourcentage de pipelines réussis
                - **⚡ Temps Moyen** : Durée moyenne d'exécution
                - **🎯 Score Confiance** : Qualité moyenne des résultats
                
                **Graphiques :**
                - **Scores des Idées** : Distribution des scores générés
                - **Jauge de Confiance** : Score de confiance global
                - **Signaux de Marché** : Force des signaux collectés
                
                **Historique :**
                - **Exécutions Récentes** : Derniers runs avec statuts
                - **Tendances** : Évolution des métriques dans le temps
                
                **Utilisation :**
                - Surveillez la performance globale
                - Identifiez les patterns de succès/échec
                - Optimisez vos paramètres
                """,
                related_topics=["metrics_explanation", "alerts_setup"],
                tips=[
                    "Actualisez le dashboard pour les dernières données",
                    "Utilisez les filtres pour analyser des périodes spécifiques",
                    "Les métriques sont mises à jour en temps réel"
                ]
            ),
            
            "metrics_explanation": HelpContent(
                title="📊 Comprendre les Métriques",
                category=HelpCategory.MONITORING,
                content="""
                **Métriques de Pipeline :**
                
                **Taux de Succès**
                - Calcul : (Pipelines réussis / Total) × 100
                - Cible : > 80%
                - Impact : Fiabilité du système
                
                **Temps Moyen**
                - Calcul : Somme des durées / Nombre d'exécutions
                - Cible : < 15 minutes (mode standard)
                - Impact : Efficacité et coût
                
                **Score de Confiance**
                - Calcul : Moyenne des scores de confiance
                - Cible : > 70%
                - Impact : Qualité des résultats
                
                **Métriques Système :**
                
                **CPU/Mémoire**
                - Monitoring des ressources système
                - Alertes automatiques si > 80%
                - Impact : Performance et stabilité
                
                **Taux d'Alertes**
                - Calcul : (Alertes / Heure)
                - Cible : < 5 par heure
                - Impact : Santé système
                
                **Interprétation :**
                - 🟢 Vert : Performance optimale
                - 🟡 Jaune : Attention requise
                - 🔴 Rouge : Action immédiate nécessaire
                """,
                related_topics=["dashboard_overview", "alerts_setup"],
                tips=[
                    "Surveillez les tendances plutôt que les valeurs isolées",
                    "Comparez les métriques avant/après changements",
                    "Utilisez les alertes pour une surveillance proactive"
                ]
            ),
            
            "alerts_setup": HelpContent(
                title="🚨 Configuration des Alertes",
                category=HelpCategory.MONITORING,
                content="""
                Configurez des alertes pour être notifié des problèmes importants.
                
                **Types d'Alertes :**
                
                **🔧 Système**
                - CPU > 80%
                - Mémoire > 85%
                - Disque > 90%
                
                **📊 Pipeline**
                - Taux d'échec > 10%
                - Temps d'exécution > 5 minutes
                - Échec de génération
                
                **🎯 Qualité**
                - Score de confiance < 50%
                - Peu de signaux de marché
                - Idées de faible qualité
                
                **Canaux de Notification :**
                
                **📧 Email**
                - Configuration SMTP requise
                - Rapports détaillés HTML
                - Idéal pour archives
                
                **💬 Slack**
                - Webhook URL requis
                - Messages formatés
                - Idéal pour équipes
                
                **🎮 Discord**
                - Webhook URL requis
                - Embeds riches
                - Idéal pour communautés
                
                **🔗 Webhook**
                - Endpoint HTTP personnalisé
                - Format JSON
                - Idéal pour intégrations
                
                **Configuration :**
                1. Éditez `.env` avec vos credentials
                2. Activez les canaux souhaités
                3. Testez avec `python -m app test-alerts`
                """,
                related_topics=["dashboard_overview", "metrics_explanation"],
                tips=[
                    "Commencez avec les alertes email pour tester",
                    "Configurez les seuils selon vos besoins",
                    "Testez régulièrement vos configurations"
                ]
            ),
            
            # Exports
            "export_formats": HelpContent(
                title="📤 Formats d'Export",
                category=HelpCategory.EXPORTS,
                content="""
                Asmblr supporte plusieurs formats d'export pour différents usages.
                
                **📄 JSON**
                - **Contenu** : Données brutes complètes
                - **Structure** : Hiérarchique avec métadonnées
                - **Usage** : Intégration API, traitement automatisé
                - **Taille** : 1-5 MB
                
                **📊 CSV**
                - **Contenu** : Données tabulaires (idées, scores)
                - **Structure** : Tableau plat avec colonnes
                - **Usage** : Analyse Excel/Google Sheets
                - **Taille** : 50-200 KB
                
                **📝 Markdown**
                - **Contenu** : Rapport lisible par humains
                - **Structure** : Formaté avec titres et listes
                - **Usage** : Documentation, partage
                - **Taille** : 100-500 KB
                
                **📋 PDF**
                - **Contenu** : Rapport professionnel
                - **Structure** : Mise en page formattée
                - **Usage** : Présentations, archives
                - **Taille** : 200-800 KB
                
                **📦 ZIP (Complet)**
                - **Contenu** : Tous les formats + artefacts
                - **Structure** : Dossiers organisés par type
                - **Usage** : Archive complète, sauvegarde
                - **Taille** : 2-10 MB
                
                **Recommandation :**
                - JSON pour développeurs
                - CSV pour analystes
                - Markdown pour documentation
                - ZIP pour archive complète
                """,
                related_topics=["export_automation", "data_analysis"],
                tips=[
                    "Le ZIP contient tous les autres formats",
                    "JSON préserve toutes les métadonnées",
                    "CSV est idéal pour les graphiques Excel"
                ]
            ),
            
            "export_automation": HelpContent(
                title="🤖 Automatisation des Exports",
                category=HelpCategory.EXPORTS,
                content="""
                Automatisez vos exports avec l'API ou les scripts.
                
                **API Endpoint :**
                ```http
                POST /api/v1/export
                Content-Type: application/json
                
                {
                    "run_id": "20240207_120000",
                    "formats": ["json", "csv"],
                    "webhook_url": "https://votre-app.com/webhook"
                }
                ```
                
                **Script Python :**
                ```python
                from app.ui.export_manager import get_export_manager
                
                export_manager = get_export_manager()
                
                # Exporter en JSON
                json_data = export_manager.export_results(
                    results, "json", run_id
                )
                
                # Exporter en ZIP
                zip_data = export_manager.export_results(
                    results, "zip", run_id
                )
                
                # Sauvegarder
                with open("results.zip", "wb") as f:
                    f.write(zip_data)
                ```
                
                **Intégration CI/CD :**
                ```yaml
                # GitHub Actions
                - name: Export Results
                  run: |
                    python scripts/export_results.py
                    aws s3 cp results.zip s3://bucket/
                ```
                
                **Webhook Callback :**
                ```json
                {
                    "run_id": "20240207_120000",
                    "status": "completed",
                    "download_url": "https://asmblr.com/download/xyz",
                    "formats": ["json", "csv", "zip"],
                    "timestamp": "2024-02-07T12:00:00Z"
                }
                ```
                """,
                related_topics=["export_formats", "api_usage"],
                tips=[
                    "Utilisez les webhooks pour une notification asynchrone",
                    "Le ZIP est le plus pratique pour l'archivage",
                    "JSON est le meilleur pour l'intégration système"
                ]
            ),
            
            # Troubleshooting
            "troubleshooting_connection": HelpContent(
                title="🔧 Problèmes de Connexion",
                category=HelpCategory.TROUBLESHOOTING,
                content="""
                **Symptôme : "Ollama not reachable"**
                
                **Causes possibles :**
                1. Ollama n'est pas démarré
                2. Mauvais port/config
                3. Firewall bloque l'accès
                4. Ollama pas installé
                
                **Solutions :**
                
                **1. Vérifier l'installation**
                ```bash
                ollama --version
                # Si erreur : réinstallez Ollama
                ```
                
                **2. Démarrer Ollama**
                ```bash
                # Terminal 1
                ollama serve
                
                # Terminal 2 (vérification)
                curl http://localhost:11434/api/tags
                ```
                
                **3. Vérifier les modèles**
                ```bash
                ollama list
                # Si vide :
                ollama pull llama3.1:8b
                ollama pull qwen2.5-coder:7b
                ```
                
                **4. Configuration**
                ```bash
                # .env
                OLLAMA_BASE_URL=http://localhost:11434
                ```
                
                **5. Firewall**
                - Autoriser le port 11434
                - Désactiver temporairement pour tester
                
                **Vérification finale :**
                ```bash
                python -m app doctor
                ```
                """,
                related_topics=["ollama_setup", "troubleshooting_pipeline"],
                tips=[
                    "Redémarrez Ollama si vous rencontrez des erreurs",
                    "Vérifiez qu'aucun autre processus n'utilise le port 11434",
                    "Utilisez `ollama serve` dans un terminal dédié"
                ]
            ),
            
            "troubleshooting_pipeline": HelpContent(
                title="⚡ Problèmes de Pipeline",
                category=HelpCategory.TROUBLESHOOTING,
                content="""
                **Pipeline lent ou bloqué**
                
                **Causes communes :**
                - Trop de sources à scraper
                - Connexion internet lente
                - Modèles LLM surchargés
                - Ressources système insuffisantes
                
                **Solutions :**
                
                **1. Mode Fast**
                - Passez en mode Fast
                - Réduisez le nombre d'idées
                - Limitez les sources
                
                **2. Ressources**
                ```bash
                # Vérifier l'utilisation
                htop  # CPU/Mémoire
                df -h  # Disque
                
                # Libérer de la mémoire
                sudo systemctl restart ollama
                ```
                
                **3. Configuration**
                ```bash
                # .env
                MAX_SOURCES=5  # Réduire
                MIN_PAGES=2     # Réduire
                ```
                
                **Pipeline échoue**
                
                **Erreurs courantes :**
                - "Insufficient market signals"
                - "No valid ideas generated"
                - "MVP build failed"
                
                **Solutions :**
                
                **1. Market Signals**
                - Affinez votre topic
                - Ajoutez des seed data
                - Essayez différents sources
                
                **2. Ideas Generation**
                - Soyez plus spécifique
                - Vérifiez votre ICP
                - Réduisez la complexité
                
                **3. MVP Build**
                - Vérifiez l'espace disque
                - Redémarrez le pipeline
                - Essayez sans MVP
                
                **Debug avancé :**
                ```bash
                # Logs détaillés
                export LOG_JSON=true
                export LOG_LEVEL=DEBUG
                
                # Monitoring temps réel
                tail -f data/audit.log
                ```
                """,
                related_topics=["progress_tracking", "troubleshooting_connection"],
                tips=[
                    "Le mode Fast résout 80% des problèmes de performance",
                    "Les logs sont votre meilleur ami pour le debugging",
                    "Redémarrez Ollama entre les runs complexes"
                ]
            ),
            
            "data_analysis": HelpContent(
                title="📊 Analyse des Données",
                category=HelpCategory.EXPORTS,
                content="""
                **Analysez vos résultats Asmblr avec des outils externes.**
                
                **Excel/Google Sheets :**
                1. Exportez en CSV
                2. Importez dans votre tableur
                3. Créez des graphiques :
                   - Distribution des scores
                   - Évolution temporelle
                   - Comparaison par topic
                
                **Python/Pandas :**
                ```python
                import pandas as pd
                import matplotlib.pyplot as plt
                
                # Charger les données
                df = pd.read_csv('results.csv')
                
                # Analyse des scores
                df['score'].hist()
                plt.title('Distribution des Scores')
                plt.show()
                
                # Top idées
                top_ideas = df.nlargest(10, 'score')
                logger.info(top_ideas[['name', 'score']])
                
                # Tendances temporelles
                df['date'] = pd.to_datetime(df['timestamp'])
                daily_scores = df.groupby(df['date'].dt.date)['score'].mean()
                daily_scores.plot()
                ```
                
                **Power BI/Tableau :**
                1. Exportez en JSON
                2. Utilisez le connecteur JSON
                3. Créez un dashboard interactif :
                   - Filtres par topic
                   - KPIs en temps réel
                   - Drill-down sur les idées
                
                **Métriques à suivre :**
                - Score moyen par topic
                - Taux de succès par mode
                - Temps d'exécution tendance
                - Qualité des signaux de marché
                
                **Benchmarking :**
                - Comparez vos résultats
                - Identifiez les patterns de succès
                - Optimisez vos paramètres
                """,
                related_topics=["export_formats", "export_automation"],
                tips=[
                    "CSV est le format le plus simple pour l'analyse",
                    "Normalisez les données avant comparaison",
                    "Utilisez des visualisations pour identifier les patterns"
                ]
            ),
            
            "api_usage": HelpContent(
                title="🔌 Utilisation de l'API",
                category=HelpCategory.EXPORTS,
                content="""
                **Intégrez Asmblr dans vos applications avec l'API REST.**
                
                **Authentication :**
                ```http
                Authorization: Bearer YOUR_API_KEY
                Content-Type: application/json
                ```
                
                **Endpoints principaux :**
                
                **Lancer un pipeline :**
                ```http
                POST /api/v1/pipeline
                {
                    "topic": "AI expense tracking",
                    "execution_profile": "standard",
                    "n_ideas": 10,
                    "seed_inputs": {
                        "icp": "Freelance developers",
                        "pains": ["Manual tracking", "Invoicing issues"]
                    }
                }
                ```
                
                **Statut du pipeline :**
                ```http
                GET /api/v1/pipeline/{run_id}
                
                Response:
                {
                    "run_id": "20240207_120000",
                    "status": "running",
                    "progress": 0.65,
                    "current_stage": "idea_generation",
                    "estimated_completion": "2024-02-07T12:15:00Z"
                }
                ```
                
                **Résultats :**
                ```http
                GET /api/v1/pipeline/{run_id}/results
                
                Response:
                {
                    "run_id": "20240207_120000",
                    "status": "completed",
                    "results": {
                        "research": {...},
                        "analysis": {...},
                        "product": {...}
                    }
                }
                ```
                
                **Métriques :**
                ```http
                GET /api/v1/metrics
                
                Response:
                {
                    "total_runs": 150,
                    "success_rate": 87.3,
                    "avg_execution_time": 12.5,
                    "active_pipelines": 2
                }
                ```
                
                **Webhooks :**
                Configurez des webhooks pour les notifications :
                ```json
                {
                    "event": "pipeline.completed",
                    "run_id": "20240207_120000",
                    "timestamp": "2024-02-07T12:00:00Z",
                    "data": {
                        "status": "success",
                        "confidence_score": 85.2
                    }
                }
                ```
                
                **SDK Python :**
                ```python
                from asmblr_client import AsmblrClient
                
                client = AsmblrClient(api_key="YOUR_KEY")
                
                # Lancer un pipeline
                run = client.start_pipeline(
                    topic="AI expense tracking",
                    execution_profile="standard"
                )
                
                # Attendre les résultats
                results = client.wait_for_completion(run.run_id)
                
                # Exporter
                client.export_results(run.run_id, format="json")
                ```
                """,
                related_topics=["export_automation", "data_analysis"],
                tips=[
                    "Utilisez les webhooks pour une intégration asynchrone",
                    "Limitez le nombre de pipelines concurrents",
                    "Cachez les résultats pour éviter les appels répétés"
                ]
            )
        }
    
    def get_help_content(self, key: str) -> Optional[HelpContent]:
        """Get help content by key."""
        return self.help_contents.get(key)
    
    def get_help_by_category(self, category: HelpCategory) -> List[HelpContent]:
        """Get all help content for a category."""
        return [content for content in self.help_contents.values() 
                if content.category == category]
    
    def search_help(self, query: str) -> List[HelpContent]:
        """Search help content by query."""
        query = query.lower()
        results = []
        
        for content in self.help_contents.values():
            if (query in content.title.lower() or 
                query in content.content.lower() or
                any(query in topic.lower() for topic in content.related_topics)):
                results.append(content)
        
        return results
    
    def render_help_modal(self, help_key: str) -> None:
        """Render help content in a modal."""
        content = self.get_help_content(help_key)
        if not content:
            st.error("Contenu d'aide non trouvé")
            return
        
        with st.expander(f"❓ {content.title}", expanded=True):
            st.markdown(content.content)
            
            if content.tips:
                st.markdown("**💡 Conseils :**")
                for tip in content.tips:
                    st.markdown(f"• {tip}")
            
            if content.related_topics:
                st.markdown("**🔗 Sujets connexes :**")
                for topic in content.related_topics:
                    if st.button(topic, key=f"related_{topic}"):
                        self.render_help_modal(topic)
            
            if content.external_links:
                st.markdown("**🌐 Liens externes :**")
                for link in content.external_links:
                    st.markdown(f"• [{link}]({link})")
            
            if content.video_url:
                st.markdown(f"🎥 [Vidéo tutorielle]({content.video_url})")
    
    def render_help_sidebar(self) -> None:
        """Render help sidebar with navigation."""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ❓ Aide Contextuelle")
        
        # Search
        search_query = st.sidebar.text_input("🔍 Rechercher l'aide")
        
        if search_query:
            results = self.search_help(search_query)
            if results:
                st.sidebar.markdown("**Résultats :**")
                for result in results[:5]:  # Limit results
                    if st.sidebar.button(result.title, key=f"search_{result.title}"):
                        self.render_help_modal(result.title.replace(" ", "_").lower())
            else:
                st.sidebar.info("Aucun résultat trouvé")
        
        # Categories
        st.sidebar.markdown("**Catégories :**")
        
        categories = [
            (HelpCategory.GETTING_STARTED, "🚀 Démarrage"),
            (HelpCategory.PIPELINE, "⚡ Pipeline"),
            (HelpCategory.CONFIGURATION, "⚙️ Configuration"),
            (HelpCategory.MONITORING, "📊 Monitoring"),
            (HelpCategory.EXPORTS, "📤 Exports"),
            (HelpCategory.TROUBLESHOOTING, "🔧 Dépannage")
        ]
        
        for category, label in categories:
            if st.sidebar.button(label, key=f"cat_{category.value}"):
                contents = self.get_help_by_category(category)
                if contents:
                    selected = st.sidebar.selectbox(
                        "Sélectionner :",
                        options=[c.title for c in contents],
                        key=f"select_{category.value}"
                    )
                    if selected:
                        content = next(c for c in contents if c.title == selected)
                        content_key = next(
                            k for k, v in self.help_contents.items() 
                            if v.title == selected
                        )
                        self.render_help_modal(content_key)
        
        # Quick help
        st.sidebar.markdown("**Aide rapide :**")
        quick_help = [
            ("🎯 Premier lancement", "first_run"),
            ("🤖 Ollama setup", "ollama_setup"),
            ("📊 Dashboard", "dashboard_overview"),
            ("🔧 Problèmes", "troubleshooting_connection")
        ]
        
        for label, key in quick_help:
            if st.sidebar.button(label, key=f"quick_{key}"):
                self.render_help_modal(key)


# Global help system instance
_global_help_system = HelpSystem()


def get_help_system() -> HelpSystem:
    """Get the global help system instance."""
    return _global_help_system


def render_contextual_help(context: str) -> None:
    """Render contextual help based on current UI context."""
    help_system = get_help_system()
    
    # Context mapping
    context_mapping = {
        "welcome": "welcome",
        "pipeline": "progress_tracking",
        "dashboard": "dashboard_overview",
        "exports": "export_formats",
        "settings": "execution_modes",
        "ollama": "ollama_setup"
    }
    
    help_key = context_mapping.get(context, "welcome")
    help_system.render_help_modal(help_key)
