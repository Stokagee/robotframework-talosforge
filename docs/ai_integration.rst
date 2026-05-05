.. _ai_integration:

AI Integrace
============

Tento dokument popisuje jak používat AI modely pro generování složitých testovacích dat v TalosForge.

.. contents::
    :local:
    :depth: 2

Co je AI generování
-------------------

**TalosForge** používá hybridní přístup:

* **Faker** (výchozí) - extrémě rychlý, funguje offline
* **AI modely** - inteligentní generování složitých dat

AI se automaticky používá pro případy, které Faker neumí zpracovat:

* Přítomnost pole ``description`` v JSON schématu
* Složité regulární výrazy (pattern delší než 20 znaků)
* ``oneOf``/``anyOf``/``allOf`` konstrukce
* Specifické formáty (např. ``czech-id``, ``ssn``)

Podporovaní AI poskytovatelé
----------------------------

TalosForge podporuje dva AI poskytovatele:

OpenAI
~~~~~~

* **Model:** GPT-3.5-turbo (výchozí), lze změnit na GPT-4
* **Instalace:** ``pip install openai>=1.0``
* **API klíč:** ``OPENAI_API_KEY``

Zhipu AI
~~~~~~~~

* **Model:** GLM-4 (výchozí)
* **Instalace:** ``pip install zhipuai``
* **API klíč:** ``ZHIPU_API_KEY``

.. _ai-prioritization:

Priorita poskytovatelů
~~~~~~~~~~~~~~~~~~~~~~

Pokud jsou nastaveny obě API klíče, má **Zhipu prioritu**. Toto chování můžete změnit pomocí proměnné prostředí ``TAOSFORGE_AI_PROVIDER``.

Instalace a nastavení
---------------------

OpenAI
~~~~~~

.. code-block:: bash

    # Instalace knihovny
    pip install openai>=1.0

    # Nastavení API klíče (Linux/Mac)
    export OPENAI_API_KEY=sk-your-openai-api-key-here

    # Nastavení API klíče (Windows)
    set OPENAI_API_KEY=sk-your-openai-api-key-here

Zhipu AI
~~~~~~~~

.. code-block:: bash

    # Instalace knihovny
    pip install zhipuai

    # Nastavení API klíče (Linux/Mac)
    export ZHIPU_API_KEY=your-zhipu-api-key-here

    # Nastavení API klíče (Windows)
    set ZHIPU_API_KEY=your-zhipu-api-key-here

Výběr poskytovatele
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Explicitní výběr OpenAI
    export TAOSFORGE_AI_PROVIDER=openai

    # Explicitní výběr Zhipu
    export TAOSFORGE_AI_PROVIDER=zhipu

Výběr modelu
~~~~~~~~~~~~

.. code-block:: bash

    # OpenAI model (výchozí: gpt-3.5-turbo)
    export TAOSFORGE_OPENAI_MODEL=gpt-4

    # Zhipu model (výchozí: glm-4)
    export TAOSFORGE_ZHIPU_MODEL=glm-4-plus

.. _ai-when-triggered:

Kdy se AI spouští
-----------------

AI se spouští automaticky když je ``use_ai=True`` a schéma obsahuje jeden z následujících prvků:

description field
~~~~~~~~~~~~~~~~~

Pole ``description`` v JSON schématu:

.. code-block:: json

    {
      "type": "string",
      "description": "Generate a realistic Czech full name"
    }

AI použije description k vygenerování kontextově odpovídajících dat.

Složité regulární výrazy
~~~~~~~~~~~~~~~~~~~~~~~~

Pattern delší než 20 znaků:

.. code-block:: json

    {
      "type": "string",
      "pattern": "^[A-Z]{2}[0-9]{5}[A-Z]{10}[a-z]{20}$"
    }

Faker by neuměl vygenerovat data odpovídající tomuto složitému patternu.

oneOf/anyOf/allOf
~~~~~~~~~~~~~~~~~

Kompozitní schémata:

.. code-block:: json

    {
      "oneOf": [
        {"type": "string", "format": "email"},
        {"type": "string", "format": "uri"}
      ]
    }

