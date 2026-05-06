"""
Testy konfigurace TalosForge.
"""

import os
from pathlib import Path

import pytest

import TalosForge.core.config as config_module
from TalosForge.core.config import (
    Config,
    DEFAULT_LOCALE,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_ZHIPU_MODEL,
    FAKER_LOCALE,
    get_active_ai_provider,
    get_config,
    init_config,
    is_ai_available,
)
from TalosForge.core.exceptions import TalosForgeException


def test_config_defaults():
    """Test default hodnot."""
    config = Config()
    assert config.locale == "cs_CZ"
    assert config.openai_model == "gpt-3.5-turbo"
    assert config.zhipu_model == "glm-4"
    assert config.ai_provider == "auto"  # Změněno z "openai" na "auto"
    assert config.cache_enabled is True
    assert config.cache_ttl == 3600


def test_config_from_file(tmp_path):
    """Test načtení ze souboru."""
    config_file = tmp_path / "config.yml"
    config_file.write_text(
        """
talosforge:
  locale: en_US
  ai:
    provider: zhipu
    openai:
      model: gpt-4
    zhipu:
      model: glm-4
  cache:
    enabled: false
    ttl: 7200
"""
    )
    config = Config(config_file)
    assert config.locale == "en_US"
    assert config.ai_provider == "zhipu"
    assert config.openai_model == "gpt-4"
    assert config.cache_enabled is False
    assert config.cache_ttl == 7200


def test_config_env_override(monkeypatch):
    """Test přepsání pomocí environment variables."""
    monkeypatch.setenv("TAOSFORGE_LOCALE", "en_US")
    monkeypatch.setenv("TAOSFORGE_OPENAI_MODEL", "gpt-4")
    monkeypatch.setenv("TAOSFORGE_AI_PROVIDER", "zhipu")

    config = Config()
    assert config.locale == "en_US"
    assert config.openai_model == "gpt-4"
    assert config.ai_provider == "zhipu"


def test_config_env_api_keys(monkeypatch):
    """Test API klíčů z environment variables."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai")
    monkeypatch.setenv("ZHIPU_API_KEY", "test-zhipu-key")

    config = Config()
    assert config.openai_api_key == "sk-test-openai"
    assert config.zhipu_api_key == "test-zhipu-key"


def test_config_env_var_reference(tmp_path, monkeypatch):
    """Test reference na environment variable v config souboru."""
    monkeypatch.setenv("MY_OPENAI_KEY", "sk-from-env")

    config_file = tmp_path / "config.yml"
    config_file.write_text(
        """
talosforge:
  ai:
    openai:
      api_key: ${MY_OPENAI_KEY}
"""
    )
    config = Config(config_file)
    assert config.openai_api_key == "sk-from-env"


def test_config_env_var_not_found(tmp_path):
    """Test reference na neexistující environment variable."""
    config_file = tmp_path / "config.yml"
    config_file.write_text(
        """
talosforge:
  ai:
    openai:
      api_key: ${NONEXISTENT_KEY}
"""
    )
    config = Config(config_file)
    assert config.openai_api_key == ""


def test_config_without_talosforge_key(tmp_path):
    """Test konfigurace bez talosforge klíče."""
    config_file = tmp_path / "config.yml"
    config_file.write_text(
        """
locale: sk_SK
ai:
  openai:
    model: gpt-4
"""
    )
    config = Config(config_file)
    assert config.locale == "sk_SK"
    assert config.openai_model == "gpt-4"


def test_get_active_ai_provider_with_openai(monkeypatch):
    """Test get_active_ai_provider s OpenAI klíčem."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai")
    # Reset config
    config_module._config = None

    provider = get_active_ai_provider()
    assert provider == "openai"


def test_get_active_ai_provider_with_zhipu(monkeypatch):
    """Test get_active_ai_provider se Zhipu klíčem."""
    monkeypatch.setenv("ZHIPU_API_KEY", "test-zhipu-key")
    # Reset config
    config_module._config = None

    provider = get_active_ai_provider()
    assert provider == "zhipu"


def test_get_active_ai_provider_none():
    """Test get_active_ai_provider bez klíčů."""
    provider = get_active_ai_provider()
    assert provider is None


def test_is_ai_available(monkeypatch):
    """Test is_ai_available."""
    # Bez klíčů
    assert is_ai_available() is False

    # S OpenAI klíčem
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    config_module._config = None
    assert is_ai_available() is True


