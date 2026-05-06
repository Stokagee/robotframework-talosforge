"""
Konfigurační modul pro TalosForge.

Podporuje načítání konfigurace z:
1. YAML souboru (talosforge.yml nebo ~/.talosforge/config.yml)
2. Environment variables (fallback)
3. Default hodnoty
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .exceptions import TalosForgeException

logger = logging.getLogger(__name__)

# Default hodnoty
DEFAULT_LOCALE = "cs_CZ"
DEFAULT_OPENAI_MODEL = "gpt-3.5-turbo"
DEFAULT_ZHIPU_MODEL = "glm-4"
DEFAULT_AI_PROVIDER = "auto"
DEFAULT_CACHE_TTL = 3600
DEFAULT_GPS_REGION = "EU"  # Výchozí = Evropa (lat 36-71, lng -25 až 45)

# Cesty ke konfiguračnímu souboru
CONFIG_PATHS = [
    Path("talosforge.yml"),
    Path.home() / ".talosforge" / "config.yml",
]


def ensure_default_config() -> Path:
    """
    Zajistí existenci default konfiguračního souboru.

    Pokud ~/.talosforge/config.yml neexistuje, vytvoří ho
    z config.example.yml šablony.

    Returns:
        Cesta ke konfiguračnímu souboru.
    """
    config_dir = Path.home() / ".talosforge"
    config_path = config_dir / "config.yml"

    if not config_path.exists():
        config_dir.mkdir(parents=True, exist_ok=True)

        # Najít config.example.yml v balíčku
        try:
            import TalosForge as tf_package
            package_dir = Path(tf_package.__file__).parent
            example_path = package_dir / "config.example.yml"

            if example_path.exists():
                shutil.copy(example_path, config_path)
                logger.info(f"Vytvořen default config: {config_path}")
            else:
                # Vytvořit minimal config
                default_content = """talosforge:
  locale: cs_CZ
  ai:
    provider: auto
    openai:
      model: gpt-3.5-turbo
    zhipu:
      model: glm-4
  cache:
    enabled: true
    ttl: 3600
"""
                config_path.write_text(default_content, encoding="utf-8")
                logger.info(f"Vytvořen minimal config: {config_path}")
        except Exception as e:
            # Fallback - vytvořit minimal config
            default_content = """talosforge:
  locale: cs_CZ
  ai:
    provider: auto
    openai:
      model: gpt-3.5-turbo
    zhipu:
      model: glm-4
  cache:
    enabled: true
    ttl: 3600
