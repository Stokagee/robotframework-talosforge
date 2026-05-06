.. _api:

API Reference
=============

Kompletní reference všech tříd a metod TalosForge.

.. contents::
    :local:
    :depth: 2

Hlavní třída
------------

.. py:class:: TalosForge.TalosForge

    Hlavní třída TalosForge knihovny pro Robot Framework.

    Poskytuje tři hlavní keywords:

    * :py:meth:`load_schema` - Načte OpenAPI soubor do paměti
    * :py:meth:`generate_data_from_schema` - Generuje testovací data ze schématu
    * :py:meth:`validate_data_against_schema` - Validuje data proti schématu (od verze 0.4.0)

    **Inicializace**

    Třída se automaticky inicializuje při importu do Robot Frameworku:

    .. code-block:: robotframework

        *** Settings ***
        Library     TalosForge

    Vzákladní nastavení (konfigurace se provádí přes environment proměnné):

    * ``TAOSFORGE_LOCALE`` - Lokalizace pro Faker (default: ``cs_CZ``)
    * ``OPENAI_API_KEY`` - API klíč pro OpenAI
    * ``ZHIPU_API_KEY`` - API klíč pro Zhipu AI

    .. py:method:: load_schema(swagger_path: str, force_reload: bool = False) -> None

        Načte OpenAPI soubor do paměti pro rychlejší přístup.

        :param str swagger_path: Cesta k lokálnímu OpenAPI souboru (JSON/YAML)
        :param bool force_reload: Vynutí znovunačtení i když je již načteno
        :raises TalosForgeException: Pokud soubor neexistuje nebo je poškozený

        **Příklad:**

        .. code-block:: robotframework

            Load Schema    swagger_path=./api.yaml

    .. py:method:: generate_data_from_schema(schema_path: str = None, method: str = None, endpoint: str = None, openapi_url: str = None, target: str = 'api', amount: int = 1, use_ai: bool = False) -> Any

        Generuje testovací data na základě schématu.

        :param schema_path: Cesta k JSON schématu
        :param method: HTTP metoda (``GET``, ``POST``, ...). Doporučený způsob specifikace metody (od verze 0.4.0). Vyžaduje ``endpoint``.
        :param endpoint: Cesta k endpointu (s ``method=`` jen cesta, bez ``method=`` ve formátu ``METODA /cesta``)
        :param openapi_url: URL k online OpenAPI specifikaci
        :param target: ``api`` nebo ``ui``
        :param amount: Počet záznamů
        :param use_ai: Povolí AI generování
        :return: Slovník (amount=1) nebo seznam slovníků (amount>1)
        :raises TalosForgeException: Chyba při generování

        **Příklady:**

        .. code-block:: robotframework

            # Z JSON schématu
            ${user}=    Generate Data From Schema    schema_path=./user.json

            # Z endpointu (nová syntaxe)
            ${data}=    Generate Data From Schema    method=POST    endpoint=/users

            # Z endpointu (zpětně kompatibilní syntaxe)
            ${data}=    Generate Data From Schema    endpoint=POST /users

            # Více záznamů
            ${users}=    Generate Data From Schema    method=POST    endpoint=/users    amount=5

    .. py:method:: validate_data_against_schema(data: Any, schema_path: str = None, endpoint: str = None, method: str = None, openapi_url: str = None, response_code: int = 200, return_errors: bool = False) -> Optional[List[Dict[str, Any]]]

        Validuje data proti JSON Schema nebo OpenAPI 3.0 response schématu (od verze 0.4.0).

        Strict mode je vždy zapnutý: extra pole, chybějící ``required`` pole, type/format/range nesoulady vyhazují chybu.

        :param data: Data k validaci (slovník nebo seznam)
        :param schema_path: Cesta k lokálnímu JSON schématu
        :param endpoint: Endpoint z načtené OpenAPI (volitelně s ``method=``)
        :param method: HTTP metoda pro endpoint
        :param openapi_url: URL k OpenAPI specifikaci (vyžaduje ``endpoint``)
        :param response_code: HTTP status code response schématu (default ``200``)
        :param return_errors: Pokud ``True``, vrací seznam chyb místo raise
        :return: ``None`` při validních datech (return_errors=False), nebo seznam chybových slovníků (return_errors=True; prázdný seznam = validní)
        :raises DataValidationError: Pokud return_errors=False a data neodpovídají schématu
        :raises TalosForgeException: Pokud zdroj není platný nebo schéma/endpoint není nalezeno

        **Příklady:**

        .. code-block:: robotframework

            # Proti lokálnímu JSON schématu
            ${data}=    Create Dictionary    name=Jan    email=jan@example.cz
            Validate Data Against Schema    data=${data}    schema_path=./user.json

            # Proti response schématu z načtené OpenAPI
            Load Schema    swagger_path=./api.yaml
            Validate Data Against Schema    data=${response}
            ...    method=POST    endpoint=/users    response_code=${201}

            # Proti online OpenAPI URL
            Validate Data Against Schema    data=${response}
            ...    openapi_url=https://api.example.com/openapi.yaml
            ...    method=GET    endpoint=/items    response_code=${200}

            # Získat chyby jako seznam
            ${errors}=    Validate Data Against Schema    data=${data}
            ...    schema_path=./user.json    return_errors=${True}

