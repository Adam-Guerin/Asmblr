"""
Cache LLM Sémantique Avancé avec Embeddings
Utilise les embeddings pour trouver des réponses similaires sémantiquement
"""

import asyncio
import json
import hashlib
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import redis
import pickle
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Entrée de cache avec embeddings"""
    prompt: str
    response: str
    embedding: np.ndarray
    model_name: str
    timestamp: datetime
    hit_count: int = 0
    last_accessed: datetime = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp


@dataclass
class CacheStats:
    """Statistiques du cache sémantique"""
    total_entries: int = 0
    semantic_hits: int = 0
    exact_hits: int = 0
    misses: int = 0
    avg_similarity_score: float = 0.0
    cache_hit_rate: float = 0.0
    embedding_cache_size: int = 0


class SemanticLLMCache:
    """Cache LLM avec recherche sémantique"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        model_name: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.85,
        max_entries: int = 10000,
        ttl_hours: int = 24,
        embedding_dim: int = 384
    ):
        self.redis_url = redis_url
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.max_entries = max_entries
        self.ttl_hours = ttl_hours
        self.embedding_dim = embedding_dim
        
        # Initialiser le modèle d'embeddings
        self.model = SentenceTransformer(model_name)
        
        # Initialiser Redis
        self.redis_client = redis.from_url(redis_url)
        
        # Initialiser FAISS pour la recherche vectorielle
        self.index = faiss.IndexFlatIP(embedding_dim)  # Inner Product
        self.entries: List[CacheEntry] = []
        
        # Statistiques
        self.stats = CacheStats()
        
        # Cache des embeddings
        self.embedding_cache: Dict[str, np.ndarray] = {}
        
        logger.info(f"Cache sémantique initialisé avec modèle {model_name}")
    
    async def initialize(self):
        """Initialisation asynchrone"""
        try:
            # Charger les entrées existantes depuis Redis
            await self._load_from_redis()
            
            # Reconstruire l'index FAISS
            await self._rebuild_index()
            
            logger.info(f"Cache initialisé avec {len(self.entries)} entrées")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation: {e}")
            raise
    
    async def get(self, prompt: str, model_name: str) -> Optional[str]:
        """
        Récupère une réponse depuis le cache avec recherche sémantique
        
        Args:
            prompt: Le prompt à rechercher
            model_name: Nom du modèle LLM
            
        Returns:
            La réponse mise en cache ou None
        """
        start_time = time.time()
        
        try:
            # 1. Vérifier le cache exact d'abord
            exact_key = self._get_exact_key(prompt, model_name)
            exact_response = self.redis_client.get(exact_key)
            
            if exact_response:
                self.stats.exact_hits += 1
                logger.debug(f"Cache exact hit pour prompt: {prompt[:50]}...")
                return exact_response.decode('utf-8')
            
            # 2. Recherche sémantique
            embedding = await self._get_embedding(prompt)
            
            if len(self.entries) > 0:
                # Rechercher les entrées similaires
                similar_entries = await self._search_similar(embedding, model_name)
                
                if similar_entries:
                    best_entry = similar_entries[0]
                    similarity = self._calculate_similarity(embedding, best_entry.embedding)
                    
                    if similarity >= self.similarity_threshold:
                        # Mettre à jour les statistiques
                        best_entry.hit_count += 1
                        best_entry.last_accessed = datetime.now()
                        
                        self.stats.semantic_hits += 1
                        self.stats.avg_similarity_score = (
                            (self.stats.avg_similarity_score * (self.stats.semantic_hits - 1) + similarity)
                            / self.stats.semantic_hits
                        )
                        
                        # Sauvegarder la mise à jour
                        await self._save_entry(best_entry)
                        
                        logger.debug(f"Cache sémantique hit (similarity: {similarity:.3f})")
                        return best_entry.response
            
            # 3. Miss
            self.stats.misses += 1
            self._update_hit_rate()
            
            logger.debug(f"Cache miss pour prompt: {prompt[:50]}...")
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du cache: {e}")
            return None
        finally:
            duration = time.time() - start_time
            logger.debug(f"Opération cache terminée en {duration:.3f}s")
    
    async def put(self, prompt: str, response: str, model_name: str) -> bool:
        """
        Stocke une réponse dans le cache
        
        Args:
            prompt: Le prompt original
            response: La réponse à mettre en cache
            model_name: Nom du modèle LLM
            
        Returns:
            True si succès, False sinon
        """
        try:
            # 1. Stocker dans Redis pour accès exact
            exact_key = self._get_exact_key(prompt, model_name)
            self.redis_client.setex(
                exact_key,
                timedelta(hours=self.ttl_hours),
                response
            )
            
            # 2. Créer l'entrée avec embedding
            embedding = await self._get_embedding(prompt)
            entry = CacheEntry(
                prompt=prompt,
                response=response,
                embedding=embedding,
                model_name=model_name,
                timestamp=datetime.now()
            )
            
            # 3. Ajouter à l'index FAISS
            await self._add_to_index(entry)
            
            # 4. Nettoyer si nécessaire
            await self._cleanup_if_needed()
            
            # 5. Sauvegarder dans Redis
            await self._save_entry(entry)
            
            self.stats.total_entries = len(self.entries)
            
            logger.debug(f"Entrée ajoutée au cache: {prompt[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du stockage dans le cache: {e}")
            return False
    
    async def _get_embedding(self, text: str) -> np.ndarray:
        """Récupère ou calcule l'embedding d'un texte"""
        # Vérifier le cache d'embeddings
        cache_key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
        
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        # Calculer l'embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        # Normaliser pour la similarité cosinus
        embedding = embedding / np.linalg.norm(embedding)
        
        # Mettre en cache
        self.embedding_cache[cache_key] = embedding
        self.stats.embedding_cache_size = len(self.embedding_cache)
        
        return embedding
    
    async def _search_similar(self, query_embedding: np.ndarray, model_name: str, top_k: int = 5) -> List[CacheEntry]:
        """Recherche les entrées similaires dans le cache"""
        if len(self.entries) == 0:
            return []
        
        # Filtrer par modèle
        filtered_entries = [e for e in self.entries if e.model_name == model_name]
        
        if len(filtered_entries) == 0:
            return []
        
        # Créer un index temporaire pour les entrées filtrées
        temp_index = faiss.IndexFlatIP(self.embedding_dim)
        embeddings = np.array([e.embedding for e in filtered_entries])
        temp_index.add(embeddings)
        
        # Rechercher
        query_embedding = query_embedding.reshape(1, -1)
        similarities, indices = temp_index.search(query_embedding, min(top_k, len(filtered_entries)))
        
        # Retourner les entrées triées par similarité
        results = []
        for similarity, idx in zip(similarities[0], indices[0]):
            if similarity >= self.similarity_threshold:
                results.append(filtered_entries[idx])
        
        return results
    
    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calcule la similarité cosinus entre deux embeddings"""
        return float(np.dot(embedding1, embedding2))
    
    async def _add_to_index(self, entry: CacheEntry):
        """Ajoute une entrée à l'index FAISS"""
        self.entries.append(entry)
        
        # Ajouter à l'index FAISS
        embedding = entry.embedding.reshape(1, -1)
        self.index.add(embedding)
    
    async def _save_entry(self, entry: CacheEntry):
        """Sauvegarde une entrée dans Redis"""
        key = f"semantic_entry:{hashlib.md5(entry.prompt.encode()).hexdigest()}"
        
        # Sérialiser l'entrée (sans l'embedding pour économiser de l'espace)
        entry_data = asdict(entry)
        entry_data['embedding'] = entry.embedding.tolist()  # Convertir numpy en list
        
        self.redis_client.setex(
            key,
            timedelta(hours=self.ttl_hours),
            json.dumps(entry_data, default=str)
        )
    
    async def _load_from_redis(self):
        """Charge les entrées depuis Redis"""
        pattern = "semantic_entry:*"
        keys = self.redis_client.keys(pattern)
        
        for key in keys:
            try:
                data = self.redis_client.get(key)
                if data:
                    entry_data = json.loads(data)
                    
                    # Reconstruire l'entrée
                    entry = CacheEntry(
                        prompt=entry_data['prompt'],
                        response=entry_data['response'],
                        embedding=np.array(entry_data['embedding']),
                        model_name=entry_data['model_name'],
                        timestamp=datetime.fromisoformat(entry_data['timestamp']),
                        hit_count=entry_data.get('hit_count', 0),
                        last_accessed=datetime.fromisoformat(entry_data['last_accessed']) if entry_data.get('last_accessed') else None
                    )
                    
                    self.entries.append(entry)
                    
            except Exception as e:
                logger.warning(f"Erreur lors du chargement de l'entrée {key}: {e}")
    
    async def _rebuild_index(self):
        """Reconstruit l'index FAISS"""
        if len(self.entries) == 0:
            return
        
        embeddings = np.array([entry.embedding for entry in self.entries])
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.index.add(embeddings)
        
        logger.info(f"Index FAISS reconstruit avec {len(self.entries)} entrées")
    
    async def _cleanup_if_needed(self):
        """Nettoie les anciennes entrées si nécessaire"""
        if len(self.entries) <= self.max_entries:
            return
        
        # Trier par last_accessed et supprimer les plus anciennes
        sorted_entries = sorted(self.entries, key=lambda x: x.last_accessed)
        
        entries_to_remove = sorted_entries[:len(self.entries) - self.max_entries]
        
        for entry in entries_to_remove:
            # Supprimer de Redis
            key = f"semantic_entry:{hashlib.md5(entry.prompt.encode()).hexdigest()}"
            self.redis_client.delete(key)
            
            # Supprimer de la liste
            self.entries.remove(entry)
        
        # Reconstruire l'index
        await self._rebuild_index()
        
        logger.info(f"Nettoyage effectué: {len(entries_to_remove)} entrées supprimées")
    
    def _get_exact_key(self, prompt: str, model_name: str) -> str:
        """Génère la clé pour le cache exact"""
        prompt_hash = hashlib.md5(f"{model_name}:{prompt}".encode()).hexdigest()
        return f"exact_cache:{prompt_hash}"
    
    def _update_hit_rate(self):
        """Met à jour le taux de hit"""
        total_requests = self.stats.exact_hits + self.stats.semantic_hits + self.stats.misses
        if total_requests > 0:
            self.stats.cache_hit_rate = (self.stats.exact_hits + self.stats.semantic_hits) / total_requests
    
    async def get_stats(self) -> CacheStats:
        """Retourne les statistiques du cache"""
        self._update_hit_rate()
        self.stats.total_entries = len(self.entries)
        return self.stats
    
    async def clear_cache(self):
        """Vide complètement le cache"""
        try:
            # Supprimer toutes les clés Redis
            patterns = ["exact_cache:*", "semantic_entry:*", "embedding:*"]
            for pattern in patterns:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            
            # Vider les structures en mémoire
            self.entries.clear()
            self.embedding_cache.clear()
            
            # Reconstruire l'index
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            
            # Réinitialiser les statistiques
            self.stats = CacheStats()
            
            logger.info("Cache vidé complètement")
            
        except Exception as e:
            logger.error(f"Erreur lors du vidage du cache: {e}")
    
    async def export_cache(self, filepath: str):
        """Exporte le cache dans un fichier"""
        try:
            export_data = {
                'entries': [asdict(entry) for entry in self.entries],
                'stats': asdict(self.stats),
                'export_timestamp': datetime.now().isoformat()
            }
            
            # Convertir les embeddings numpy en listes
            for entry_data in export_data['entries']:
                entry_data['embedding'] = entry_data['embedding'].tolist()
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Cache exporté dans {filepath}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export du cache: {e}")
    
    async def import_cache(self, filepath: str):
        """Importe le cache depuis un fichier"""
        try:
            with open(filepath, 'r') as f:
                import_data = json.load(f)
            
            # Vider le cache actuel
            await self.clear_cache()
            
            # Importer les entrées
            for entry_data in import_data['entries']:
                entry = CacheEntry(
                    prompt=entry_data['prompt'],
                    response=entry_data['response'],
                    embedding=np.array(entry_data['embedding']),
                    model_name=entry_data['model_name'],
                    timestamp=datetime.fromisoformat(entry_data['timestamp']),
                    hit_count=entry_data.get('hit_count', 0),
                    last_accessed=datetime.fromisoformat(entry_data['last_accessed']) if entry_data.get('last_accessed') else None
                )
                
                await self._add_to_index(entry)
                await self._save_entry(entry)
            
            # Importer les statistiques
            if 'stats' in import_data:
                stats_data = import_data['stats']
                self.stats = CacheStats(**stats_data)
            
            # Reconstruire l'index
            await self._rebuild_index()
            
            logger.info(f"Cache importé depuis {filepath}: {len(self.entries)} entrées")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'import du cache: {e}")


