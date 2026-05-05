"""
Jednoduchá mezipaměť pro TalosForge.

Tento modul poskytuje SimpleCache třídu pro ukládání často používaných dat
jako jsou OpenAPI specifikace stažené z URL.
"""

import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SimpleCache:
    """
    Jednoduchá slovníková mezipaměť s volitelnou časovou platností.

    Tato třída poskytuje jednoduchou mezipaměť pro ukládání hodnot
    pod klíči. Podporuje volitelnou časovou platnost (TTL).

    Example:
        >>> cache = SimpleCache(ttl=3600)  # 1 hodina
        >>> cache.set("key", "value")
        >>> value = cache.get("key")
        >>> print(value)
        'value'
    """

    def __init__(self, ttl: Optional[int] = None):
        """
        Inicializuje SimpleCache.

        Args:
            ttl: Time-to-live v sekundách. Pokud None, cache neexpiruje.
        """
        self._cache: Dict[str, tuple[Any, float]] = {}
        self.ttl = ttl
        logger.debug(f"SimpleCache inicializován s TTL={ttl}s")

    def get(self, key: str) -> Optional[Any]:
        """
        Získá hodnotu z cache.

        Args:
            key: Klíč pro získání hodnoty.

        Returns:
            Hodnota nebo None pokud klíč neexistuje nebo expiroval.

        Example:
            >>> cache = SimpleCache()
            >>> cache.set("test", "value")
            >>> result = cache.get("test")
            >>> print(result)
            'value'
        """
        if key not in self._cache:
            return None

        value, timestamp = self._cache[key]

        # Kontrola expirace
        if self.ttl is not None:
            if time.time() - timestamp > self.ttl:
                logger.debug(f"Cache klíč '{key}' expiroval")
                del self._cache[key]
                return None

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Uloží hodnotu do cache.

        Args:
            key: Klíč pro uložení hodnoty.
            value: Hodnota k uložení.

        Example:
            >>> cache = SimpleCache()
            >>> cache.set("user", {"name": "John"})
        """
        self._cache[key] = (value, time.time())
        logger.debug(f"Uloženo do cache: '{key}'")

    def has(self, key: str) -> bool:
        """
        Zkontroluje, zda klíč existuje v cache a neexpiroval.

        Args:
            key: Klíč pro kontrolu.

        Returns:
            True pokud klíč existuje a je platný, jinak False.

        Example:
            >>> cache = SimpleCache()
            >>> cache.set("test", "value")
            >>> cache.has("test")
            True
        """
        return self.get(key) is not None

    def clear(self) -> None:
        """
        Vymaže celou cache.

        Example:
            >>> cache = SimpleCache()
            >>> cache.set("test", "value")
            >>> cache.clear()
            >>> cache.has("test")
            False
        """
        self._cache.clear()
        logger.debug("Cache vymazána")

    def remove(self, key: str) -> bool:
        """
        Odstraní konkrétní klíč z cache.

        Args:
            key: Klíč k odstranění.

        Returns:
            True pokud klíč byl odstraněn, False pokud neexistoval.

        Example:
            >>> cache = SimpleCache()
            >>> cache.set("test", "value")
            >>> removed = cache.remove("test")
            >>> print(removed)
            True
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Odstraněno z cache: '{key}'")
            return True
        return False

    def size(self) -> int:
        """
        Vrátí počet položek v cache (včetně expirovaných).

        Returns:
            Počet položek v cache.

        Example:
            >>> cache = SimpleCache()
            >>> cache.set("a", 1)
            >>> cache.set("b", 2)
            >>> print(cache.size())
            2
        """
        return len(self._cache)

    def cleanup(self) -> int:
        """
        Odstraní všechny expirované položky z cache.

        Returns:
            Počet odstraněných položek.

        Example:
            >>> cache = SimpleCache(ttl=0)  # Okamžitá expirace
            >>> cache.set("test", "value")
            >>> import time
            >>> time.sleep(0.1)
            >>> removed = cache.cleanup()
            >>> print(removed)
            1
        """
        if self.ttl is None:
            return 0

        removed = 0
        current_time = time.time()
        keys_to_remove = []

        for key, (_, timestamp) in self._cache.items():
            if current_time - timestamp > self.ttl:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._cache[key]
            removed += 1

        if removed > 0:
            logger.debug(f"Cleanup odstranil {removed} expirovaných položek")

        return removed