Core moduly
-----------

.. py:module:: TalosForge.core
    :synopsis: Hlavní logika generování

Core moduly obsahují klíčové komponenty pro generování dat.

.. py:class:: TalosForge.core.generator.DataGenerator

    Generátor testovacích dat pomocí Fakeru.

    Hlavní metoda:

    .. py:method:: generate(schema: Dict[str, Any], target: str = 'api', use_ai: Bool = False) -> Any

        Generuje data podle JSON Schema.

        :param schema: JSON Schema slovník
        :param target: ``api`` nebo ``ui``
        :param use_ai: Povolí AI pro složité případy
        :return: Vygenerovaná data

    Podporované typy:

    * ``_generate_string`` - string s format, minLength, maxLength, pattern
    * ``_generate_integer`` - integer s minimum, maximum
    * ``_generate_number`` - float s minimum, maximum
    * ``_generate_boolean`` - boolean
    * ``_generate_array`` - array s items, minItems, maxItems (rekurzivní)
    * ``_generate_object`` - object s properties, required, default (rekurzivní)
    * ``_handle_enum`` - enum hodnoty
    * ``_handle_oneof_anyof_allof`` - oneOf/anyOf/allOf konstrukce

.. py:class:: TalosForge.core.ai_generator.AIGenerator

    Generátor testovacích dat pomocí AI modelů.

    Hlavní metoda:

    .. py:method:: generate(schema_fragment: Dict[str, Any], target: str = 'api', context_description: str = None) -> Any

        Generuje data pomocí AI modelu.

        :param schema_fragment: Část JSON Schema
        :param target: ``api`` nebo ``ui``
        :param context_description: Volitelný kontext (např. z ``description``)
        :return: Vygenerovaná data

    Používá OpenAI nebo Zhipu AI podle dostupnosti API klíčů.

.. py:class:: TalosForge.schema.loader.SchemaLoader

    Načítá a parsuje JSON a OpenAPI schémata.

    Metody:

    * ``load_json_schema(schema_path)`` - Načte JSON schéma ze souboru
    * ``load_openapi_spec(spec_path)`` - Načte OpenAPI specifikaci (JSON/YAML)
    * ``extract_endpoint_schemas(spec)`` - Extrahuje schémata z requestBody
    * ``load_openapi_spec_from_url(spec_url)`` - Stáhne specifikaci z URL
    * ``extract_response_schemas(spec)`` - *(od verze 0.4.0, rozšířeno v 0.4.1)* Extrahuje response schémata z OpenAPI 3.0 specifikace. Vrací slovník ``{"METHOD /path": {status_key: schema}}`` pro ``application/json`` content type. ``status_key`` je ``int`` pro numerické kódy (``200``), ``str`` pro range kódy (``"2XX"`` … ``"5XX"``, vždy uppercase) a ``"default"`` pro fallback definici.
    * ``resolve_response_schema(schemas, response_code)`` - *(od verze 0.4.1)* Statický helper, který pro daný numerický ``response_code`` vybere schéma v pořadí: přesný numerický kód → range bucket (např. ``2XX`` pro ``200``) → ``default``. Vrací ``None``, pokud žádná úroveň nesedí.
    * ``build_registry(spec)`` - *(od verze 0.4.0)* Postaví ``referencing.Registry`` pro resolution ``$ref`` odkazů v OpenAPI specifikaci. Použito interně ``SchemaValidator``em pro validaci proti komponentám z ``components.schemas``.