# Singleton global
_semantic_cache: Optional[SemanticLLMCache] = None


async def get_semantic_cache() -> SemanticLLMCache:
    """Retourne l'instance singleton du cache sémantique"""
    global _semantic_cache
    
    if _semantic_cache is None:
        _semantic_cache = SemanticLLMCache()
        await _semantic_cache.initialize()
    
    return _semantic_cache


# Exemple d'utilisation
async def example_usage():
    """Exemple d'utilisation du cache sémantique"""
    cache = await get_semantic_cache()
    
    # Test de mise en cache
    prompt1 = "Comment créer une startup IA?"
    response1 = "Pour créer une startup IA, vous devez..."
    
    await cache.put(prompt1, response1, "llama3.1:8b")
    
    # Test de récupération exacte
    result = await cache.get(prompt1, "llama3.1:8b")
    print(f"Résultat exact: {result}")
    
    # Test de récupération sémantique
    prompt2 = "Quelles sont les étapes pour lancer une entreprise d'intelligence artificielle?"
    result = await cache.get(prompt2, "llama3.1:8b")
    print(f"Résultat sémantique: {result}")
    
    # Statistiques
    stats = await cache.get_stats()
    print(f"Statistiques: {stats}")


if __name__ == "__main__":
    asyncio.run(example_usage())
