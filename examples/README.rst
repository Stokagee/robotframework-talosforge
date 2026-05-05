TalosForge Examples
===================

Tato složka obsahuje reálné ukázky použití TalosForge v různých scénářích.

Obsah
-----

Robot Framework soubory:

* **api_testing.robot** - Ukázky integrace s RequestsLibrary pro API testování
* **ui_testing.robot** - Ukázky integrace s Browser library pro UI testování
* **ai_generation.robot** - Ukázky AI generování pro složité scénáře

Složka schemas/:

* **user.json** - Základní uživatelské schéma
* **login.json** - Přihlašovací formulář
* **registration.json** - Registrační formulář
* **user_profile.json** - Uživatelský profil
* **post.json** - Blog post s uživatelem
* **article.json** - Článek s description (pro AI)
* **complex_pattern.json** - Složité regex patterny (pro AI)
* **oneof_anyof.json** - oneOf/anyOf konstrukce (pro AI)
* **czech_specific.json** - České specifické formáty (pro AI)

Jak spustit
-----------

Základní spuštění (vyžaduje nainstalovaný Robot Framework):

.. code-block:: bash

    # Spustit vybraný soubor
    robot --outputdir results/api api_testing.robot
    robot --outputdir results/ui ui_testing.robot
    robot --outputdir results/ai ai_generation.robot

    # Spustit všechny
    robot --outputdir results --exclude skip *.robot

S AI podporou:

.. code-block:: bash

    # Nastavit API klíč (Linux/Mac)
    export OPENAI_API_KEY=sk-your-key-here

    # Nastavit API klíč (Windows)
    set OPENAI_API_KEY=sk-your-key-here

    # Spustit s AI
    robot --outputdir results/ai --variable USE_AI:TRUE ai_generation.robot

Předpoklady
-----------

* Python 3.11+
* Robot Framework 7.0+
* TalosForge nainstalovaný v development módu:

.. code-block:: bash

    cd ..
    pip install -e .

Pro AI ukázky navíc:

* OpenAI API klíč nastavený v ``OPENAI_API_KEY``

API Testing (api_testing.robot)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ukazuje integraci s RequestsLibrary:

* Generování dat pro API požadavky
* Odesílání dat na reálná API
* Validace odpovědí
* Generování více záznamů najednou
* Práce s OpenAPI schématy

UI Testing (ui_testing.robot)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ukazuje integraci s Browser library:

* Generování formulářových dat (target=ui)
* Porovnání target=api vs target=ui
* Generování pro různé typy formulářů
* Hromadné generování formulářů

AI Generation (ai_generation.robot)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ukazuje AI generování pro složité případy:

* Schema s description field
* Složité regex patterny
* oneOf/anyOf konstrukce
* České specifické formáty
* Srovnání AI vs Faker

Poznámky
------

* Všechny .robot soubory obsahují komentáře vysvětlující každý krok
* Schémata v schemas/ jsou připravena k okamžitému použití
* Pro produkční použití upravte BASE_URL a další konstanty

Další zdroje
------------

* :doc:`../installation` - Instalace TalosForge
* :doc:`../ai_integration` - Detailní průvodce AI integrací
* :doc:`../configuration` - Konfigurace a nastavení
* :doc:`../keywords` - Reference keywords