AI vybere jednu z možností a vygeneruje odpovídající data.

Nepodporované formáty
~~~~~~~~~~~~~~~~~~~~~

Formáty které Faker neumí:

.. code-block:: json

    {
      "type": "string",
      "format": "czech-id"
    }

.. _ai-examples:

Příklady použití
----------------

Základní AI generování
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Settings ***
    Library     TalosForge

    *** Variables ***
    ${OPENAI_API_KEY}    sk-your-key-here

    *** Test Cases ***
    Generate With AI
        ${content}=    Generate Data From Schema
        ...    schema_path=./article.json
        ...    use_ai=True
        Log    ${content}

**article.json:**

.. code-block:: json

    {
      "type": "object",
      "properties": {
        "title": {
          "type": "string",
          "description": "Generate a catchy blog post title about technology"
        },
        "content": {
          "type": "string",
          "description": "Generate a 200-word blog post about the benefits of test automation",
          "minLength": 200
        }
      }
    }

Schema s description
~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "type": "object",
      "properties": {
        "full_name": {
          "type": "string",
          "description": "A realistic Czech full name"
        },
        "address": {
          "type": "string",
          "description": "A realistic Prague street address with postal code"
        }
      }
    }

Složité patterny
~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "type": "object",
      "properties": {
        "product_code": {
          "type": "string",
          "pattern": "^[A-Z]{3}[0-9]{6}[A-Z]{2}$",
          "description": "Product code in format: 3 letters, 6 digits, 2 letters"
        }
      }
    }

oneOf příklad
~~~~~~~~~~~~~

.. code-block:: json

    {
      "type": "object",
      "properties": {
        "contact": {
          "oneOf": [
            {
              "type": "string",
              "format": "email",
              "description": "Email address"
            },
            {
              "type": "string",
              "format": "phone",
              "description": "Phone number"
            }
          ]
        }
      }
    }

.. _ai-fallback:

Fallback chování
----------------

Pokud AI generování selže, TalosForge automaticky fallbackuje na Faker:

1. AI API není dostupné (žádný API klíč)
2. API request selže (timeout, rate limit, chyba)
3. AI vrátí neplatná data

Vždy se loguje varování, aby jste věděli že došlo k fallbacku.

.. code-block:: robotframework

    *** Test Cases ***
    Fallback Example
        # Pokud AI není dostupná, použije se Faker
        ${user}=    Generate Data From Schema
        ...    schema_path=./user.json
        ...    use_ai=True
        # V logu uvidíte: "AI unavailable, falling back to Faker"

.. _ai-costs:

Cost considerations
-------------------

AI generování je **zpoplatněno** podle ceníku poskytovatele:

* **OpenAI GPT-3.5-turbo:** ~$0.001-0.002 za 1K tokens
* **OpenAI GPT-4:** ~$0.03-0.06 za 1K tokens
* **Zhipu GLM-4:** Podporuje čínský jazyk, cenově výhodnější

**Doporučení:** Používejte AI pouze pro složité případy. Pro běžné testy stačí Faker.

Best practices
--------------

* **Používejte ``use_ai=True`` jen když potřebujete** - Faker je rychlejší a zdarma
* **Testujte lokálně s AI před nasazením do CI/CD** - ověřte že vše funguje
* **Monitorujte API náklady** - AI volání se mohou sčítat
* **Používejte popisy (description)** - čím lepší popis, tím lepší výsledky
* **Nastavte ``TAOSFORGE_AI_PROVIDER`` v CI/CD** - pro deterministické chování

.. code-block:: robotframework

    *** Settings ***
    Library     TalosForge

    *** Variables ***
    # Výběr providera pro deterministické testy
    ${TAOSFORGE_AI_PROVIDER}    openai

    *** Test Cases ***
    Production Ready Test
        # Tento test bude vždy používat OpenAI
        ${data}=    Generate Data From Schema
        ...    schema_path=./complex.json
        ...    use_ai=True

Související kapitoly
--------------------

* :doc:`installation` - Instalace AI providerů
* :doc:`configuration` - Konfigurace environment variables
* :doc:`keywords` - Detailní popis ``use_ai`` parametru
