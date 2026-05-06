"""
Base schema reader module for database introspection.

Tento modul poskytuje abstraktní základní třídu pro čtení databázových schémat.
Každá databázová backend (PostgreSQL, MySQL, atd.) implementuje své vlastní
čtení schématu děděním z této třídy.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseSchemaReader(ABC):
    """
    Abstraktní základní třída pro čtenáře databázových schémat.

    Tato třída definuje rozhraní, které musí implementovat všechny konkrétní
    čtečky schémat pro různé databázové backendy.
    """

    @abstractmethod
    def load_schema(self) -> Dict[str, Any]:
        """
        Načte schéma databázové tabulky a vrátí JSON Schema strukturu.

        Tato metoda by měla:
        1. Připojit se k databázi
        2. Získat metadata o tabulce (názvy sloupců, typy, nullability)
        3. Mapovat databázové typy na JSON Schema typy
        4. Identifikovat auto-generated sloupce (SERIAL, IDENTITY, atd.)
        5. Vrátit JSON Schema ve formátu {"type": "object", "properties": {...}, "required": [...]}

        Returns:
            Slovník reprezentující JSON Schema pro tabulku.
            Formát: {"type": "object", "properties": {...}, "required": [...]}

        Raises:
            TalosForgeException: Pokud se nepodaří načíst schéma.

        Example:
            >>> reader = PostgresSchemaReader(dsn="...", schema="public", table="users")
            >>> schema = reader.load_schema()
            >>> print(schema["properties"]["email"])
            {'type': 'string', 'format': 'email'}
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """
        Zavře databázové připojení, pokud je otevřené.

        Tato metoda by měla bezpečně ukončit připojení k databázi
        a uvolnit všechny přidružené zdroje.

        Example:
            >>> reader = PostgresSchemaReader(...)
            >>> try:
            ...     schema = reader.load_schema()
            ... finally:
            ...     reader.close()
        """
        raise NotImplementedError
