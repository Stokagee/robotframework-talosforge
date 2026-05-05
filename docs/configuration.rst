.. _configuration:

Konfigurace
============

Tento dokument popisuje všechny možnosti konfigurace TalosForge.

.. contents::
    :local:
    :depth: 2

Přehled konfiguračního systému
-------------------------------

TalosForge používá **environment-based konfiguraci**. Není třeba žádný konfigurační soubor (jako .env, .ini nebo YAML).

Veškeré nastavení se provádí pomocí:

* **Environment variables** - v shellu nebo CI/CD
* **Python os.environ** - v kódu před importem TalosForge
* **Robot Framework Variables** - v sekci ``*** Variables ***``

.. _config-env-vars:

Environment Variables
---------------------

TalosForge podporuje následující environment variables:

+---------------------------+-------------------+-------------------------------------------+
| Proměnná                  | Výchozí hodnota   | Popis                                     |
+===========================+===================+===========================================+
| ``TAOSFORGE_LOCALE``      | ``cs_CZ``         | Faker locale pro lokalizovaná data        |
+---------------------------+-------------------+-------------------------------------------+
| ``TAOSFORGE_AI_PROVIDER`` | ``openai``        | AI provider (``openai`` nebo ``zhipu``)   |
+---------------------------+-------------------+-------------------------------------------+
| ``OPENAI_API_KEY``        | ``""`` (prázdné)  | OpenAI API klíč                           |
+---------------------------+-------------------+-------------------------------------------+
| ``ZHIPU_API_KEY``         | ``""`` (prázdné)  | Zhipu AI API klíč                         |
+---------------------------+-------------------+-------------------------------------------+
| ``TAOSFORGE_OPENAI_MODEL``| ``gpt-3.5-turbo`` | OpenAI model                              |
+---------------------------+-------------------+-------------------------------------------+
| ``TAOSFORGE_ZHIPU_MODEL`` | ``glm-4``         | Zhipu AI model                            |
+---------------------------+-------------------+-------------------------------------------+

.. _config-locale:

Lokalizace
----------

TalosForge používá knihovnu Faker s výchozí českou lokalizací (``cs_CZ``).

Změna locale
~~~~~~~~~~~~

.. code-block:: bash

    # Linux/Mac
    export TAOSFORGE_LOCALE=en_US

    # Windows
    set TAOSFORGE_LOCALE=en_US

Podporované locales
~~~~~~~~~~~~~~~~~~~

Faker podporuje mnoho lokalizací. Mezi nejčastější patří:

* ``en_US`` - Angličtina (USA)
* ``de_DE`` - Němčina
* ``fr_FR`` - Francouzština
* ``cs_CZ`` - Čeština (výchozí)
* ``sk_SK`` - Slovenština
* ``pl_PL`` - Polština

Kompletní seznam viz `Faker documentation <https://faker.readthedocs.io/>`_.

Příklad v Robot Framework
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Variables ***
    ${TAOSFORGE_LOCALE}    en_US

    *** Test Cases ***
    Generate English Name
        ${user}=    Generate Data From Schema    schema_path=./user.json
        # Vygeneruje: John Doe místo Jan Novák

.. _config-ai-provider:

Výběr AI providera
------------------

Pokud máte nastavené obě API klíče, TalosForge automaticky vybere providera podle priority:

1. **Zhipu AI** (priorita)
2. **OpenAI** (fallback)

Ruční výběr
~~~~~~~~~~~

.. code-block:: bash

    # Vynutit OpenAI
    export TAOSFORGE_AI_PROVIDER=openai

    # Vynutit Zhipu
    export TAOSFORGE_AI_PROVIDER=zhipu

Detekce dostupnosti
~~~~~~~~~~~~~~~~~~~

TalosForge automaticky detekuje které AI providery jsou dostupní:

* Pokud ``OPENAI_API_KEY`` není prázdná → OpenAI je dostupný
* Pokud ``ZHIPU_API_KEY`` není prázdná → Zhipu je dostupný
* Pokud obě nejsou prázdné → používá se ``TAOSFORGE_AI_PROVIDER`` nebo Zhipu (priorita)

.. _config-model-selection:

Výběr AI modelu
---------------

Každý provider má svůj výchozí model:

