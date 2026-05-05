"""
Testy pro SimpleCache.
"""

import time

from TalosForge.utils.cache import SimpleCache


def test_cache_set_and_get():
    """Test ukládání a získávání z cache."""
    cache = SimpleCache()
    cache.set("key", "value")
    assert cache.get("key") == "value"


def test_cache_get_nonexistent():
    """Test získání neexistujícího klíče."""
    cache = SimpleCache()
    assert cache.get("nonexistent") is None


def test_cache_has():
    """Test metody has."""
    cache = SimpleCache()
    cache.set("key", "value")
    assert cache.has("key") is True
    assert cache.has("nonexistent") is False


def test_cache_clear():
    """Test vymazání cache."""
    cache = SimpleCache()
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    assert cache.size() == 2

    cache.clear()
    assert cache.size() == 0
    assert cache.get("key1") is None


def test_cache_remove():
    """Test odstranění konkrétního klíče."""
    cache = SimpleCache()
    cache.set("key", "value")
    assert cache.remove("key") is True
    assert cache.has("key") is False
    assert cache.remove("key") is False


def test_cache_ttl():
    """Test časové platnosti (TTL)."""
    cache = SimpleCache(ttl=1)  # 1 sekunda
    cache.set("key", "value")

    # Okamžitě by mělo být dostupné
    assert cache.get("key") == "value"

    # Po 1.1 sekundě by mělo být ne dostupné
    time.sleep(1.1)
    assert cache.get("key") is None


def test_cache_no_ttl():
    """Test cache bez TTL."""
    cache = SimpleCache(ttl=None)
    cache.set("key", "value")

    # I po čase by mělo být dostupné
    time.sleep(0.1)
    assert cache.get("key") == "value"


def test_cache_cleanup():
    """Test cleanup metody."""
    cache = SimpleCache(ttl=1)
    cache.set("key1", "value1")
    cache.set("key2", "value2")

    time.sleep(1.1)

    removed = cache.cleanup()
    assert removed == 2
    assert cache.size() == 0


def test_cache_size():
    """Test metody size."""
    cache = SimpleCache()
    assert cache.size() == 0

    cache.set("key1", "value1")
    assert cache.size() == 1

    cache.set("key2", "value2")
    assert cache.size() == 2
