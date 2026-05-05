.. _installation:

Instalace a nastavení
=======================

Tento dokument popisuje jak nainstalovat a nastavit TalosForge.

Požadavky na systém
---------------------

* **Python 3.11+** - TalosForge vyžaduje Python verze 3.11 nebo vyšší
* **Robot Framework 7.0+** - Kompatibilní s Robot Framework verze 7.0 a vyšší
* **pip** - Správce Python balíčků

Instalace
----------

Z PyPI
~~~~~~~

Nejjednodušší způsob instalace je z PyPI (Python Package Index):

.. code-block:: bash

    pip install TalosForge

Tento příkaz nainstaluje TalosForge a všechny závislosti.

Ze zdrojového kódu
~~~~~~~~~~~~~~~~~~~~~

Pokud chcete instalovat přímo ze zdrojového kódu:

.. code-block:: bash

    git clone https://github.com/yourusername/TalosForge.git
    cd TalosForge
    pip install -e .

Vývojářská instalace
~~~~~~~~~~~~~~~~~~~~

Pro vývoj potřebné závislosti:

.. code-block:: bash

    pip install -e ".[dev]"

Tím se nainstalují i nástroje pro vývoj (pytest, flake8, black).

Instalace AI providerů (volitelné)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pro podporu AI generování musíte nainstalovat příslušný balíček a nastavit API klíč.

**OpenAI:**

.. code-block:: bash

    pip install openai>=1.0
    export OPENAI_API_KEY=your_openai_api_key_here

**Zhipu AI:**

.. code-block:: bash

    pip install zhipuai
    export ZHIPU_API_KEY=your_zhipu_api_key_here

.. _installation-verification:

Ověření instalace
~~~~~~~~~~~~~~~~~

Ověřte instalaci spuštěním Python skriptu:

.. code-block:: python

    from talosforge import TalosForge
    t = TalosForge()
    print("TalosForge úspěšně nainstalován!")

Nebo v Robot Framework:

.. code-block:: robotframework

    *** Test Cases ***
    Installation Test
        Library     TalosForge
        Log    TalosForge úspěšně importován!

První použití
-------------

Po instalaci můžete TalosForge okamžitě použít ve svých testech:

1. Vytvořte JSON schéma (např. ``user_schema.json``)
2. V Robot Framework testu importujte knihovnu: ``Library     TalosForge``
3. Generujte data: ``${user}=    Generate Data From Schema    schema_path=./user_schema.json``

.. _installation-troubleshooting:

Řešení problémů
---------------

**Problém:** ``ModuleNotFoundError: No module named 'talosforge'``

**Řešení:** Ujistěte se, že instalujete ve správném Python prostředí. Zkuste:

.. code-block:: bash

    python --version  # Zkontrolujte verzi Python (musí být 3.11+)
    pip show TalosForge  # Zkontrolujte instalaci
    python -c "from talosforge import TalosForge"  # Test importu

**Problém:** Chyby při generování s AI

**Řešení:** Překontrolujte nastavení API klíčů:

.. code-block:: bash

    echo $OPENAI_API_KEY  # Zkontrolujte OpenAI klíč
    echo $ZHIPU_API_KEY   # Zkontrolujte Zhipu klíč

**Problém:** Výstup neodpovídá očekávánému formátu

**Žešení:** Ověřte správnost JSON schématu pomocí online validátoru:
https://www.jsonschemavalidator.com/

Další kroky
------------

Po úspěšné instalaci doporučujeme:

1. Prozkoumejte :ref:`keywords` pro detailní popis keywords
2. Zahrňte TalosForge do vašeho CI/CD pipeline

Nástroje pro vývoj
-------------------

Pokud chcete přispět do vývoje TalosForge, vizte:

* `GitHub Issues <https://github.com/yourusername/TalosForge/issues>`_
* `Pull Requests <https://github.com/yourusername/TalosForge/pulls>`_
* `CODE_OF_CONDUCT.md` (v repozitáři)

Další zdroje
------------

* `Robot Framework Documentation <https://robotframework.org/>`_
* `JSON Schema Specification <https://json-schema.org/>`_
* `OpenAPI Specification <https://swagger.io/specification/>`_
