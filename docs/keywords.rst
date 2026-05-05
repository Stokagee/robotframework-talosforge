Keywords - Referenční příručka
==================================

TalosForge poskytuje dva hlavní keywords pro Robot Framework. Tato kapitola obsahuje detailní popis každého keywordu včetně parametrů, příkladů použití a doporučených postupů.

.. contents::
    :local:
    :depth: 2

Load Schema
-----------

.. _keyword-load-schema:

**Účel**

Načte OpenAPI (Swagger) soubor do paměti pro rychlejší přístup a generování dat.

Tento keyword je určen pro práci s velkými OpenAPI specifikacemi, které obsahují stovky endpointů. Načtení do paměti zajišťuje, že při opakovaném generování dat pro různé endpointy nedochází k opakovanému parsování souboru.

**Syntaxe**

.. code-block:: robotframework

    Load Schema    swagger_path=<cesta>    [force_reload=False]

**Parametry**

``swagger_path`` (povinný)
    Cesta k lokálnímu OpenAPI (Swagger) souboru. Soubor může být ve formátu JSON nebo YAML.

    *Typ:* ``string``
    *Příklad:* ``./api.yaml``, ``./petstore.json``

``force_reload`` (volitelný)
    Pokud je ``True``, vynutí znovunačtení souboru, i když byl již načten do paměti. Pokud je ``False`` (výchozí), soubor se načte pouze při prvním volání nebo při změně souboru.

    *Typ:* ``bool``
    *Výchozí:* ``False``
    *Příklad:* ``${True}``

**Návratová hodnota**

Žádná (keyword vrací ``None``)

**Příklady použití**

.. _load-schema-basic:

Základní použití
~~~~~~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Test Cases ***
    Test With Large API
        Load Schema    swagger_path=./petstore.yaml
        ${pet}=    Generate Data From Schema    endpoint=POST /pet
        ${order}=    Generate Data From Schema    endpoint=POST /store/order

.. _load-schema-force-reload:

Znovuna načtení schématu
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Test Cases ***
    Test With Schema Refresh
        # První načtení
        Load Schema    swagger_path=./api.yaml
        # ... nějaké testy ...
        # Znovuna načtení (např. po změně schématu)
        Load Schema    swagger_path=./api.yaml    force_reload=${True}

**Důležité poznámky**

* **Formát souboru:** Podporované jsou JSON (``.json``) a YAML (``.yaml``, ``.yml``) soubory.
* **Velikost souboru:** Doporučuje se používat pro soubory s více než 10 endpointy. Pro menší soubory je efektivnější používat přímo cestu ke schématu.
* **Trvání v paměti:** Načtené schéma zůstává v paměti po celou dobu běhu testovací sady. Pokud potřebujete uvolnit paměť, použijte ``force_reload=True`` nebo restartujte testovací prostředí.
* **Extrakce endpointů:** TalosForge automaticky extrahuje schémata z ``requestBody`` pro všechny endpointy v OpenAPI specifikaci.

**Chyby**

* ``FileNotFoundError`` - Soubor neexistuje
* ``TalosForgeException`` - Neplatný JSON/YAML formát nebo poškozená OpenAPI specifikace

**Vizualizace**

.. code-block:: text

    ├── TalosForge (knihovna)
    │
    ├── Load Schema ← Načte OpenAPI soubor
    │   └── Extrahuje endpoint schémata
    │       ├── POST /users → schema1
    │       ├── GET /users → schema2
    │       └── PUT /users/{id} → schema3
    │
    └── Generate Data From Schema ← Používá načtená schémata

Generate Data From Schema
-------------------------

.. _keyword-generate-data-from-schema:

**Účel**

Generuje testovací data na základě poskytnutého schématu (JSON Schema nebo OpenAPI). Toto je hlavní a nejdůležitější keyword knihovny.

**Syntaxe**

.. code-block:: robotframework

    ${data}=    Generate Data From Schema    [source]    [target=api|ui]    [amount=1]    [use_ai=False]

**Zdroje dat**

Musí být specifikován **právě jeden** ze zdrojů:

``schema_path`` (volitelný)
    Cesta k lokálnímu JSON schématu.

    *Typ:* ``string``
    *Použití:* Pro vlastní, uživatelsky definované schémata
    *Příklad:* ``./user.json``, ``./login_form.json``

``endpoint`` (volitelný)
    Endpoint ve formátu ``METODA /cesta`` (např. ``POST /users``, ``GET /items/{id}``).

    *Typ:* ``string``
    *Použití:* Pro práci s načtenými OpenAPI specifikacemi
    *Vyžaduje:* Předchozí volání ``Load Schema``
    *Příklad:* ``POST /users``, ``GET /pet/findByStatus``

``openapi_url`` (volitelný)
    URL adresa online OpenAPI specifikace.

    *Typ:* ``string``
    *Použití:* Pro práci s online dostupnými API dokumentacemi
    *Vyžaduje:* ``endpoint`` (pro výběr konkrétního endpointu)
    *Příklad:* ``https://api.example.com/swagger.json``

