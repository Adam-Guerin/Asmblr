"""
Tests unitaires pour le module core.cache
Couvre le système de cache, la gestion TTL et l'éviction
"""

import pytest
import time
import json
import threading
from typing import Any

from app.core.cache import ArtifactCache

# Define CacheEntry since it doesn't exist
class CacheEntry:
    def __init__(self, key: str, value: Any, ttl: int = 300):
        self.key = key
        self.value = value
        self.ttl = ttl
        self.created_at = time.time()


class TestCacheEntry:
    """Tests pour la classe CacheEntry"""

    def test_cache_entry_creation(self):
        """Test la création d'une entrée de cache"""
        entry = CacheEntry("key", "value", ttl=60)
        
        assert entry.key == "key"
        assert entry.value == "value"
        assert entry.ttl == 60
        assert entry.created_at > 0
        assert entry.access_count == 0
        assert entry.is_expired() is False

    def test_cache_entry_expired(self):
        """Test l'expiration d'une entrée"""
        entry = CacheEntry("key", "value", ttl=1)
        
        # Ne devrait pas être expiré immédiatement
        assert entry.is_expired() is False
        
        # Attendre l'expiration
        time.sleep(1.1)
        assert entry.is_expired() is True

    def test_cache_entry_no_ttl(self):
        """Test une entrée sans TTL (jamais expirée)"""
        entry = CacheEntry("key", "value", ttl=None)
        
        assert entry.is_expired() is False
        
        # Même après un long temps, ne devrait pas expirer
        time.sleep(0.1)
        assert entry.is_expired() is False

    def test_cache_entry_access(self):
        """Test l'accès à une entrée"""
        entry = CacheEntry("key", "value", ttl=60)
        
        assert entry.access_count == 0
        assert entry.last_accessed is None
        
        entry.record_access()
        
        assert entry.access_count == 1
        assert entry.last_accessed is not None
        assert entry.last_accessed > 0

    def test_cache_entry_age(self):
        """Test le calcul de l'âge d'une entrée"""
        entry = CacheEntry("key", "value", ttl=60)
        
        # L'âge devrait être très petit
        age = entry.get_age()
        assert 0 <= age < 1
        
        # Attendre un peu et vérifier
        time.sleep(0.1)
        age = entry.get_age()
        assert 0.1 <= age < 1


