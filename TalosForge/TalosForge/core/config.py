"""
Konfigurace TalosForge.

Tento modul poskytuje konfigurační nastavení pro TalosForge,
včetně locale pro Faker a nastavení AI providerů.
"""

import os


# Faker locale - výchozí je čeština
FAKER_LOCALE = os.getenv("TAOSFORGE_LOCALE", "cs_CZ")


# AI Provider konfigurace
AI_PROVIDER = os.getenv("TAOSFORGE_AI_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")


# Výchozí AI modely
DEFAULT_OPENAI_MODEL = os.getenv("TAOSFORGE_OPENAI_MODEL", "gpt-3.5-turbo")
DEFAULT_ZHIPU_MODEL = os.getenv("TAOSFORGE_ZHIPU_MODEL", "glm-4")


def get_active_ai_provider() -> str | None:
    """
    Vrátí název aktivního AI providera na základě dostupnosti API klíčů.

    Returns:
        Název AI providera ("openai", "zhipu") nebo None pokud není k dispozici žádný klíč.

    Example:
        >>> provider = get_active_ai_provider()
        >>> if provider:
        ...     print(f"Using AI provider: {provider}")
    """
    if ZHIPU_API_KEY:
        return "zhipu"
    if OPENAI_API_KEY:
        return "openai"
    return None


def is_ai_available() -> bool:
    """
    Zkontroluje, zda je k dispozici alespoň jeden AI provider.

    Returns:
        True pokud je k dispozici API klíč pro nějaký AI provider, jinak False.

    Example:
        >>> if is_ai_available():
        ...     print("AI generování je k dispozici")
    """
    return bool(OPENAI_API_KEY or ZHIPU_API_KEY)
