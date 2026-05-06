"""
Global fixtures for TalosForge tests.

This file provides shared fixtures that apply to all tests.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

import TalosForge.core.config as config_module


@pytest.fixture(autouse=True)
def reset_global_state(monkeypatch, tmp_path):
    """
    Reset global state before each test.

    This fixture ensures that tests run in isolation by:
    1. Resetting the global config module
    2. Mocking CONFIG_PATHS to point to empty directory
    3. Removing environment variables that could affect tests
    """
    # Reset globální konfigurace
    config_module._config = None

    # Use tmp_path as the only config search path (empty directory)
    monkeypatch.setattr(config_module, 'CONFIG_PATHS', [tmp_path / "nonexistent.yml"])

    # Odstranit environment variables které by mohly ovlivnit testy
    monkeypatch.delenv("TAOSFORGE_LOCALE", raising=False)
    monkeypatch.delenv("TAOSFORGE_OPENAI_MODEL", raising=False)
    monkeypatch.delenv("TAOSFORGE_AI_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)

    yield

    config_module._config = None