* **OpenAI:** ``gpt-3.5-turbo`` (rychlý a levný)
* **Zhipu:** ``glm-4`` (podpora čínštiny)

Změna modelu
~~~~~~~~~~~~

.. code-block:: bash

    # OpenAI GPT-4 pro lepší kvalitu
    export TAOSFORGE_OPENAI_MODEL=gpt-4

    # OpenAI GPT-4o pro multimodální data
    export TAOSFORGE_OPENAI_MODEL=gpt-4o

    # Zhipu GLM-4 Plus
    export TAOSFORGE_ZHIPU_MODEL=glm-4-plus

.. _config-cache:

Mezipaměť (Cache)
-----------------

TalosForge automaticky cachuje stažené OpenAPI specifikace z URL.

Cache parametry
~~~~~~~~~~~~~~~

Cache je **hardcoded** v ``SchemaLoader`` třídě:

* ``use_cache=True`` - cache je zapnutá
* ``cache_ttl=3600`` - TTL je 1 hodina (3600 sekund)

Tyto parametry nelze měnit bez úpravy zdrojového kódu.

Cache v praxi
~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Test Cases ***
    Cache Example
        # První volání - stáhne z URL
        ${data1}=    Generate Data From Schema
        ...    openapi_url=https://api.example.com/swagger.json
        ...    endpoint=GET /users

        # Druhé volání do 1 hodiny - použije cache
        ${data2}=    Generate Data From Schema
        ...    openapi_url=https://api.example.com/swagger.json
        ...    endpoint=POST /users

.. _config-settings-section:

Sekce *** Settings *** v Robot Framework
-----------------------------------------

Kompletní ukázka konfigurace TalosForge v Robot Framework:

Základní nastavení
~~~~~~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Settings ***
    Documentation     TalosForge Test Suite
    Library            TalosForge

    *** Variables ***
    ${TAOSFORGE_LOCALE}    cs_CZ

    *** Test Cases ***
    Basic Example
        ${user}=    Generate Data From Schema    schema_path=./user.json
        Log    ${user}

S AI podporou
~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Settings ***
    Documentation     TalosForge AI Test Suite
    Library            TalosForge
    Library            RequestsLibrary
    Library            Collections

    Suite Setup        Log    Starting AI-powered tests
    Suite Teardown     Log    AI-powered tests completed

    *** Variables ***
    # API Configuration
    ${BASE_URL}           https://api.example.com

    # TalosForge Configuration
    ${OPENAI_API_KEY}     sk-your-openai-key-here
    ${TAOSFORGE_LOCALE}   en_US
    ${TAOSFORGE_AI_PROVIDER}    openai
    ${TAOSFORGE_OPENAI_MODEL}   gpt-3.5-turbo

    # Schema paths
    ${SCHEMA_PATH}        ${CURDIR}/schemas/user.json

    *** Test Cases ***
    Generate With AI
        [Documentation]    Generate realistic data using AI
        ${user}=    Generate Data From Schema
        ...    schema_path=${SCHEMA_PATH}
        ...    use_ai=True
        Log    Generated user: ${user}

    Send To API
        [Documentation]    Send generated data to API
        ${payload}=    Generate Data From Schema
        ...    schema_path=${SCHEMA_PATH}
        ...    use_ai=True

        Create Session    api    ${BASE_URL}
        ${response}=    POST On Session    api    /users    json=${payload}

        Status Should Be    201    ${response.status_code}

