"""
Vlastní výjimky pro TalosForge.

Tento modul definuje základní výjimky používané v knihovně TalosForge.
"""


class TalosForgeException(Exception):
    """
    Základní výjimka pro TalosForge.

    Všechny výjimky v knihovně TalosForge dědí od této třídy.
    Umožňuje uživatelům knihovny jednoduše zachytit jakoukoliv chybu
    specifickou pro TalosForge pomocí jediného except bloku.

    Example:
        try:
            data = talosforge.generate_data_from_schema(...)
        except TalosForgeException as e:
            print(f"Chyba TalosForge: {e}")
    """

    pass
