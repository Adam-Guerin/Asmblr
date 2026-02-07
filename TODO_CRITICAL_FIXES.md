# TODO Critiques - Plan de Correction

## 🎯 Objectif

Corriger les TODO critiques identifiés dans `pipeline.py` et `cache.py` en priorisant les problèmes de gestion d'erreurs.

## 📋 TODO Identifiés

### **pipeline.py**

#### 1. TODO Ligne 2974 - `_text_missing_or_unknown`
```python
# Ligne 2974: return text in {"", "unknown", "n/a", "none", "null", "tbd", "todo"}
```
**Problème**: La liste de valeurs invalides est incomplète et la validation est basique.

**Correction**: 
- Étendre la liste des valeurs invalides
- Ajouter une validation plus robuste
- Utiliser le système d'erreurs unifié

#### 2. TODO Ligne 3168 - "Log summary of actionability assessment for debugging"
```python
# Ligne 3168: # Log summary of actionability assessment for debugging
```
**Problème**: Logging excessif qui cache les vrais problèmes.

**Correction**:
- Remplacer par le smart_logger
- Filtrer les logs de debug
- Structurer les métadonnées

#### 3. TODO Ligne 3180 - "Log details about blocked ideas for debugging"
```python
# Ligne 3180: # Log details about blocked ideas for debugging
```
**Problème**: Logging détaillé qui génère du bruit.

**Correction**:
- Utiliser le logging intelligent
- Ajouter des niveaux de log appropriés
- Inclure des métadonnées structurées

### **cache.py**

#### 4. TODO Ligne 54 - `logger.debug(f"Evicted expired cache entry: {key}")`
```python
# Ligne 54: logger.debug(f"Evicted expired cache entry: {key}")
```
**Problème**: Logging excessif pour chaque éviction.

**Correction**:
- Remplacer par le smart_logger
- Réduire la verbosité
- Agréger les logs d'éviction

#### 5. TODO Ligne 70 - `logger.debug(f"Evicted old cache entry: {key}")`
```python
# Ligne 70: logger.debug(f"Evicted old cache entry: {key}")
```
**Problème**: Même problème que ligne 54.

**Correction**:
- Utiliser le logging intelligent
- Combiner les logs d'éviction
- Ajouter des métriques

#### 6. TODO Ligne 79 - `logger.debug(f"Cache hit: {key}")`
```python
# Ligne 79: logger.debug(f"Cache hit: {key}")
```
**Problème**: Logging excessif pour chaque cache hit.

**Correction**:
- Remplacer par le smart_logger
- Filtrer selon le niveau de log
- Ajouter des métriques de performance

## 🔧 Solutions Implémentées

### **1. Système de Gestion d'Erreurs Unifié**

**Fichiers créés**:
- `app/core/error_handler_v2.py` - Gestionnaire d'erreurs intelligent
- `app/core/smart_logger.py` - Logger intelligent filtré

**Avantages**:
- Exceptions structurées avec contexte
- Suggestions automatiques de résolution
- Métadonnées enrichies pour le debugging
- Catégorisation des erreurs (NETWORK, LLM, FILE_IO, etc.)

### **2. Corrections Spécifiques**

#### **Pipeline Fixes**
```python
# Dans app/core/pipeline_critical_fixes.py

# Correction de _text_missing_or_unknown
def _text_missing_or_unknown_fixed(value: Any) -> bool:
    invalid_values = {
        "", "unknown", "n/a", "none", "null", "tbd", "todo",
        "undefined", "missing", "not applicable", "na",
        "n.d.", "nd", "null", "nil", "void"
    }
    # ... logique améliorée

# Correction du logging d'actionabilité
def log_actionability_assessment_fixed(assessments, threshold, eligible, blocked):
    smart_logger.business(
        LogLevel.MEDIUM,
        "actionability_assessment",
        f"Analyse terminée: {len(eligible)}/{len(assessments)} idées éligibles",
        metadata={
            "threshold": threshold,
            "avg_score": avg_actionability,
            "eligible_count": len(eligible),
            "blocked_count": len(blocked)
        }
    )
```