.. py:class:: TalosForge.utils.cache.SimpleCache

    Jednoduchá mezipaměť pro URL specifikace.

    Metody:

    * ``get(key)`` - Získá hodnotu z cache
    * ``set(key, value)`` - Uloží hodnotu do cache
    * ``has(key)`` - Zkontroluje klíč v cache
    * ``clear()`` - Vymaže cache
    * ``remove(key)`` - Odstraní konkrétní klíč
    * ``size()`` - Velikost cache
    * ``cleanup()`` - Odstraní expirované položky

Validation modul
----------------

*Od verze 0.4.0.*

.. py:module:: TalosForge.validation
    :synopsis: Validace dat proti JSON Schema / OpenAPI 3.0

.. py:class:: TalosForge.validation.validator.SchemaValidator

    Wrapper kolem ``openapi_schema_validator.OAS30Validator`` s **vždy zapnutým strict režimem** (``additionalProperties: false`` se rekurzivně aplikuje na všechny ``object`` schémata, včetně vnořených objektů a komponent dosažených přes ``$ref``).

    .. py:method:: __init__(schema: Dict[str, Any], registry: Optional[referencing.Registry] = None)

        :param schema: JSON Schema nebo OpenAPI 3.0 schéma fragment
        :param registry: Volitelný ``referencing.Registry`` pro resolution ``$ref`` odkazů (typicky postavený přes :py:meth:`SchemaLoader.build_registry`)

    .. py:method:: validate(data: Any, return_errors: bool = False) -> Optional[List[Dict[str, Any]]]

        Validuje ``data`` proti schématu.

        :param data: Data k validaci
        :param return_errors: Pokud ``True``, vrátí seznam chybových slovníků místo raise
        :return: ``None`` při úspěchu (return_errors=False), nebo seznam chyb (return_errors=True; prázdný = validní)
        :raises DataValidationError: Pokud return_errors=False a validace selhala

.. py:module:: TalosForge.validation.error_formatter
    :synopsis: Formátování chyb z jsonschema

.. py:function:: TalosForge.validation.error_formatter.format_path(path_parts) -> str

    Převede deque/seznam segmentů cesty na řetězec ve stylu JSONPath.

    Příklady: ``[]`` → ``"$"``, ``["users", 0, "email"]`` → ``"$.users[0].email"``.

.. py:function:: TalosForge.validation.error_formatter.error_to_dict(error) -> Dict[str, Any]

    Převede ``jsonschema.exceptions.ValidationError`` na serializovatelný slovník s poli ``path``, ``path_parts``, ``message``, ``validator``, ``validator_value``, ``instance``.

Výjimky
--------

.. py:exception:: TalosForge.core.exceptions.TalosForgeException

    Základní výjimka pro TalosForge.

    Všechny chyby v knihovně dědí od této třídy.

.. py:exception:: TalosForge.validation.exceptions.DataValidationError

    *Od verze 0.4.0.*

    Vyhozená keywordem :py:meth:`validate_data_against_schema` (a třídou :py:class:`SchemaValidator`) pokud data neprojdou strict-mode validací.

    Dědí od :py:exc:`TalosForgeException`.

    Atributy:

    * ``message`` (str) — lidsky čitelná zpráva s výpisem všech chyb
    * ``errors`` (list[dict]) — seznam chybových slovníků (stejná struktura jako návratová hodnota ``validate(..., return_errors=True)``)