"""
            config_path.write_text(default_content, encoding="utf-8")
            logger.info(f"Vytvořen minimal config (fallback): {config_path}")

    return config_path


class Config:
    """Správa konfigurace TalosForge."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Inicializace konfigurace.

        Args:
            config_path: Volitelná cesta ke konfiguračnímu souboru.
                         Pokud není zadána, hledají se výchozí cesty.
        """
        self._config: Dict[str, Any] = {}
        self._load_config(config_path)

    def _load_config(self, config_path: Optional[Path] = None) -> None:
        """Načtení konfigurace ze souboru a environment variables."""
        # Načtení ze souboru
        if config_path and config_path.exists():
            self._load_from_file(config_path)
        else:
            self._try_default_paths()

        # Fallback na environment variables a defaults
        self._apply_env_overrides()
        self._apply_defaults()

    def _load_from_file(self, path: Path) -> None:
        """Načtení YAML konfiguračního souboru."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
                # Extrakce pouze talosforge sekce pokud existuje
                if isinstance(content, dict) and "talosforge" in content:
                    self._config = content["talosforge"]
                elif content:
                    self._config = content
        except Exception as e:
            raise TalosForgeException(f"Chyba při načítání konfigurace z {path}: {e}")

    def _try_default_paths(self) -> None:
        """Zkusí načíst konfiguraci z výchozích cest."""
        for path in CONFIG_PATHS:
            if path.exists():
                self._load_from_file(path)
                break

    def _apply_env_overrides(self) -> None:
        """Přečte environment variables a přepíše hodnoty."""
        # Locale
        if "TAOSFORGE_LOCALE" in os.environ:
            self._set_nested("locale", os.getenv("TAOSFORGE_LOCALE"))

        # AI provider
        if "TAOSFORGE_AI_PROVIDER" in os.environ:
            self._set_nested("ai.provider", os.getenv("TAOSFORGE_AI_PROVIDER"))

        # OpenAI
        if "OPENAI_API_KEY" in os.environ:
            self._set_nested("ai.openai.api_key", os.getenv("OPENAI_API_KEY"))
        if "TAOSFORGE_OPENAI_MODEL" in os.environ:
            self._set_nested("ai.openai.model", os.getenv("TAOSFORGE_OPENAI_MODEL"))

        # Zhipu
        if "ZHIPU_API_KEY" in os.environ:
            self._set_nested("ai.zhipu.api_key", os.getenv("ZHIPU_API_KEY"))
        if "TAOSFORGE_ZHIPU_MODEL" in os.environ:
            self._set_nested("ai.zhipu.model", os.getenv("TAOSFORGE_ZHIPU_MODEL"))

        # GPS Region
        if "TAOSFORGE_GPS_REGION" in os.environ:
            self._set_nested("gps_region", os.getenv("TAOSFORGE_GPS_REGION"))

    def _apply_defaults(self) -> None:
        """Aplikuje default hodnoty."""
        self._config.setdefault("locale", DEFAULT_LOCALE)
        self._config.setdefault("ai", {})
        self._config["ai"].setdefault("provider", DEFAULT_AI_PROVIDER)
        self._config["ai"].setdefault("openai", {})
        self._config["ai"]["openai"].setdefault("api_key", "")
        self._config["ai"]["openai"].setdefault("model", DEFAULT_OPENAI_MODEL)
        self._config["ai"].setdefault("zhipu", {})
        self._config["ai"]["zhipu"].setdefault("api_key", "")
        self._config["ai"]["zhipu"].setdefault("model", DEFAULT_ZHIPU_MODEL)
        self._config.setdefault("cache", {})
        self._config["cache"].setdefault("enabled", True)
        self._config["cache"].setdefault("ttl", DEFAULT_CACHE_TTL)
        self._config.setdefault("gps_region", DEFAULT_GPS_REGION)

    def _set_nested(self, key: str, value: Any) -> None:
        """Nastaví hodnotu v vnořeném slovníku pomocí tečkové notace."""
        keys = key.split(".")
        current = self._config
        for k in keys[:-1]:
            current = current.setdefault(k, {})
        current[keys[-1]] = value

    def _resolve_env_var(self, value: str) -> str:
        """Vyřeší environment variable reference ve formátu ${VAR_NAME}."""
        if value is None:
            return ""  # Ošetřit None hodnotu
        if value and isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            return os.getenv(env_var, "")
        return value

    # Vlastnosti pro přístup k konfiguraci (zpětná kompatibilita)

    @property
    def locale(self) -> str:
        return self._config.get("locale", DEFAULT_LOCALE)

    @property
    def ai_provider(self) -> str:
        return self._config.get("ai", {}).get("provider", DEFAULT_AI_PROVIDER)

    @property
    def openai_api_key(self) -> str:
        key = self._config.get("ai", {}).get("openai", {}).get("api_key", "")
        return self._resolve_env_var(key)

    @property
    def openai_model(self) -> str:
        return self._config.get("ai", {}).get("openai", {}).get("model", DEFAULT_OPENAI_MODEL)

    @property
    def zhipu_api_key(self) -> str:
        key = self._config.get("ai", {}).get("zhipu", {}).get("api_key", "")
        return self._resolve_env_var(key)

    @property
    def zhipu_model(self) -> str:
        return self._config.get("ai", {}).get("zhipu", {}).get("model", DEFAULT_ZHIPU_MODEL)

    @property
    def cache_enabled(self) -> bool:
        return self._config.get("cache", {}).get("enabled", True)

    @property
    def cache_ttl(self) -> int:
        return self._config.get("cache", {}).get("ttl", DEFAULT_CACHE_TTL)

    @property
    def gps_region(self) -> Optional[str]:
        """GPS region pro generování souřadnic (CZ, US, EU nebo 'global' pro původní chování)."""
        return self._config.get("gps_region", DEFAULT_GPS_REGION)


