.. _api:

API Reference
=============

Kompletní reference všech tříd a metod TalosForge.

.. contents::
    :local:
    :depth: 2

Hlavní třída
------------

.. py:class:: talosforge.TalosForge

    Hlavní třída TalosForge knihovny pro Robot Framework.

    Poskytuje dva hlavní keywords:

    * :py:meth:`load_schema` - Načte OpenAPI soubor do paměti
    * :py:meth:`generate_data_from_schema` - Generuje testovací data ze schématu

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

    .. py:method:: generate_data_from_schema(schema_path: str = None, endpoint: str = None, openapi_url: str = None, target: str = 'api', amount: int = 1, use_ai: bool = False) -> Any

        Generuje testovací data na základě schématu.

        :param schema_path: Cesta k JSON schématu
        :param endpoint: Endpoint ve formátu ``METODA /cesta``
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

            # Z endpointu
            ${data}=    Generate Data From Schema    endpoint=POST /users

            # Více záznamů
            ${users}=    Generate Data From Schema    endpoint=POST /users    amount=5

Core moduly
-----------

.. py:module:: talosforge.core
    :synopsis: Hlavní logika generování

Core moduly obsahují klíčové komponenty pro generování dat.

.. py:class:: talosforge.core.generator.DataGenerator

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

.. py:class:: talosforge.core.ai_generator.AIGenerator

    Generátor testovacích dat pomocí AI modelů.

    Hlavní metoda:

    .. py:method:: generate(schema_fragment: Dict[str, Any], target: str = 'api', context_description: str = None) -> Any

        Generuje data pomocí AI modelu.

        :param schema_fragment: Část JSON Schema
        :param target: ``api`` nebo ``ui``
        :param context_description: Volitelný kontext (např. z ``description``)
        :return: Vygenerovaná data

    Používá OpenAI nebo Zhipu AI podle dostupnosti API klíčů.

.. py:class:: talosforge.schema.loader.SchemaLoader

    Načítá a parsuje JSON a OpenAPI schémata.

    Metody:

    * ``load_json_schema(schema_path)`` - Načte JSON schéma ze souboru
    * ``load_openapi_spec(spec_path)`` - Načte OpenAPI specifikaci (JSON/YAML)
    * ``extract_endpoint_schemas(spec)`` - Extrahuje schémata z requestBody
    * ``load_openapi_spec_from_url(spec_url)`` - Stáhne specifikaci z URL

.. py:class:: talosforge.utils.cache.SimpleCache

    Jednoduchá mezipaměť pro URL specifikace.

    Metody:

    * ``get(key)`` - Získá hodnotu z cache
    * ``set(key, value)`` - Uloží hodnotu do cache
    * ``has(key)`` - Zkontroluje klíč v cache
    * ``clear()`` - Vymaže cache
    * ``remove(key)`` - Odstraní konkrétní klíč
    * ``size()`` - Velikost cache
    * ``cleanup()`` - Odstraní expirované položky

Výjimky
--------

.. py:exception:: talosforge.core.exceptions.TalosForgeException

    Základní výjimka pro TalosForge.

    Všechny chyby v knihovně dědí od této třídy.