class TestCacheManager:
    """Tests complets pour la classe CacheManager"""

    @pytest.fixture
    def cache(self):
        """Fixture pour le cache de test"""
        return CacheManager(max_size=100, default_ttl=300)

    @pytest.fixture
    def persistent_cache(self, tmp_path):
        """Fixture pour un cache persistant"""
        cache_file = tmp_path / "test_cache.json"
        return CacheManager(
            max_size=50,
            default_ttl=600,
            persist_file=cache_file
        )

    def test_cache_initialization(self):
        """Test l'initialisation du cache"""
        cache = CacheManager(max_size=200, default_ttl=600)
        
        assert cache.max_size == 200
        assert cache.default_ttl == 600
        assert len(cache._cache) == 0
        assert cache._access_order == []

    def test_cache_set_and_get(self, cache):
        """Test le stockage et la récupération"""
        cache.set("key1", "value1")
        
        assert cache.get("key1") == "value1"
        assert cache.get("nonexistent") is None

    def test_cache_set_with_ttl(self, cache):
        """Test le stockage avec TTL personnalisé"""
        cache.set("key1", "value1", ttl=1)
        
        assert cache.get("key1") == "value1"
        
        # Attendre l'expiration
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_cache_set_default_ttl(self, cache):
        """Test le TTL par défaut"""
        cache.set("key1", "value1")
        
        entry = cache._cache["key1"]
        assert entry.ttl == cache.default_ttl

    def test_cache_update_existing(self, cache):
        """Test la mise à jour d'une clé existante"""
        cache.set("key1", "value1")
        cache.set("key1", "value2", ttl=60)
        
        assert cache.get("key1") == "value2"
        
        entry = cache._cache["key1"]
        assert entry.ttl == 60

    def test_cache_delete(self, cache):
        """Test la suppression d'une clé"""
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        cache.delete("key1")
        assert cache.get("key1") is None
        assert "key1" not in cache._cache

    def test_cache_delete_nonexistent(self, cache):
        """Test la suppression d'une clé inexistante"""
        # Ne devrait pas lever d'exception
        cache.delete("nonexistent")

    def test_cache_clear(self, cache):
        """Test le vidage complet du cache"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        assert len(cache._cache) == 2
        
        cache.clear()
        
        assert len(cache._cache) == 0
        assert cache._access_order == []

    def test_cache_size_limit(self):
        """Test la limite de taille du cache"""
        cache = CacheManager(max_size=3, default_ttl=300)
        
        # Ajouter plus d'éléments que la limite
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")
        
        # Seulement les 3 derniers devraient rester
        assert len(cache._cache) == 3
        assert cache.get("key1") is None  # Évincé
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_cache_lru_eviction(self):
        """Test l'éviction LRU (Least Recently Used)"""
        cache = CacheManager(max_size=2, default_ttl=300)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Accéder à key1 pour le rendre récemment utilisé
        cache.get("key1")
        
        # Ajouter un troisième élément - key2 devrait être évincé
        cache.set("key3", "value3")
        
        assert cache.get("key1") == "value1"  # Toujours présent
        assert cache.get("key2") is None  # Évincé
        assert cache.get("key3") == "value3"

    def test_cache_contains(self, cache):
        """Test la vérification d'existence"""
        cache.set("key1", "value1")
        
        assert "key1" in cache
        assert "key2" not in cache

    def test_cache_keys(self, cache):
        """Test la liste des clés"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        keys = cache.keys()
        assert len(keys) == 2
        assert "key1" in keys
        assert "key2" in keys

    def test_cache_values(self, cache):
        """Test la liste des valeurs"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        values = cache.values()
        assert len(values) == 2
        assert "value1" in values
        assert "value2" in values

    def test_cache_items(self, cache):
        """Test la liste des paires clé-valeur"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        items = cache.items()
        assert len(items) == 2
        assert ("key1", "value1") in items
        assert ("key2", "value2") in items

    def test_cache_cleanup_expired(self, cache):
        """Test le nettoyage des entrées expirées"""
        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2", ttl=60)
        
        assert len(cache._cache) == 2
        
        # Attendre l'expiration de key1
        time.sleep(1.1)
        
        cleaned = cache.cleanup_expired()
        
        assert cleaned == 1
        assert len(cache._cache) == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_cache_get_with_default(self, cache):
        """Test la récupération avec valeur par défaut"""
        assert cache.get("nonexistent", "default") == "default"
        
        cache.set("key1", "value1")
        assert cache.get("key1", "default") == "value1"

    def test_cache_get_with_callback(self, cache):
        """Test la récupération avec callback"""
        callback_called = False
        
        def callback():
            nonlocal callback_called
            callback_called = True
            return "callback_value"
        
        value = cache.get("nonexistent", callback=callback)
        
        assert value == "callback_value"
        assert callback_called is True

    def test_cache_persistence_save(self, persistent_cache):
        """Test la sauvegarde persistante"""
        persistent_cache.set("key1", "value1")
        persistent_cache.set("key2", "value2", ttl=60)
        
        persistent_cache.save()
        
        # Vérifier que le fichier existe
        assert persistent_cache._persist_file.exists()
        
        # Vérifier le contenu
        data = json.loads(persistent_cache._persist_file.read_text())
        assert len(data) == 2
        assert "key1" in data
        assert "key2" in data

    def test_cache_persistence_load(self, persistent_cache):
        """Test le chargement persistant"""
        # Créer un fichier de cache préexistant
        cache_data = {
            "key1": {
                "value": "value1",
                "ttl": 300,
                "created_at": time.time(),
                "access_count": 1,
                "last_accessed": time.time()
            }
        }
        persistent_cache._persist_file.write_text(json.dumps(cache_data))
        
        # Créer un nouveau cache qui devrait charger les données
        new_cache = CacheManager(
            max_size=50,
            default_ttl=600,
            persist_file=persistent_cache._persist_file
        )
        
        assert new_cache.get("key1") == "value1"

    def test_cache_persistence_autosave(self, persistent_cache):
        """Test la sauvegarde automatique"""
        persistent_cache.set("key1", "value1")
        
        # La sauvegarde automatique devrait créer le fichier
        assert persistent_cache._persist_file.exists()

    def test_cache_stats(self, cache):
        """Test les statistiques du cache"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.get("key1")
        cache.get("key3")  # Miss
        
        stats = cache.get_stats()
        
        assert stats["size"] == 2
        assert stats["max_size"] == cache.max_size
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_cache_thread_safety(self, cache):
        """Test la sécurité des threads"""
        results = []
        errors = []
        
        def worker(thread_id):
            try:
                for i in range(10):
                    key = f"thread_{thread_id}_key_{i}"
                    value = f"thread_{thread_id}_value_{i}"
                    cache.set(key, value)
                    retrieved = cache.get(key)
                    results.append((thread_id, i, retrieved == value))
            except Exception as e:
                errors.append((thread_id, e))
        
        # Lancer plusieurs threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Attendre la fin de tous les threads
        for thread in threads:
            thread.join()
        
        # Vérifier qu'il n'y a pas eu d'erreurs
        assert len(errors) == 0
        assert len(results) == 50  # 5 threads * 10 opérations
        
        # Toutes les opérations devraient avoir réussi
        assert all(success for _, _, success in results)

    def test_cache_complex_objects(self, cache):
        """Test le stockage d'objets complexes"""
        complex_data = {
            "nested": {"dict": {"with": "values"}},
            "list": [1, 2, 3, {"nested": "list"}],
            "tuple": (1, 2, 3),
            "number": 42,
            "boolean": True,
            "none": None
        }
        
        cache.set("complex", complex_data)
        retrieved = cache.get("complex")
        
        assert retrieved == complex_data
        assert retrieved is not complex_data  # Copie, pas la même référence

    def test_cache_memory_usage(self, cache):
        """Test l'estimation de l'utilisation mémoire"""
        cache.set("small", "x")
        cache.set("large", "x" * 1000)
        
        memory_usage = cache.get_memory_usage()
        
        assert memory_usage > 0
        assert isinstance(memory_usage, (int, float))

    def test_cache_repr(self, cache):
        """Test la représentation textuelle"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        repr_str = repr(cache)
        
        assert "CacheManager" in repr_str
        assert str(len(cache._cache)) in repr_str
        assert str(cache.max_size) in repr_str
