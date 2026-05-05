Změny chování v TalosForge
==========================

Tento dokument obsahuje seznam změn chování, které mohou ovlivnit existující kód.

Verze 0.3.0 (2025-02-01)
-------------------------

Pole ``example`` je ignorováno
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Změna:** Pole ``example`` (jednotné číslo) v JSON Schema/OpenAPI je nyní ignorováno.

**Důvod:** Statické hodnoty z ``example`` byly proti účelu knihovny - generovat různorodá testovací data.

**Ovlivněné kódy:**

.. code-block:: json

    // Toto schéma nyní ignoruje "example"
    {"type": "string", "example": "static_value"}

**Řešení:**

1. Použijte ``examples`` (množné číslo):

.. code-block:: json

    {"type": "string", "examples": ["value1", "value2", "value3"]}

2. Použijte ``enum``:

.. code-block:: json

    {"type": "string", "enum": ["value1", "value2"]}

3. Nechte Faker generovat (doporučeno):

.. code-block:: json

    {"type": "string", "format": "email"}

**Nová priorita zpracování:**

1. ``enum`` → náhodný výběr
2. ``examples`` → náhodný výběr
3. ``example`` → **ignorováno**
4. ``AI`` → AI generování (pokud ``use_ai=True``)
5. ``Faker`` → generování podle typu

.. seealso:: :doc:`migracni_pirucka`
.. seealso:: `README.md - Priorita zpracování schématu <https://github.com/yourusername/TalosForge#priorita-zpracování-schématu>`_
