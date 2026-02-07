# Mode Validation Sprint 7 Jours

## Overview

Le mode **Validation Sprint 7 jours** est une nouvelle approche d'exécution orientée vers l'action, conçue spécifiquement pour les solo founders qui veulent valider rapidement leur idée sur le marché.

## Objectif

Générer une sortie complète et exécutable en 7 jours comprenant :
- **Hypothèse de validation** claire et mesurable
- **Plan de test A/B** pour optimiser la conversion
- **Contenu landing page** avec copy optimisée
- **3 messages outreach** pour différents canaux
- **KPI cibles** pour suivre les progrès

## Caractéristiques

### Configuration du Profil

```python
"validation_sprint": {
    "name": "validation_sprint",
    "time_budget_min": 15,        # 15 minutes max
    "token_budget_est": 25000,      # Optimisé pour rapidité
    "max_sources": 5,              # Sources ciblées et pertinentes
    "max_n_ideas": 1,             # Une seule idée pour focus
    "stage_retry_attempts": 1,       # Exécution rapide
    "force_fast_mode": True,         # Optimisé pour la vitesse
    "output_mode": "execution_focused"  # Déclenche la sortie spéciale
}
```

### Sortie Générée

#### 1. Hypothèse de Validation
- **Segment Cible** : Identifié depuis l'idée top score
- **Problème Clé** : Extrait des pains validés
- **Solution Proposée** : Nom de l'idée
- **Énoncé Complet** : Template "Nous croyons que..."
- **Confiance** : 65% (medium)
- **Risque** : Évalué comme MEDIUM

#### 2. Plan de Test A/B
- **Durée** : 7 jours
- **Variante A** : Control - MVP Features
  - Interface simplifiée
  - Onboarding rapide
  - Prix d'essai gratuit
- **Variante B** : Test - Enhanced Value Prop
  - Copy optimisé
  - Social proof
  - Garantie satisfait ou remboursé
- **Critères de Succès** :
  - Taux conversion > 10%
  - Temps sur page > 2 minutes
  - Taux engagement > 30%

#### 3. Contenu Landing Page
- **Titre Principal** : "La solution [IDÉE] pour [SEGMENT]"
- **Sous-titre** : "Résolvez [PROBLÈME] en moins de temps"
- **Bénéfices Clés** :
  - Économisez 10h par semaine
  - Lancez plus vite vos projets
  - Automatisez les tâches répétitives
- **Preuve Sociale** :
  - Rejoint par 50+ entrepreneurs en beta
  - 4.8/5 étoiles sur les premiers tests
  - Cas d'usage validés par 3 experts
- **Appels à l'Action** :
  - Principal : "Commencer l'essai gratuit - 7 jours"
  - Secondaire : "Voir la démo en 2 minutes"
- **Tarification** :
  - Essai : "Gratuit 7 jours"
  - Après essai : "29€/mois - sans engagement"
  - Garantie : "Satisfait ou remboursé 30 jours"

#### 4. Messages Outreach (3 canaux)

**Message 1 - Email Cold Outreach**
- **Canal** : Email
- **Timing** : Jour 2-3 du sprint
- **Audience** : Cold prospects
- **Sujet** : "Aide pour [problème] ?"
- **Template** : Personnalisé avec [PRÉNOM], [PRINCIPAL_BÉNÉFICE]

**Message 2 - LinkedIn Direct**
- **Canal** : LinkedIn
- **Timing** : Jour 4-5 du sprint
- **Audience** : LinkedIn connections
- **Sujet** : "Solution pour [problème]"
- **Template** : Plus direct et concis

**Message 3 - Communauté Engagement**
- **Canal** : Communauté/Forum
- **Timing** : Jour 5-7 du sprint
- **Audience** : Community/Forum members
- **Sujet** : "Retour d'expérience validation sprint"
- **Template** : Partage des résultats intermédiaires

#### 5. KPI Cibles

**KPIs Primaires**
- **Taux Conversion** : 15% cible
- **Taux Activation** : 60% cible
- **Rétention J7** : 40% cible

**KPIs Secondaires**
- **Temps Engagement** : 2+ minutes cible
- **Adoption Fonctionnalités** : 3+ fonctionnalités cible
- **Score NPS** : +40 cible

**Critères de Succès**
- **Minimum Viable** : Conversion > 10% ET Activation > 40%
- **Cible Atteinte** : Conversion > 15% ET Activation > 60%
- **Exceptionnel** : Conversion > 25% ET Retention > 50%

## Avantages par Rapport au "Pack Complet"

### ✅ Plus Vendable
- **Prix Positionnement** : Offre claire à 7 jours vs analyse complète à plusieurs semaines
- **Cible Claire** : Solo founders veulent de l'action rapide, pas de la analyse infinie
- **ROI Mesurable** : Résultats en 7 jours vs investissement en temps/mois

### ✅ Plus Pratique
- **Exécution Immédiate** : Tous les matériaux prêts à déployer
- **Guides Pas-à-Pas** : Instructions quotidiennes claires
- **Templates Réutilisables** : Messages, landing, KPIs prêts à l'emploi

### ✅ Plus Focalisé
- **Une Seule Idée** : Focus total vs dispersion sur multiples idées
- **Validation Rapide** : 7 jours pour go/no-go vs 3-6 mois d'analyse
- **Apprentissage Accéléré** : Feedback rapide pour itération

## Intégration Technique

### Pipeline Principal
- **Fichier** : `app/core/pipeline.py`
- **Méthode** : `_generate_validation_sprint_output()`
- **Déclenchement** : `profile.get("output_mode") == "execution_focused"`

### Interface Utilisateur
- **Fichier** : `ui.py`
- **Sélecteur** : Mode d'exécution avec 3 options
- **Paramètre** : `validation_sprint_mode` passé au pipeline

### Tests
- **Fichier** : `tests/test_validation_sprint_mode.py`
- **Couverture** : Tests complets pour toutes les composantes
- **Validation** : Structure de sortie, génération de contenu, intégration UI

## Cas d'Usage

### Idéal Pour
- **Solo Founders** : Veulent valider rapidement avec budget limité
- **Première Version** : Test de marché avant développement lourd
- **Approche Lean** : Build-Measure-Learn en cycle d'une semaine

### Workflow Type
1. **Lancer** : Choisir "Validation Sprint 7 jours" + sujet
2. **Générer** : Obtenir hypothèse, test A/B, landing, messages, KPIs
3. **Exécuter** : Déployer landing et lancer outreach
4. **Analyser** : Mesurer KPIs après 7 jours
5. **Décider** : Pivot vs Persevere basé sur résultats

## Fichiers Générés

1. **`validation_sprint_output.json`** : Données structurées complètes
2. **`validation_sprint_plan.md`** : Plan lisible en markdown
3. **Intégration** : S'interface avec les résultats standards du pipeline

---

*Ce mode transforme Asmblr d'outil d'analyse en plateforme de validation rapide pour entrepreneurs.*
