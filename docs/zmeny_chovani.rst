Změny chování v TalosForge
==========================

Tento dokument obsahuje seznam změn chování, které mohou ovlivnit existující kód.

Verze 0.4.0 (2026-05-05)
-------------------------

Nový keyword ``Validate Data Against Schema``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Změna:** Knihovna nově nabízí třetí keyword pro validaci dat proti JSON Schema / OpenAPI 3.0 response schématu. Není to breaking change — existující kód funguje beze změny.

Detaily viz :ref:`Validate Data Against Schema <keyword-validate-data-against-schema>`.

Strict mode validace je vždy zapnutý a není parametrizovatelný — extra pole, chybějící ``required`` pole, nesoulad typu/formátu/rozsahu vyhodí ``DataValidationError``. Tato volba je úmyslná. Více v :ref:`sekci o strict modu <validate-strict-mode>`.

Nový parametr ``method`` v ``Generate Data From Schema``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Změna:** Přidán samostatný parametr ``method`` pro HTTP metodu. Nemění výchozí chování — stará syntaxe ``endpoint=POST /users`` stále funguje.

Předchozí chování (≤0.3.x):

.. code-block:: robotframework

    ${data}=    Generate Data From Schema    endpoint=POST /users

Nové (doporučené) chování (0.4.0+):

.. code-block:: robotframework

    ${data}=    Generate Data From Schema    method=POST    endpoint=/users

**Důvod:** Robot Framework může mezeru v hodnotě argumentu rozdělit na dva argumenty. Samostatný parametr ``method=`` tomuto problému předchází.

Kontextové generování pro prefixová pole
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Změna:** Pole s prefixy (``customer_name``, ``user_email``, ``pickup_address``, atd.) nyní generují kontextově odpovídající data místo obecného textu. Implementováno přes nový ``UniversalFieldParser``.

Předchozí chování (≤0.3.x):

.. code-block:: python

    # Pole "customer_name" mohlo dostat obecný text z Fakeru
    {"customer_name": "Lorem ipsum dolor sit amet"}

Nové chování (0.4.0):

.. code-block:: python

    {"customer_name": "Renáta Pešková"}        # české jméno
    {"customer_phone": "+420 774 442 642"}     # telefon
    {"pickup_address": "Ke Břvům 829"}         # adresa

**Dopad na existující testy:** Pokud testy očekávaly konkrétní obecnou hodnotu pro prefixová pole, výsledek se změní. Asserty kontrolující jen typ (``isinstance``) zůstávají v platnosti.

**Detekce prefixů:** ``UniversalFieldParser`` pozná snake_case, camelCase, PascalCase i kebab-case a používá fuzzy matching (RapidFuzz) — toleruje překlepy a varianty názvů.

Unikátnost hodnot v polích typu ``tags`` / ``categories``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Změna:** Pole rozpoznaná jako kolekce (``tags``, ``categories``, ``items``, ``list``, ``array``) nyní automaticky obsahují **unikátní hodnoty** — duplicity jsou odstraněny.

Předchozí chování (≤0.3.x):

.. code-block:: python

    {"tags": ["vip", "vip", "urgent", "vip"]}  # mohly se opakovat

Nové chování (0.4.0):

.. code-block:: python

    {"tags": ["vip", "urgent", "premium"]}     # vždy unikátní

**Dopad:** Pokud schéma má ``minItems`` větší než počet dostupných unikátních hodnot v pool/enumu, výsledek může mít méně položek než ``minItems``. Pro deterministické testy zvažte rozšíření zdroje hodnot (``examples``/``enum``).

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