S více knihovnami
~~~~~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Settings ***
    Documentation     Comprehensive API Testing Suite
    ...               Demonstrates integration of TalosForge with other libraries

    Library            TalosForge
    Library            RequestsLibrary
    Library            Collections
    Library            String

    Suite Setup        Initialize Test Environment
    Suite Teardown     Cleanup Test Environment

    *** Variables ***
    # API Configuration
    ${BASE_URL}           https://petstore.swagger.io/v2
    ${API_SESSION}        petstore_api

    # TalosForge Configuration
    ${OPENAI_API_KEY}     %{OPENAI_API_KEY}    # Přečte z environment
    ${TAOSFORGE_LOCALE}   en_US
    ${USE_AI}             ${True}

    # Schema Configuration
    ${SWAGGER_PATH}       ${CURDIR}/schemas/petstore.yaml
    ${USER_SCHEMA}        ${CURDIR}/schemas/user.json

    *** Keywords ***
    Initialize Test Environment
        [Documentation]    Setup API session and load schemas
        Log    Initializing test environment...
        Log    API URL: ${BASE_URL}
        Log    Locale: ${TAOSFORGE_LOCALE}
        Log    AI enabled: ${USE_AI}

        Create Session    ${API_SESSION}    ${BASE_URL}
        Load Schema    swagger_path=${SWAGGER_PATH}

    Cleanup Test Environment
        [Documentation]    Cleanup after tests
        Delete All Sessions    ${API_SESSION}

    Generate And Create User
        [Arguments]    ${use_ai}=${False}
        [Documentation]    Generate user data and create user via API

        # Generate data
        ${user_data}=    Generate Data From Schema
        ...    schema_path=${USER_SCHEMA}
        ...    use_ai=${use_ai}

        Log    Generated user: ${user_data}

        # Send to API
        ${response}=    POST On Session
        ...    ${API_SESSION}
        ...    /user
        ...    json=${user_data}

        Status Should Be    200    ${response.status_code}
        RETURN    ${response}

    *** Test Cases ***
    Create User With Faker
        [Documentation]    Create user using Faker (fast, offline)
        [Tags]    faker    smoke
        ${response}=    Generate And Create User    use_ai=${False}
        Log    User created with ID: ${response.json()}[id]

    Create User With AI
        [Documentation]    Create user using AI (realistic data)
        [Tags]    ai    regression
        ${response}=    Generate And Create User    use_ai=${True}
        Log    User created with ID: ${response.json()}[id]

    Bulk Create Users
        [Documentation]    Create multiple users at once
        [Tags]    bulk    performance

        ${users}=    Generate Data From Schema
        ...    schema_path=${USER_SCHEMA}
        ...    amount=10
        ...    use_ai=${USE_AI}

        Log    Generated ${users.__len__()} users

        FOR    ${user}    IN    @{users}
            ${response}=    POST On Session
            ...    ${API_SESSION}
            ...    /user
            ...    json=${user}
            Status Should Be    200    ${response.status_code}
        END

.. _config-env-in-py:

Nastavení v Python kódu
-------------------------

Před importem TalosForge můžete nastavit environment variables v Pythonu:

.. code-block:: python

    import os

    # Nastavení před importem TalosForge
    os.environ["TAOSFORGE_LOCALE"] = "en_US"
    os.environ["OPENAI_API_KEY"] = "sk-your-key-here"
    os.environ["TAOSFORGE_AI_PROVIDER"] = "openai"

    # Import až po nastavení
    from talosforge import TalosForge

    forge = TalosForge()
    data = forge.generate_data_from_schema(schema_path="./user.json")
    print(data)

.. _config-ci-cd:

CI/CD konfigurace
-----------------

GitHub Actions
~~~~~~~~~~~~~~

.. code-block:: yaml

    name: Tests with TalosForge

    on: [push, pull_request]

    jobs:
      test:
        runs-on: ubuntu-latest
        env:
          TAOSFORGE_LOCALE: en_US
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          TAOSFORGE_AI_PROVIDER: openai

        steps:
          - uses: actions/checkout@v3
          - uses: actions/setup-python@v4
            with:
              python-version: '3.11'

          - name: Install dependencies
            run: |
              pip install -e .
              pip install openai>=1.0

          - name: Run Robot Framework tests
            run: |
              robot --outputdir results --variable USE_AI:true tests/

GitLab CI
~~~~~~~~~

.. code-block:: yaml

    test:
      image: python:3.11
      variables:
        TAOSFORGE_LOCALE: "en_US"
        OPENAI_API_KEY: "$OPENAI_API_KEY"
        TAOSFORGE_AI_PROVIDER: "openai"
      script:
        - pip install -e .
        - pip install openai>=1.0
        - robot --outputdir results tests/
      artifacts:
        paths:
          - results/

Související kapitoly
--------------------

* :doc:`installation` - Instalace AI providerů
* :doc:`ai_integration` - Detailní průvodce AI integrací
* :doc:`keywords` - Popis keywords a parametrů