# Globální instance konfigurace
_config: Optional[Config] = None


def init_config(config_path: Optional[Path] = None) -> Config:
    """Inicializuje globální konfiguraci."""
    global _config
    _config = Config(config_path)
    return _config


def get_config() -> Config:
    """Vrátí globální konfiguraci."""
    global _config
    if _config is None:
        _config = Config()
    return _config


# Zpětná kompatibilita - export jako globální proměnné
FAKER_LOCALE = DEFAULT_LOCALE
AI_PROVIDER = DEFAULT_AI_PROVIDER
OPENAI_API_KEY = ""
DEFAULT_OPENAI_MODEL_NAME = DEFAULT_OPENAI_MODEL  # Přejmenováno pro konzistenci
ZHIPU_API_KEY = ""
DEFAULT_ZHIPU_MODEL_NAME = DEFAULT_ZHIPU_MODEL  # Přejmenováno pro konzistenci


def get_active_ai_provider() -> Optional[str]:
    """
    Vrátí název aktivního AI providera.

    Priorita:
    1. Respektuje explicitní nastavení 'provider' z configu (STRIKTNĚ)
    2. Pokud je 'provider: auto', používá automatickou detekci

    STRIKTNÍ CHOVÁNÍ:
    - provider: openai → POUZE OpenAI (když nemá klíč → None)
    - provider: zhipu → POUZE Zhipu (když nemá klíč → None)
    - provider: auto → zkusit OpenAI, pak Zhipu

    Returns:
        Název AI providera ("openai", "zhipu") nebo None.

    Example:
        >>> provider = get_active_ai_provider()
        >>> if provider:
        ...     print(f"Using AI provider: {provider}")
    """
    config = get_config()

    # Získat nastavený provider z configu
    preferred_provider = config.ai_provider

    # STRIKTNÍ REŽIM: Pokud je nastaven konkrétní provider, použít HO
    if preferred_provider == "openai":
        return "openai" if config.openai_api_key else None
    elif preferred_provider == "zhipu":
        return "zhipu" if config.zhipu_api_key else None
    # preferred_provider == "auto" nebo None
    elif preferred_provider == "auto" or not preferred_provider:
        # Auto mode - zkusit OpenAI, pak Zhipu
        if config.openai_api_key:
            return "openai"
        if config.zhipu_api_key:
            return "zhipu"

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
    return get_active_ai_provider() is not None


# Aktualizace globálních proměnných pro zpětnou kompatibilitu
def _update_globals() -> None:
    """Aktualizuje globální proměnné z konfigurace."""
    global FAKER_LOCALE, AI_PROVIDER, OPENAI_API_KEY, ZHIPU_API_KEY
    global DEFAULT_OPENAI_MODEL_NAME, DEFAULT_ZHIPU_MODEL_NAME

    config = get_config()
    FAKER_LOCALE = config.locale
    AI_PROVIDER = config.ai_provider
    OPENAI_API_KEY = config.openai_api_key
    DEFAULT_OPENAI_MODEL_NAME = config.openai_model
    ZHIPU_API_KEY = config.zhipu_api_key
    DEFAULT_ZHIPU_MODEL_NAME = config.zhipu_model


# Exporty pro zpětnou kompatibilitu
# Tyto konstanty jsou používány v ai_generator.py
DEFAULT_OPENAI_MODEL = DEFAULT_OPENAI_MODEL_NAME
DEFAULT_ZHIPU_MODEL = DEFAULT_ZHIPU_MODEL_NAME