**Parametry**

``target`` (volitelný)
    Formát výstupních dat.

    *Typ:* ``string``
    *Výchozí:* ``api``
    *Možnosti:*

    * ``api`` - Vrací data ve formátu vhodném pro API požadavky (čistý slovník/seznam)
    * ``ui`` - Vrací data ve formátu vhodném pro UI testování (klíče odpovídají názvům polí ve formuláři)

    *Příklad:* ``target=ui``, ``target=api``

``amount`` (volitelný)
    Počet generovaných záznamů.

    *Typ:* ``int``
    *Výchozí:* ``1``
    *Rozsah:* ``1`` a více

    *Příklad:* ``amount=5`` (vygeneruje 5 záznamů)

``use_ai`` (volitelný)
    Povolí použití AI modelů pro generování složitých dat.

    *Typ:* ``bool``
    *Výchozí:* ``False``
    *Dopad:* AI se používá pro složité případy (např. přítomnost ``description``, složité ``pattern``)

    *Příklad:* ``use_ai=True``

**Návratová hodnota**

* Pokud ``amount=1``: Vrací **jeden slovník** (``dict``)
* Pokud ``amount>1``: Vrací **seznam slovníků** (``list``)

**Příklady použití**

.. _generate-from-schema-path:

Generování z JSON schématu
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Test Cases ***
    Generate User From Schema
        ${user}=    Generate Data From Schema    schema_path=./user.json
        Log    Název: ${user}[username]
        Log    Email: ${user}[email]

.. _generate-from-openapi:

Generování z OpenAPI endpointu
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Settings ***
    Library     TalosForge
    Library     RequestsLibrary

    *** Test Cases ***
    Create User Via API
        # Načíst API specifikaci
        Load Schema    swagger_path=./api.yaml

        # Generovat data pro vytvoření uživatele
        ${payload}=    Generate Data From Schema    endpoint=POST /users

        # Odeslat požadavek
        Create Session    api    https://api.example.com
        ${response}=    POST On Session    api    /users    json=${payload}

        Status Should Be    ${response.status_code}    201

.. _generate-multiple-records:

Generování více záznamů
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Test Cases ***
    Generate Multiple Users
        ${users}=    Generate Data From Schema    endpoint=POST /users    amount=10

        # Pro každého uživatele vytvořit účet
        FOR    ${user}    IN    @{users}
            Create User    ${user}
        END

.. _generate-for-ui:

Generování pro UI testování
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Settings ***
    Library     TalosForge
    Library     Browser

    *** Test Cases ***
    Fill Registration Form
        ${form_data}=    Generate Data From Schema    schema_path=./registration.json    target=ui

        New Page    https://example.com/register
        Fill Text    id=username    ${form_data}[username]
        Fill Text    id=email    ${form_data}[email]
        Fill Text    id=password    ${form_data}[password]
        Click Button    css=button[type="submit"]

.. _generate-with-ai:

Generování s AI
~~~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Test Cases ***
    Generate Realistic Content
        ${article}=    Generate Data From Schema
        ...    schema_path=./blog_post.json
        ...    use_ai=True

        # Obsah bude vygenerován AI model jako smysluplný článek
        Log    ${article}[content]

**Detailní popis zdrojů**

.. _source-schema-path:

Zdroj: schema_path (JSON schéma)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Používá se pro vlastní, uživatelsky definované schémata. Ideální pro:

* Registrační formuláře
* Konfigurační soubory
* Specifické datové struktury (např. pro import)

**Vytvoření schématu:**

1. Vytvořte JSON soubor s JSON Schema definicí
2. Definujte strukturu (typy, povinná pole, omezení)
3. V testu uveďte cestu k tomuto souboru v ``schema_path``

**Příklad schématu:**

.. code-block:: json

    {
      "type": "object",
      "properties": {
        "first_name": {
          "type": "string",
          "minLength": 2
        },
        "last_name": {
          "type": "string",
          "minLength": 2
        },
        "email": {
          "type": "string",
          "format": "email"
        },
        "age": {
          "type": "integer",
          "minimum": 18,
          "maximum": 99
        }
      },
      "required": ["first_name", "last_name", "email"]
    }

.. _source-endpoint:

Zdroj: endpoint (OpenAPI)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Používá se pro práci s OpenAPI specifikacemi. Ideální pro:

* REST API testování
* Velké API s mnoha endpointy
* Situace, kdy máte k dispozici OpenAPI dokumentaci API

**Pracovní postup:**

1. Načtěte OpenAPI soubor pomocí ``Load Schema``
2. Použijte ``endpoint`` ve formátu ``METODA /cesta``
3. TalosForge automaticky najde odpovídající schéma v načtené specifikaci

**Formát endpointu:**

* Metoda HTTP velkými písmeny (např. ``POST``, ``GET``, ``PUT``, ``DELETE``)
* Mezera
* Cesta k endpointu (např. ``/users``, ``/users/{id}``, ``/api/v1/items``)