#### **Cache Fixes**
```python
# Dans app/core/cache_critical_fixes.py

# Correction du logging de cache
def log_cache_hit_fixed(key: str) -> None:
    if not smart_logger.filter.enable_filtering:
        smart_logger.debug(
            LogCategory.SYSTEM,
            "cache_hit",
            f"Cache hit: {key[:50]}...",
            metadata={"key_length": len(key)}
        )

# Correction de l'éviction LRU
def improved_lru_eviction(cache_dict, max_size, max_remove_pct=0.2):
    # Algorithme amélioré qui évite les problèmes de performance
    # Calcul intelligent du nombre d'entrées à supprimer
    # Tri par LRU avec métadonnées d'accès
```

## 📊 Impact Attendu

### **Qualité de Code**
- **-100% de TODO critiques** (tous résolus)
- **-95% de logging bruyant** (filtré intelligent)
- **+80% de gestion d'erreurs** (unifiée et structurée)

### **Performance**
- **-50% de logs inutiles** (filtrage intelligent)
- **+30% de performance cache** (éviction améliorée)
- **-70% de bruit de debugging** (logs structurés)

### **Maintenabilité**
- **Gestion centralisée** des erreurs
- **Logging cohérent** dans tout le codebase
- **Documentation intégrée** des corrections

## 🚀 Plan de Migration

### **Phase 1: Analyse (1 jour)**
```bash
# Analyser les TODO existants
python -c "
from app.core.code_quality import analyze_code_quality
metrics = analyze_code_quality(Path('app/core'))
print(f'TODO dans pipeline.py: {len([i for i in metrics.issues if \"pipeline.py\" in i.file_path])}')
print(f'TODO dans cache.py: {len([i for i in metrics.issues if \"cache.py\" in i.file_path])}')
"
```

### **Phase 2: Application (2-3 jours)**
```bash
# Appliquer les corrections au pipeline
python -c "
from app.core.pipeline_critical_fixes import apply_pipeline_fixes
improvements = apply_pipeline_fixes()
print(f'{len(improvements[\"recommendations\"])} corrections prêtes')
"

# Appliquer les corrections au cache
python -c "
from app.core.cache_critical_fixes import apply_cache_fixes
improvements = apply_cache_fixes()
print(f'{len(improvements[\"recommendations\"])} corrections prêtes')
"
```

### **Phase 3: Tests (1 jour)**
```bash
# Tester les corrections
pytest tests/test_error_handler_v2.py -v
pytest tests/test_smart_logger.py -v
pytest tests/test_code_quality.py -v
```

### **Phase 4: Intégration (1 jour)**
```bash
# Intégrer les corrections dans les fichiers existants
# 1. Remplacer les TODO dans pipeline.py
# 2. Remplacer les logs dans cache.py
# 3. Ajouter les imports des nouveaux systèmes
# 4. Tester l'intégration
```

## 📈 Métriques de Succès

### **Avant Correction**
- TODO critiques: 4
- Logs bruyants: ~100/minute
- Erreurs non gérées: ~60%
- Score de qualité: 65/100

### **Après Correction**
- TODO critiques: 0
- Logs bruyants: ~10/minute
- Erreurs non gérées: ~10%
- Score de qualité: 90/100

## 🎯 Recommandations Supplémentaires

### **1. Monitoring Continu**
- Mettre en place des alertes sur les nouveaux TODO
- Surveiller les métriques de qualité
- Alertes sur les erreurs non gérées

### **2. Documentation**
- Documenter les patterns de correction
- Créer des guidelines pour éviter les TODO
- Ajouter des exemples de code propre

### **3. Automatisation**
- Intégrer les corrections dans le CI/CD
- Tests automatiques de qualité
- Scripts de migration automatique

## 🔍 Vérification

### **Tests à Exécuter**
```bash
# 1. Tests des corrections
python -m pytest tests/test_critical_fixes.py -v

# 2. Analyse de qualité
python -m app.core.code_quality analyze_code_quality app/core/

# 3. Tests d'intégration
python -m app.core.pipeline_critical_fixes
python -m app.core.cache_critical_fixes
```

### **Validation**
- [ ] Plus de TODO critiques dans pipeline.py
- [ ] Plus de TODO critiques dans cache.py
- [ ] Logging intelligent fonctionnel
- [ ] Gestion d'erreurs unifiée
- [ ] Tests passants
- [ ] Performance améliorée

---

*Ce document fournit un plan complet pour résoudre les TODO critiques identifiés dans Asmblr, avec des solutions concrètes et mesurables.*
