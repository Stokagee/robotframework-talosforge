TalosForge - Dokumentace
=========================

Vítejte v dokumentaci knihovny **TalosForge** - schema-driven generátoru testovacích dat pro Robot Framework.

.. image:: https://img.shields.io/badge/python-3.11+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python 3.11+

.. image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
   :target: LICENSE
   :alt: License

.. image:: https://img.shields.io/badge/robotframework-7.0+-green.svg
   :target: https://robotframework.org/
   :alt: Robot Framework

.. image:: https://img.shields.io/badge/tests-60%20passed-success.svg
   :target: tests/
   :alt: Tests

Co je TalosForge?
-----------------

**TalosForge** je Python knihovna pro `Robot Framework <https://robotframework.org/>`_, která generuje testovací data na míru pomocí:

* **JSON Schema** - definujte strukturu dat
* **OpenAPI/Swagger** - použijte existující API dokumentaci
* **Faker** - extrémě rychlé generování (offline)
* **AI modely** - inteligentní generování složitých dat (OpenAI, Zhipu AI)

Hlavní výhody
--------------

* **Jeden zdroj pravdy** - Testovací data definujete ve schématu, ne v kódu
* **Hybridní přístup** - Faker pro rychlost, AI pro složité případy
* **Univerzální** - Kompatibilní s RequestsLibrary, Browser, DatabaseLibrary
* **Jednoduché API** - Pouze dva keywords: ``Load Schema`` a ``Generate Data From Schema``

Rychlý start
------------

Instalace
~~~~~~~~~

.. code-block:: bash

    pip install TalosForge

Vytvořte JSON schéma
~~~~~~~~~~~~~~~~~~~~~~

**user_schema.json**:

.. code-block:: json

    {
      "type": "object",
      "properties": {
        "username": {"type": "string", "minLength": 5},
        "email": {"type": "string", "format": "email"},
        "age": {"type": "integer", "minimum": 18, "maximum": 99}
      },
      "required": ["username", "email"]
    }

Použití v Robot Framework
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Settings ***
    Library     TalosForge

    *** Test Cases ***
    Generate User Data
        ${user}=    Generate Data From Schema    schema_path=./user_schema.json
        Log    ${user}
        # Výstup: {'username': 'Jan Novák', 'email': 'jan.novak@example.cz', 'age': 25}

Obsah dokumentace
-----------------

* **Instalace a nastavení** - jak nainstalovat a nastavit TalosForge
* **Keywords** - detailní popis ``Load Schema`` a ``Generate Data From Schema``
* **AI Integrace** - kompletní průvodce AI generováním (OpenAI, Zhipu)
* **Konfigurace** - reference environment variables a nastavení
* **API Reference** - kompletní dokumentace tříd a metod

.. toctree::
    :maxdepth: 2
    :caption: Obsah:

    installation
    keywords
    ai_integration
    configuration
    api
    migracni_pirucka
    zmeny_chovani
    faq

.. IMPORTANT::
   Nová verze 0.3.0! Pole ``example`` je nyní ignorováno. Viz :doc:`migracni_pirucka`.

Indexy a vyhledávání
---------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
