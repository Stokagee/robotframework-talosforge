"""
Logovací modul pro TalosForge.

Tento modul poskytuje centralizované logování s barevným výstupem
a integrací s Robot Framework.
"""

import logging
import sys

from colorama import Fore, Style, init

# Inicializovat colorama (jen jednou)
init(autoreset=True)


def _supports_color() -> bool:
    """
    Detekuje zda terminál podporuje barvy.

    Returns:
        True pokud je TTY terminal, jinak False.
    """
    return sys.stdout.isatty()


def _colorize(msg: str, level: str) -> str:
    """
    Přidá barvu k zprávě podle levelu.

    Args:
        msg: Zpráva k obarvení.
        level: Log level ("WARNING" nebo "ERROR").

    Returns:
        Obarvená zpráva nebo původní zpráva pokud barvy nejsou podporovány.
    """
    if not _supports_color():
        return msg

    colors = {
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
    }
    color = colors.get(level, '')
    return f"{color}{msg}{Style.RESET_ALL}"


def _log_to_rf(msg: str, level: str) -> None:
    """
    Loguje zprávu do Robot Framework.

    Args:
        msg: Zpráva k logování.
        level: Log level ("WARNING" nebo "ERROR").
    """
    try:
        from robot.api import logger as rf_logger
        from robot.libraries.BuiltIn import BuiltIn

        # Console output s barvami
        BuiltIn().log_to_console(_colorize(f"[{level}] {msg}", level))

        # Log do RF logu
        if level == "WARNING":
            rf_logger.warn(msg)
        else:
            rf_logger.error(msg)
    except Exception:
        # Není v RF contextu, ignorovat
        pass


def log_warning(msg: str) -> None:
    """
    Loguje WARNING zprávu.

    Zpráva se loguje:
    - Do Robot Framework (log.html + console)
    - Na stdout s barvami

    Args:
        msg: Zpráva k logování.
    """
    _log_to_rf(msg, "WARNING")
    print(_colorize(f"[WARNING] {msg}", "WARNING"), flush=True)


def log_error(msg: str) -> None:
    """
    Loguje ERROR zprávu.

    Zpráva se loguje:
    - Do Robot Framework (log.html + console)
    - Na stdout s barvami

    Args:
        msg: Zpráva k logování.
    """
    _log_to_rf(msg, "ERROR")
    print(_colorize(f"[ERROR] {msg}", "ERROR"), flush=True)


def setup_logging(level: int = logging.WARNING) -> None:
    """
    Nastaví Python logging.

    Args:
        level: Logging level (default: WARNING).
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout  # Logovat do stdout pro lepší testování
    )