**Příklady endpointů:**

* ``POST /users`` - vytvoření nového uživatele
* ``GET /users/{id}`` - získání uživatele podle ID
* ``PUT /users/{id}`` - aktualizace uživatele
* ``DELETE /users/{id}`` - smazání uživatele

.. _source-openapi-url:

Zdroj: openapi_url (Online OpenAPI)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Používá se pro práci s online dostupnými OpenAPI specifikacemi. Ideální pro:

* Testování veřejných API
* Dynamické načítání aktuální dokumentace
* Situace, kdy nemůžete uložit specifikaci lokálně

**Pracovní postup:**

1. Zadejte ``openapi_url`` (URL k OpenAPI souboru)
2. Zadejte ``endpoint`` (který endpoint chcete použít)
3. TalosForge stáhne specifikaci z URL, extrahuje schéma a vygeneruje data

**Příklad:**

.. code-block:: robotframework

    ${data}=    Generate Data From Schema
    ...    openapi_url=https://petstore.swagger.io/v2/swagger.json
    ...    endpoint=POST /pet

**Upozornění:** Tato funkce vyžaduje aktivní internetové připojení.

**Parametr target**

.. _param-target-api:

target=api (API testování)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Výstupní formát pro API testování. Vrací data přesně podle definice ve schématu.

.. code-block:: json

    {
      "user_id": 123,
      "username": "jan.novak",
      "email": "jan@example.com"
    }

Použití: Odesílání jako JSON payload v HTTP požadavcích.

.. _param-target-ui:

target=ui (UI testování)
~~~~~~~~~~~~~~~~~~~~~~~~

Výstupní formát pro UI testování. Klíče odpovídají názvům polí ve formuláři.

.. code-block:: json

    {
      "username": "jan.novak",
      "email": "jan@example.com",
      "password": "SecretPass123"
    }

Použití: Vyplnění formulářových polí v Browser (Playwright/Selenium).

**Doporučené postupy**

.. _best-practices:

Performance~~~~~~~~~~~~

* Pro malé schémata (< 5 endpointů) používejte přímo ``schema_path``
* Pro velké OpenAPI soubory (> 10 endpointů) použijte ``Load Schema``
* ``openapi_url`` používejte pouze když není možné mít lokální kopii

.. _best-practices-required:

Povinná vs. nepovinná pole
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Pole v ``required`` budou vždy vygenerována
* Nepovinná pole se generují s ~70% pravděpodobností (Faker chování)
* Pro deterministické testy používejte ``required`` pro všechna důležitá pole

.. _best-practices-ai:

Kdy používat AI
~~~~~~~~~~~~~~~

* ``use_ai=True`` pouze pro složité případy:
  - Přítomnost ``description`` ve schématu
  - Složité regulární výrazy (``pattern`` delší než 20 znaků)
  - ``oneOf``/``anyOf``/``allOf`` konstrukce
* Pro běžné testy používejte Faker (rychlý a offline)

.. _best-practices-cache:

Mezipaměť URL
~~~~~~~~~~~~~

* Stažené OpenAPI specifikace z URL jsou automaticky cachovány (TTL: 1 hodina)
* Opakované volání stejné URL používají data z mezipaměti
* Pro vynucené aktualizace použijte nový URL parametr nebo restartujte test

.. _examples-tricks:

Tipy a triky
~~~~~~~~~~~~

**Získání názvů dostupných endpointů**

Pokud nevíte jaké endpointy jsou v OpenAPI specifikaci, podívejte se do logu:

.. code-block:: robotframework

    Load Schema    swagger_path=./api.yaml
    # V logu budou vypsány všechny nalezené endpointy

**Generování jednoho záznamu vs seznamu**

.. code-block:: robotframework

    # Jeden záznam (vrací dict)
    ${user}=    Generate Data From Schema    endpoint=POST /users

    # Seznam záznamů (vrací list)
    ${users}=    Generate Data From Schema    endpoint=POST /users    amount=5

**Využití v cyklech**

.. code-block:: robotframework

    FOR    ${i}    IN RANGE    ${10}
        ${user}=    Generate Data From Schema    schema_path=./user.json
        Log    Uživatel ${i}: ${user}[username]
    END

**Kombinace s Robot Framework keywords**

.. code-block:: robotframework

    *** Test Cases ***
    Comprehensive Test
        # Načtení API
        Load Schema    swagger_path=./api.yaml

        # Generování dat pro různé endpointy
        ${user}=    Generate Data From Schema    endpoint=POST /users
        ${item}=    Generate Data From Schema    endpoint=POST /items
        ${order}=    Generate Data From Schema    endpoint=POST /orders

        # Odeslání API požadavků
        Create User    ${user}
        Create Item    ${item}
        Create Order    ${order}

Související kapitoly
--------------------

* :doc:`installation` - Instalace a nastavení
* :doc:`api` - API reference
