Migrační příručka: Verze 0.2.x → 0.3.0
========================================

Tato příručka vás provede změnami mezi verzemi 0.2.x a 0.3.0.

Změna chování pole ``example``
-------------------------------

Pole ``example`` (jednotné číslo) v OpenAPI specifikacích je nyní **ignorováno**.

Předchozí chování (0.2.x):

.. code-block:: json

    {"type": "string", "example": "Jan Novák"}

Vždy vrátilo: ``"Jan Novák"`` (statická hodnota)

Nové chování (0.3.0):

.. code-block:: json

    {"type": "string", "example": "Jan Novák"}

Vrací: Náhodná česká jména z Fakeru (``"Petr Svoboda"``, ``"Jana Dvořáková"``, ...)

.. seealso:: :doc:`zmeny_chovani`

Jak migrovat
------------

Možnost 1: Použijte ``examples`` (množné číslo)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pokud potřebujete vybírat z konkrétních hodnot:

.. code-block:: json

    {"name": {"type": "string", "examples": ["Jan Novák", "Petr Svoboda", "Jana Dvořáková"]}}

Výsledek: Náhodný výběr ze seznamu.

Možnost 2: Použijte ``enum`` pro validační omezení
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {"status": {"type": "string", "enum": ["active", "inactive", "pending"]}}

Výsledek: Náhodný výběr z enum (nejvyšší priorita).

Možnost 3: Nechte Faker generovat
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Odstraňte ``example`` a nechte Faker generovat:

.. code-block:: json

    {"email": {"type": "string", "format": "email"}}

Výsledek: Náhodné validní emaily.

Aktualizace testů
-----------------

Testy ověřující konkrétní ``example`` hodnoty:

.. code-block:: python

    # Před (selže v 0.3.0):
    data = generate({"name": {"type": "string", "example": "Jan Novák"}})
    assert data["name"] == "Jan Novák"  # ❌ Nyní selže

    # Po:
    data = generate({"name": {"type": "string"}})
    assert isinstance(data["name"], str)  # ✓ Pouze ověření typu

.. seealso:: `Plná migrační příručka <https://github.com/yourusername/TalosForge/blob/main/MIGRATION.md>`_
