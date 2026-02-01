"""
Testy konfigurace TalosForge.
"""

import os

from TalosForge.core.config import (
    FAKER_LOCALE,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_ZHIPU_MODEL,
    get_active_ai_provider,
    is_ai_available,
)


def test_faker_locale():
    """Test výchozího Faker locale."""
    assert FAKER_LOCALE == "cs_CZ"


def test_ai_models():
    """Test výchozích AI modelů."""
    assert DEFAULT_OPENAI_MODEL == "gpt-3.5-turbo"
    assert DEFAULT_ZHIPU_MODEL == "glm-4"


def test_is_ai_available_no_keys():
    """Test is_ai_available bez API klíčů."""
    # Odstranit klíče pokud existují
    original_openai = os.environ.get("OPENAI_API_KEY")
    original_zhipu = os.environ.get("ZHIPU_API_KEY")

    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("ZHIPU_API_KEY", None)

    # Modul potřebuje reload pro změnu environment proměnných
    import importlib
    import talosforge.core.config as config_module
    importlib.reload(config_module)

    result = config_module.is_ai_available()
    assert result is False

    # Obnovit původní hodnoty
    if original_openai:
        os.environ["OPENAI_API_KEY"] = original_openai
    if original_zhipu:
        os.environ["ZHIPU_API_KEY"] = original_zhipu


def test_get_active_ai_provider():
    """Test get_active_ai_provider."""
    provider = get_active_ai_provider()
    # Může být None, "openai" nebo "zhipu"
    assert provider in [None, "openai", "zhipu"]
