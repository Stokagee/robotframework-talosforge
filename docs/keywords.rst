Keywords - Referenční příručka
==================================

TalosForge poskytuje tři hlavní keywords pro Robot Framework. Tato kapitola obsahuje detailní popis každého keywordu včetně parametrů, příkladů použití a doporučených postupů.

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

    ${data}=    Generate Data From Schema    [source]    [method=]    [target=api|ui]    [amount=1]    [use_ai=False]

**Zdroje dat**

Musí být specifikován **právě jeden** ze zdrojů:

``schema_path`` (volitelný)
    Cesta k lokálnímu JSON schématu.

    *Typ:* ``string``
    *Použití:* Pro vlastní, uživatelsky definované schémata
    *Příklad:* ``./user.json``, ``./login_form.json``

``endpoint`` (volitelný)
    Cesta k endpointu. Lze zadat dvěma způsoby:

    * S parametrem ``method=`` jen jako cesta (např. ``/users``) — **doporučeno**
    * Bez ``method=`` ve formátu ``METODA /cesta`` (např. ``POST /users``) — pro zpětnou kompatibilitu

    *Typ:* ``string``
    *Použití:* Pro práci s načtenými OpenAPI specifikacemi
    *Vyžaduje:* Předchozí volání ``Load Schema`` (pokud není použito ``openapi_url``)
    *Příklad:* ``/users``, ``/pet/findByStatus``, ``POST /users``

``openapi_url`` (volitelný)
    URL adresa online OpenAPI specifikace.

    *Typ:* ``string``
    *Použití:* Pro práci s online dostupnými API dokumentacemi
    *Vyžaduje:* ``endpoint`` (pro výběr konkrétního endpointu)
    *Příklad:* ``https://api.example.com/swagger.json``

**Parametry**

``method`` (volitelný, *od verze 0.4.0*)
    HTTP metoda endpointu. **Preferovaný způsob** specifikace HTTP metody — vyhýbá se problémům s parsováním mezery v Robot Frameworku, kdy by Robot Framework rozdělil hodnotu ``POST /users`` na dva argumenty.

    *Typ:* ``string``
    *Použití:* Spolu s parametrem ``endpoint`` (cesta bez metody) nebo ``openapi_url``
    *Hodnoty:* ``GET``, ``POST``, ``PUT``, ``PATCH``, ``DELETE``, ``HEAD``, ``OPTIONS`` (case-insensitive)
    *Příklad:* ``method=POST``, ``method=GET``

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
2. Použijte ``endpoint`` (volitelně s parametrem ``method=``)
3. TalosForge automaticky najde odpovídající schéma v načtené specifikaci

**Formát endpointu:**

Od verze 0.4.0 jsou podporovány dvě syntaxe:

**Nová syntaxe (doporučeno)** — samostatný parametr ``method=`` a čistá cesta:

.. code-block:: robotframework

    ${data}=    Generate Data From Schema    method=POST    endpoint=/users

**Stará syntaxe (zpětná kompatibilita)** — metoda v hodnotě ``endpoint``:

.. code-block:: robotframework

    ${data}=    Generate Data From Schema    endpoint=POST /users

Stará syntaxe stále funguje, ale Robot Framework může mezeru chápat jako oddělovač argumentů u některých nastavení — preferuj proto novou syntaxi.

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

.. _keyword-validate-data-against-schema:

Validate Data Against Schema
----------------------------

*Od verze 0.4.0.*

**Účel**

Validuje data proti JSON Schema nebo OpenAPI 3.0 response schématu. Tento keyword je „opačnou stranou mince" k ``Generate Data From Schema`` — používá stejné typy zdrojů (lokální schéma, načtená OpenAPI specifikace, online OpenAPI URL), ale data nevytváří, nýbrž je kontroluje proti deklarovanému kontraktu.

Typické použití:

* Ověření odpovědi (response body) z reálného API proti OpenAPI specifikaci
* Kontrola, že vámi zkonstruovaný požadavek odpovídá schématu před odesláním
* Round-trip kontrolní smyčka: vygenerovaná data → odeslat na API → response validovat proti stejnému OpenAPI

**Syntaxe**

.. code-block:: robotframework

    Validate Data Against Schema    data=<data>    [source]    [method=]    [response_code=200]    [return_errors=False]

**Zdroje dat**

Musí být specifikován **právě jeden** ze zdrojů (stejně jako u ``Generate Data From Schema``):

``schema_path`` (volitelný)
    Cesta k lokálnímu JSON schématu.

    *Typ:* ``string``
    *Příklad:* ``./user.json``