def test_init_config(tmp_path):
    """Test init_config funkce."""
    config_file = tmp_path / "config.yml"
    config_file.write_text(
        """
talosforge:
  locale: de_DE
"""
    )

    config = init_config(config_file)
    assert config.locale == "de_DE"


def test_get_config_singleton():
    """Test že get_config vrací stejnou instanci."""
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2


def test_backward_compatibility_constants():
    """Test zpětné kompatibility globálních konstant."""
    assert DEFAULT_LOCALE == "cs_CZ"
    assert DEFAULT_OPENAI_MODEL == "gpt-3.5-turbo"
    assert DEFAULT_ZHIPU_MODEL == "glm-4"


def test_backward_compatibility_faker_locale():
    """Test FAKER_LOCALE globální proměnné."""
    assert FAKER_LOCALE == "cs_CZ"


def test_backward_compatibility_with_env(monkeypatch):
    """Test zpětné kompatibility s environment variables."""
    monkeypatch.setenv("TAOSFORGE_LOCALE", "en_US")

    # Reset a inicializace
    config_module._config = None
    init_config()

    # Import po inicializaci
    from TalosForge.core.config import _update_globals

    _update_globals()

    from TalosForge.core.config import FAKER_LOCALE as locale_after

    assert locale_after == "en_US"


def test_strict_provider_openai_without_key(tmp_path):
    """Test striktního chování: provider: openai bez klíče vrátí None."""
    config_file = tmp_path / "config.yml"
    config_file.write_text(
        """
talosforge:
  ai:
    provider: openai
    openai:
      api_key:
      model: gpt-4
"""
    )
    # Reset config
    config_module._config = None

    config = Config(config_file)
    assert config.ai_provider == "openai"
    assert config.openai_api_key == ""

    # Striktní chování - provider nemá klíč, takže None
    provider = get_active_ai_provider()
    assert provider is None


def test_strict_provider_zhipu_without_key(tmp_path):
    """Test striktního chování: provider: zhipu bez klíče vrátí None."""
    config_file = tmp_path / "config.yml"
    config_file.write_text(
        """
talosforge:
  ai:
    provider: zhipu
    zhipu:
      api_key:
      model: glm-4
"""
    )
    # Reset config
    config_module._config = None

    config = Config(config_file)
    assert config.ai_provider == "zhipu"
    assert config.zhipu_api_key == ""

    # Striktní chování - provider nemá klíč, takže None
    provider = get_active_ai_provider()
    assert provider is None


def test_strict_provider_openai_with_key(tmp_path, monkeypatch):
    """Test striktního chování: provider: openai s klíčem vrátí openai."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    config_file = tmp_path / "config.yml"
    config_file.write_text(
        """
talosforge:
  ai:
    provider: openai
"""
    )
    # Reset config
    config_module._config = None

    config = Config(config_file)
    assert config.ai_provider == "openai"
    assert config.openai_api_key == "sk-test-key"

    # Striktní chování - provider má klíč
    provider = get_active_ai_provider()
    assert provider == "openai"


def test_auto_mode_with_openai_key(tmp_path, monkeypatch):
    """Test auto mode: provider: auto s OpenAI klíčem vrátí openai."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    config_file = tmp_path / "config.yml"
    config_file.write_text(
        """
talosforge:
  ai:
    provider: auto
"""
    )
    # Reset config
    config_module._config = None

    provider = get_active_ai_provider()
    assert provider == "openai"


def test_auto_mode_with_zhipu_key_only(tmp_path, monkeypatch):
    """Test auto mode: provider: auto s pouze Zhipu klíčem vrátí zhipu."""
    monkeypatch.setenv("ZHIPU_API_KEY", "test-zhipu-key")

    config_file = tmp_path / "config.yml"
    config_file.write_text(
        """
talosforge:
  ai:
    provider: auto
"""
    )
    # Reset config
    config_module._config = None

    provider = get_active_ai_provider()
    assert provider == "zhipu"


def test_resolve_env_var_with_none(tmp_path):
    """Test že _resolve_env_var vrátí prázdný řetězec při None."""
    config_file = tmp_path / "config.yml"
    config_file.write_text(
        """
talosforge:
  ai:
    openai:
      api_key:
"""
    )
    config = Config(config_file)

    # Mělo by vrátit prázdný řetězec, ne None
    assert config.openai_api_key == ""
