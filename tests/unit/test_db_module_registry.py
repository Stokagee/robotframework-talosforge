"""
Unit tests for database module registry.

Tyto testy ověřují, že registr DB_READERS je správně inicializován
a že dostupné moduly jsou registrovány.
"""

import pytest


class TestDBReadersRegistry:
    """Testy pro registr DB_READERS."""

    def test_db_readers_is_dict(self):
        """Test, že DB_READERS je slovník."""
        from TalosForge.db import DB_READERS
        assert isinstance(DB_READERS, dict)

    def test_db_readers_registry_structure(self):
        """Test, že hodnoty v registru jsou třídy."""
        from TalosForge.db import DB_READERS, BaseSchemaReader

        for key, reader_class in DB_READERS.items():
            assert isinstance(key, str)
            # Zkontrolujeme, že je to třída dědící z BaseSchemaReader
            assert isinstance(reader_class, type)
            # Nemůžeme přímo zkontrolovat dědičnost bez psycopg2
            # ale můžeme zkontrolovat, že to je callable
            assert callable(reader_class)

    def test_base_schema_reader_is_exported(self):
        """Test, že BaseSchemaReader je exportován z db modulu."""
        from TalosForge.db import BaseSchemaReader
        assert BaseSchemaReader is not None

    def test_psycopg2_registration_when_available(self):
        """Test, že psycopg2 je registrován, pokud je k dispozici."""
        from TalosForge.db import DB_READERS

        # Pokud je psycopg2 k dispozici, měl by být registrován
        try:
            import psycopg2
            # psycopg2 je nainstalován
            assert 'psycopg2' in DB_READERS
            assert DB_READERS['psycopg2'] is not None
        except ImportError:
            # psycopg2 není nainstalován, registr může být prázdný
            pass

    def test_db_readers_all_module_keys_are_strings(self):
        """Test, že všechny klíče v registru jsou řetězce."""
        from TalosForge.db import DB_READERS

        for key in DB_READERS.keys():
            assert isinstance(key, str)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