``endpoint`` (volitelný)
    Cesta k endpointu z předem načtené OpenAPI specifikace. Lze kombinovat s ``method=`` (doporučeno) nebo zadat ve formátu ``METODA /cesta`` (zpětná kompatibilita).

    *Typ:* ``string``
    *Vyžaduje:* Předchozí volání ``Load Schema``, nebo souběžné použití s ``openapi_url``
    *Příklad:* ``/users``, ``POST /users``

``openapi_url`` (volitelný)
    URL adresa online OpenAPI specifikace.

    *Typ:* ``string``
    *Vyžaduje:* ``endpoint`` (a typicky ``method``)
    *Příklad:* ``https://api.example.com/openapi.yaml``

**Parametry**

``data`` (povinný)
    Data k validaci — typicky parsované tělo HTTP odpovědi (slovník nebo seznam).

    *Typ:* ``dict`` nebo ``list``

``method`` (volitelný)
    HTTP metoda endpointu. Stejné chování jako u ``Generate Data From Schema`` — preferovaný způsob specifikace HTTP metody.

    *Typ:* ``string``
    *Hodnoty:* ``GET``, ``POST``, ``PUT``, ``PATCH``, ``DELETE``, ``HEAD``, ``OPTIONS``
    *Příklad:* ``method=POST``

``response_code`` (volitelný)
    HTTP status code, jehož response schéma se má použít pro validaci. Používá se pouze u zdrojů ``endpoint`` a ``openapi_url``.

    *Typ:* ``int``
    *Výchozí:* ``200``
    *Příklad:* ``response_code=${201}``, ``response_code=${404}``

``return_errors`` (volitelný)
    Pokud je ``True``, keyword nehodí výjimku při neplatných datech, ale vrátí seznam chybových slovníků.

    *Typ:* ``bool``
    *Výchozí:* ``False``

**Návratová hodnota**

* ``return_errors=False`` (výchozí): vrací ``None`` při úspěchu; při neúspěchu vyhodí ``DataValidationError`` se zprávou obsahující všechny nalezené chyby.
* ``return_errors=True``: vrací **seznam chybových slovníků** (prázdný seznam = data validní). Každý slovník obsahuje pole:

  * ``path`` — cesta k poli ve stylu JSONPath (``$``, ``$.users[0].email`` apod.)
  * ``path_parts`` — cesta jako seznam segmentů
  * ``message`` — lidsky čitelný popis chyby
  * ``validator`` — typ porušeného omezení (``required``, ``format``, ``minimum``, ``additionalProperties``, ...)
  * ``validator_value`` — hodnota daného omezení ze schématu
  * ``instance`` — konkrétní hodnota, která neprošla

**Strict mode (vždy zapnutý)**

.. _validate-strict-mode:

Validace je **vždy ve striktním režimu** — toto chování není parametrizovatelné a je úmyslné. Konkrétně:

* Pole, které není deklarované ve schématu, vyhazuje chybu (``additionalProperties: false`` se automaticky aplikuje na **všechna** ``object`` schémata, včetně vnořených objektů a komponent dosažených přes ``$ref``)
* Chybějící ``required`` pole vyhazuje chybu
* Nesoulad typu, formátu (``email``, ``uuid``, ``int32``, ...), ``minLength``/``maxLength``, ``minimum``/``maximum``, ``enum`` apod. vyhazuje chybu

Pokud potřebujete permisivní validaci, validujte proti vlastnímu schématu, ve kterém ``additionalProperties`` výslovně dovolíte.

**Příklady použití**

.. _validate-from-schema-path:

Validace proti lokálnímu JSON schématu
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Settings ***
    Library     TalosForge

    *** Variables ***
    ${VALID_USER}      {"username": "honza123", "email": "honza@example.cz", "age": 25}
    ${INVALID_USER}    {"username": "x", "email": "not-email", "age": 200}

    *** Test Cases ***
    Validate Valid Data Passes
        ${data}=    Evaluate    ${VALID_USER}
        Validate Data Against Schema    data=${data}    schema_path=./user.json

    Validate Invalid Data Raises
        ${data}=    Evaluate    ${INVALID_USER}
        Run Keyword And Expect Error    *Validation failed*
        ...    Validate Data Against Schema    data=${data}    schema_path=./user.json

.. _validate-from-endpoint:

Validace proti response schématu z načtené OpenAPI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Test Cases ***
    Validate Loaded Endpoint Response Passes
        Load Schema    swagger_path=./api.yaml
        ${address}=    Create Dictionary    city=Praha    country=CZ
        ${data}=    Create Dictionary    id=${1}    name=Jan    address=${address}
        Validate Data Against Schema
        ...    data=${data}    method=POST    endpoint=/users    response_code=${201}

.. _validate-from-openapi-url:

Validace proti online OpenAPI specifikaci
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Test Cases ***
    Validate Against URL Spec Passes
        ${data}=    Create Dictionary    id=${1}    name=Item-Name
        Validate Data Against Schema
        ...    data=${data}    openapi_url=https://api.example.com/openapi.yaml
        ...    method=POST    endpoint=/items    response_code=${201}

Stažená specifikace je cachována (TTL 1 hodina) — opakovaná volání pro stejnou URL nezpůsobí další HTTP požadavek.

.. _validate-return-errors:

Získání chyb jako seznamu (return_errors)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: robotframework

    *** Test Cases ***
    Validate With Return Errors Returns List
        ${data}=    Evaluate    {"username": "x", "email": "not-email", "age": 200}
        ${errors}=    Validate Data Against Schema
        ...    data=${data}    schema_path=./user.json    return_errors=${True}
        Should Not Be Empty    ${errors}
        # Každá chyba má pole: path, message, validator, validator_value, instance

    Validate Empty Errors For Valid Data
        ${data}=    Evaluate    {"username": "honza123", "email": "honza@example.cz"}
        ${errors}=    Validate Data Against Schema
        ...    data=${data}    schema_path=./user.json    return_errors=${True}
        Should Be Empty    ${errors}

.. _validate-roundtrip:

Round-trip s Generate Data From Schema
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Validační keyword má smysl kombinovat s ``Generate Data From Schema`` — stejné schéma se použije pro generování i pro kontrolu odpovědi.

.. code-block:: robotframework

    *** Test Cases ***
    Generate Then Validate Round Trip
        Load Schema    swagger_path=./api.yaml

        # Generuj request data podle požadavkového schématu
        ${data}=    Generate Data From Schema    method=POST    endpoint=/items

        # Validuj data proti odpovědnímu schématu (response 201)
        Validate Data Against Schema
        ...    data=${data}    method=POST    endpoint=/items    response_code=${201}

V kombinaci s online OpenAPI URL se cache využije pro oba kroky — během round-tripu proběhne pouze jedno stažení specifikace.

**Detailní popis chování**

.. _validate-error-format:

Struktura chybového slovníku
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pro ``return_errors=True`` má každá položka výsledného seznamu tvar:

.. code-block:: python

    {
        "path": "$.email",
        "path_parts": ["email"],
        "message": "'not-email' is not a 'email'",
        "validator": "format",
        "validator_value": "email",
        "instance": "not-email",
    }

Pro chybu uvnitř pole se cesta rozšíří o index, např. ``$.users[0].email``.

.. _validate-strict-nested:

Strict mode v praxi
~~~~~~~~~~~~~~~~~~~

Strict režim platí i pro **vnořené objekty** a **komponenty dosažené přes** ``$ref``:

.. code-block:: robotframework

    *** Test Cases ***
    Strict Applies To Refd Component
        # Schéma má User.address: $ref → Address (s required: city).
        # Pole 'extra' není v Address deklarované, validace selže.
        Load Schema    swagger_path=./api.yaml
        ${address}=    Create Dictionary    city=Praha    extra=foo
        ${data}=    Create Dictionary    id=${1}    name=Jan    address=${address}
        Run Keyword And Expect Error    *Validation failed*
        ...    Validate Data Against Schema
        ...    data=${data}    method=POST    endpoint=/users    response_code=${201}

**Důležité poznámky**

* **Pouze numerické status kódy.** ``response_code=200`` nebo ``response_code=${201}``. Kódy ``default``, ``2XX``, ``4XX`` ze sekce ``responses`` se ignorují (sledováno jako issue).
* **Pouze ``application/json`` content type.** Endpointy bez ``application/json`` v ``responses[*].content`` nejsou v indexu dostupné.
* **OpenAPI 3.0 formáty.** Validátor podporuje OpenAPI 3.0 formáty navíc oproti čistému JSON Schema (``int32``, ``int64``, ``float``, ``double``, ``byte``, ``binary``).
* **Cache pro openapi_url.** Stejná URL se v rámci instance ``TalosForge`` stáhne pouze jednou (TTL 1 hodina) — to platí napříč ``Generate Data From Schema`` i ``Validate Data Against Schema``.

**Chyby**

* ``DataValidationError`` (podtyp ``TalosForgeException``) - data neodpovídají schématu (``return_errors=False``). Atribut ``errors`` obsahuje seznam chybových slovníků.
* ``TalosForgeException`` - chyba ve zdroji schématu, např.:

  * není specifikován žádný zdroj
  * ``openapi_url`` bez ``endpoint``
  * endpoint nebyl nalezen v načtené specifikaci
  * neexistující ``response_code`` u daného endpointu
  * URL nelze stáhnout, nebo specifikace má neplatný YAML/JSON

Související kapitoly
--------------------

* :doc:`installation` - Instalace a nastavení
* :doc:`api` - API reference
