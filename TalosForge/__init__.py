"""
TalosForge - Schema-driven test data generator for Robot Framework.

Tento modul poskytuje hlavní TalosForge třídu s keywords pro Robot Framework.
TalosForge generuje testovací data na základě JSON Schema a OpenAPI specifikací.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from robot.api.deco import keyword

from .core.config import _update_globals, init_config
from .core.exceptions import TalosForgeException
from .core.generator import DataGenerator
from .schema.loader import SchemaLoader
from .utils.logger import log_error, log_warning

logger = logging.getLogger(__name__)


class TalosForge:
    """
    Hlavní třída TalosForge knihovny.

    Poskytuje hlavní keywords pro Robot Framework:
    - Load Schema: Načte OpenAPI soubor nebo databázové schéma do paměti
    - Generate Data From Schema: Generuje testovací data ze schématu
    - Validate Data Against Schema: Validuje data proti JSON Schema / OpenAPI

    Example:
        *** Settings ***
        Library     TalosForge

        *** Test Cases ***
        Generate User Data
            ${user}=    Generate Data From Schema    schema_path=user.json
            Log    ${user}
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializuje TalosForge instanci.

        Args:
            config_path: Volitelná cesta ke konfiguračnímu souboru.
        """
        # Inicializace konfigurace
        if config_path:
            init_config(Path(config_path))
        else:
            init_config()

        # Aktualizace globálních proměnných pro zpětnou kompatibilitu
        _update_globals()

        self.schema_loader = SchemaLoader()
        self.data_generator = DataGenerator()
        self._loaded_openapi_schemas: Dict[str, Dict[str, Any]] = {}
        # Raw OpenAPI specs (needed by validate_data_against_schema for
        # response code resolution and registry building)
        self._loaded_specs: Dict[str, Dict[str, Any]] = {}
        self._loaded_db_schema: Optional[Dict[str, Any]] = None
        self._loaded_db_module: Optional[str] = None

    @keyword
    def load_schema(
        self,
        swagger_path: str = None,
        force_reload: bool = False,
        allow_external_refs: bool = False,
        # Database parameters
        db_module: str = None,
        db_name: str = None,
        db_host: str = None,
        db_port: int = None,
        db_user: str = None,
        db_password: str = None,
        db_schema: str = "public",
        db_table: str = None,
        db_exclude_columns: str = None,
    ) -> None:
        """
        Načte OpenAPI soubor nebo databázové schéma do paměti pro rychlejší přístup.

        Tato metoda načte lokální OpenAPI soubor, zpracuje jej a uloží
        do paměti pro následné použití s keywordem Generate Data From Schema.
        Je doporučeno pro velké OpenAPI soubory s mnoha endpointy.

        Alternativně může načíst schéma databázové tabulky z PostgreSQL, MySQL, atd.

        Args:
            swagger_path: Cesta k lokálnímu OpenAPI (Swagger) souboru (JSON nebo YAML).
            force_reload: Pokud je True, vynutí znovunačtení souboru,
                i když byl již načten. Default: False.
            allow_external_refs: Pokud je True, povolí resolving externích $ref
                reference v OpenAPI specifikaci. Vyžaduje nainstalovanou knihovnu
                'prance'. Default: False.
            db_module: Python DB modul (např. 'psycopg2', 'pymysql'). Default: None.
            db_name: Název databáze. Default: None.
            db_host: Host databáze. Default: None.
            db_port: Port databáze. Default: None.
            db_user: Uživatelské jméno. Default: None.
            db_password: Heslo. Default: None.
            db_schema: Název schématu v databázi (default: "public").
            db_table: Název tabulky pro čtení schématu. Default: None.
            db_exclude_columns: Čárkou oddělený seznam sloupců k vyloučení. Default: None.

        Raises:
            TalosForgeException: Pokud soubor neexistuje nebo nelze parsovat.

        Example:
            *** Test Cases ***
            Load API Specification
                Load Schema    swagger_path=./petstore.yaml
                ${pet}=    Generate Data From Schema    endpoint=POST /pet

            Load With External Refs
                Load Schema    swagger_path=./api.yaml    allow_external_refs=${TRUE}

            Load Database Schema
                Load Schema    db_module=psycopg2    db_name=test    db_host=localhost    \\
                ...    db_port=5432    db_user=postgres    db_password=postgres    \\
                ...    db_schema=public    db_table=users
        """
        # Database mode - načítání schématu z databáze
        if db_module is not None:
            from .db import DB_READERS

            # Validace db_module
            if db_module not in DB_READERS:
                available = ", ".join(DB_READERS.keys())
                log_error(f"Unsupported db_module '{db_module}'. Available: {available}")
                raise TalosForgeException(
                    f"Unsupported db_module '{db_module}'. Available: {available}"
                )

            # Validace povinných parametrů
            if not all([db_name, db_host, db_port, db_user, db_password]):
                log_error(
                    "Database parameters require: db_name, db_host, db_port, db_user, db_password"
                )
                raise TalosForgeException(
                    "Database parameters require: db_name, db_host, db_port, db_user, db_password"
                )

            if not db_table:
                log_error("db_table is required for database schema loading")
                raise TalosForgeException("db_table is required for database schema loading")

            # Sestavení connection stringu
            conn_string = (
                f"host={db_host} port={db_port} dbname={db_name} "
                f"user={db_user} password={db_password}"
            )

            # Získání příslušné čtečky
            reader_class = DB_READERS[db_module]

            # Vytvoření čtečky a načtení schématu
            try:
                reader = reader_class(
                    dsn=conn_string,
                    schema=db_schema,
                    table=db_table,
                    exclude_columns=db_exclude_columns.split(",") if db_exclude_columns else [],
                )
                schema = reader.load_schema()
                self._loaded_db_schema = schema
                self._loaded_db_module = db_module
                logger.info(f"Loaded database schema: {db_schema}.{db_table} " f"using {db_module}")
            except TalosForgeException:
                raise
            except Exception as e:
                log_error(f"Failed to load database schema: {e}")
                raise TalosForgeException(f"Failed to load database schema: {e}")
            finally:
                reader.close()
            return

        # OpenAPI mode - validace swagger_path
        if not swagger_path:
            log_error("Parametr 'swagger_path' je prázdný. Zadejte cestu k OpenAPI souboru.")
            raise TalosForgeException("Parametr 'swagger_path' je povinný")

        if not swagger_path.endswith((".json", ".yaml", ".yml")):
            log_warning(f"Soubor '{swagger_path}' nemá očekávanou příponu (.json, .yaml, .yml)")

        # Pokud není force_reload a schéma je již načteno, přeskočíme
        if not force_reload and swagger_path in self._loaded_openapi_schemas:
            log_warning(
                f"Schéma '{swagger_path}' je již načteno. "
                "Použijte force_reload=True pro znovunačtení."
            )
            return

        try:
            # Vytvořit SchemaLoader s příslušným nastavením allow_external_refs
            if allow_external_refs:
                loader = SchemaLoader(allow_external_refs=True)
                logger.info(f"Načítání schématu {swagger_path} s povolenými externími $ref")
            else:
                loader = self.schema_loader

            # Načtení OpenAPI specifikace
            spec = loader.load_openapi_spec(swagger_path)

            # Extrakce endpoint schémat
            endpoint_schemas = loader.extract_endpoint_schemas(spec)

            # Uložení do paměti — endpoint_schemas pro generování,
            # spec pro Validate Data Against Schema (response code resolution)
            self._loaded_openapi_schemas[swagger_path] = endpoint_schemas
            self._loaded_specs[swagger_path] = spec

            logger.info(f"Načten schéma {swagger_path} s {len(endpoint_schemas)} endpointy")
        except TalosForgeException:
            raise
        except Exception as e:
            raise TalosForgeException(f"Chyba při načítání schématu {swagger_path}: {e}")

    @keyword
    def generate_data_from_schema(
        self,
        schema_path: Optional[str] = None,
        method: Optional[str] = None,
        endpoint: Optional[str] = None,
        openapi_url: Optional[str] = None,
        target: str = "api",
        amount: int = 1,
        use_ai: bool = False,
        explore: bool = False,
        convert_decimals: bool = True,
        exclude_dictionary: Optional[str] = None,
    ) -> Any:
        """
        Generuje testovací data na základě poskytnutého schématu.

        Toto je hlavní keyword pro generování testovacích dat. Podporuje tři zdroje:
        - schema_path: Vlastní JSON schéma
        - endpoint: Endpoint z načteného OpenAPI souboru (vyžaduje Load Schema)
        - openapi_url: Online OpenAPI specifikace (vyžaduje endpoint)
        - target=db: Použije načtené databázové schéma (vyžaduje Load Schema s DB params)

        Args:
            schema_path: Cesta k lokálnímu JSON schématu.
            method: HTTP metoda (např. "POST", "GET"). Vyžaduje také parametr
                endpoint. Toto je preferovaný způsob specifikace HTTP metody.
            endpoint: Cesta k endpointu. Pokud je zadán parametr method, pouze
                cesta (např. "/users"). Pokud není zadán method, musí být ve
                formátu "METODA /cesta" (např. "POST /users") pro zpětnou
                kompatibilitu. Vyžaduje předchozí volání Load Schema.
            openapi_url: URL k online OpenAPI specifikaci. Vyžaduje endpoint.
            target: Formát výstupu. Možnosti: "api" (default), "ui" nebo "db".
                "api" vrací čistý slovník, "ui" vrací slovník pro UI testy,
                "db" vrací SQL VALUES řetězec pro DatabaseLibrary (např: "'Jan', 'Novák', 123").
            amount: Počet generovaných záznamů. Default: 1.
                Pokud je explore=True, určuje počet edge-case variant.
            use_ai: Povolí použití AI pro složité případy. Default: False.
            explore: Pokud je True, vygeneruje mnoho variant (edge-cases)
                pro property-based/fuzz testing. Vyžaduje nainstalovanou knihovnu
                'hypothesis-jsonschema'. Vrací vždy seznam. Default: False.
            convert_decimals: Pokud je True (default), automaticky převede
                Decimal hodnoty na float pro JSON kompatibilitu.
                Faker.latitude()/longitude() vrací Decimal.
                Pro přesné výpočty nastavte False. Default: True.
            exclude_dictionary: Čárkou oddělený seznam JSON cest k vyloučení
                z vygenerovaných dat. Používá tečkovou notaci pro vnořená pole
                (např. "id,created_at,user.id"). Case-sensitive. Default: None.

        Returns:
            Pokud target="db": SQL VALUES řetězec nebo seznam řetězců
                (např: "'Jan', 'Novák', 123" pro DatabaseLibrary).
            Jinak: Jeden slovník (pokud amount=1 a explore=False),
                seznam slovníků (pokud amount>1 nebo explore=True).

        Raises:
            TalosForgeException: Pokud není specifikován právě jeden zdroj nebo
                při chybě v generování.

        Example:
            # Z lokálního JSON schématu
            ${user}=    Generate Data From Schema    schema_path=./user.json

            # Z načteného OpenAPI souboru
            Load Schema    swagger_path=./api.yaml
            ${data}=    Generate Data From Schema    endpoint=POST /users    amount=5

            # Pro UI testování
            ${form}=    Generate Data From Schema    schema_path=./login.json    target=ui

            # Explore režim pro edge-case testing
            ${variants}=    Generate Data From Schema    ${schema}    explore=${TRUE}    amount=100

            # Z databázového schématu
            Load Schema    db_module=psycopg2    db_name=test    db_host=localhost    \\
            ...    db_port=5432    db_user=postgres    db_password=postgres    db_table=users
            ${user}=    Generate Data From Schema    target=db

            # S vyloučenými poli
            ${user}=    Generate Data From Schema
            ...    schema_path=./user.json
            ...    exclude_dictionary=id,created_at
        """
        # Validace: method vyžaduje endpoint
        if method and not endpoint:
            log_error(f"Parametr 'method'='{method}' je specifikován, ale chybí 'endpoint'.")
            raise TalosForgeException("Parametr 'method' vyžaduje také parametr 'endpoint'.")

        # Validace: musí být specifikován právě jeden zdroj
        sources_specified = 0
        if schema_path:
            sources_specified += 1
        if endpoint and not openapi_url:
            sources_specified += 1
        if openapi_url:
            sources_specified += 1
        if target == "db":
            sources_specified += 1

        if sources_specified == 0:
            log_error(
                "Žádný zdroj dat není specifikován. "
                "Zadejte schema_path, endpoint+method, openapi_url nebo target=db."
            )
            raise TalosForgeException(
                "Musí být specifikován alespoň jeden zdroj dat: "
                "schema_path, endpoint, openapi_url nebo target=db"
            )
        if sources_specified > 1:
            log_warning("Specifikováno více zdrojů dat. Bude použit pouze jeden podle priority.")
            raise TalosForgeException(
                "Musí být specifikován právě jeden zdroj dat, ne více najednou"
            )

        # Získání schématu ze zadaného zdroje
        schema = self._get_schema(schema_path, method, endpoint, openapi_url, target)

        # Zpracování exclude_dictionary parametru
        exclude_paths = []
        if exclude_dictionary:
            exclude_paths = [p.strip() for p in exclude_dictionary.split(",") if p.strip()]
            if exclude_paths:
                logger.info(f"Vyloučené JSON cesty: {exclude_paths}")

        # Explore režim - generování mnoha variant pomocí hypothesis-jsonschema
        if explore:
            logger.info(f"Explore režim aktivován, generuji {amount} edge-case variant")
            results = self.data_generator.generate_explore(schema, amount)
            if exclude_paths:
                logger.info(f"Aplikuji vyloučení polí na {len(results)} variant")
                results = [self._exclude_by_path(r, exclude_paths, "") for r in results]
            return results

        # Standardní generování dat pomocí DataGenerator
        results = []
        for _ in range(amount):
            generated = self.data_generator.generate(schema, target, use_ai)
            if exclude_paths:
                generated = self._exclude_by_path(generated, exclude_paths, "")
            results.append(generated)

        if exclude_paths and results:
            logger.info(f"Vygenerováno {len(results)} záznamů s vyloučenými poli")

        # Převede Decimal na float pro JSON kompatibilitu
        if convert_decimals:
            logger.info(f"Převádím Decimal → float pro {len(results)} výsledků")
            results = [self._convert_decimals(result) for result in results]

        # Speciální formátování pro databázové INSERT (target=db)
        if target == "db":
            formatted_results = [self._format_for_sql(r, schema) for r in results]
            if amount == 1:
                return formatted_results[0]
            return formatted_results

        # Standardní vrácení slovníku nebo seznamu
        if amount == 1:
            return results[0]
        return results

    def _resolve_endpoint_key(self, method: Optional[str], endpoint: str) -> str:
        """
        Převede method+endpoint na formát 'METHOD /path'.

        Příklady:
            method="POST", endpoint="/users" → "POST /users"
            method=None, endpoint="POST /users" → "POST /users" (zpětná kompatibilita)
            method="get", endpoint="users" → "GET /users"
            method="POST", endpoint="POST /users" → "POST /users"

        Args:
            method: HTTP metoda (např. "POST", "GET"). None pro zpětnou kompatibilitu.
            endpoint: Cesta k endpointu.

        Returns:
            Endpoint klíč ve formátu "METHOD /path".

        Raises:
            TalosForgeException: Pokud endpoint neobsahuje metodu a method není zadán.
        """
        if method:
            method = method.upper().strip()
            endpoint = endpoint.strip()

            parts = endpoint.split(None, 1)
            if len(parts) == 2:
                endpoint = parts[1]

            if not endpoint.startswith("/"):
                endpoint = "/" + endpoint

            return f"{method} {endpoint}"
        else:
            endpoint = endpoint.strip()
            parts = endpoint.split(None, 1)
            if len(parts) == 2:
                return endpoint
            raise TalosForgeException(
                f"Endpoint '{endpoint}' neobsahuje HTTP metodu. "
                "Použijte parametr 'method=' nebo zadejte 'METHOD /path'."
            )

    def _get_schema(
        self,
        schema_path: Optional[str],
        method: Optional[str],
        endpoint: Optional[str],
        openapi_url: Optional[str],
        target: str,
    ) -> Dict[str, Any]:
        """
        Získá schéma ze zadaného zdroje.

        Args:
            schema_path: Cesta k JSON schématu.
            method: HTTP metoda (např. "POST", "GET").
            endpoint: Endpoint z načteného OpenAPI.
            openapi_url: URL k OpenAPI specifikaci.
            target: Formát výstupu ("api", "ui" nebo "db").

        Returns:
            Slovník reprezentující JSON schéma.

        Raises:
            TalosForgeException: Pokud nelze získat schéma.
        """
        # Database source logika
        if target == "db":
            if self._loaded_db_schema is None:
                log_error(
                    "Žádné databázové schéma není načteno. "
                    "Nejprve použijte keyword 'Load Schema' s databázovými parametry."
                )
                raise TalosForgeException(
                    "No database schema loaded. First use 'Load Schema' with database parameters."
                )
            return self._loaded_db_schema

        # Z lokálního JSON schématu
        if schema_path:
            return self.schema_loader.load_json_schema(schema_path)

        # Z URL OpenAPI nebo JSON Schema (má přednost před načtenými schématy)
        if openapi_url:
            try:
                spec = self.schema_loader.load_openapi_spec_from_url(openapi_url)

                if endpoint:
                    endpoint_schemas = self.schema_loader.extract_endpoint_schemas(spec)
                    endpoint_key = self._resolve_endpoint_key(method, endpoint)

                    if endpoint_key in endpoint_schemas:
                        return endpoint_schemas[endpoint_key]
                    else:
                        available = list(endpoint_schemas.keys())
                        raise TalosForgeException(
                            f"Endpoint '{endpoint_key}' nebyl nalezen v "
                            f"OpenAPI specifikaci z {openapi_url}. "
                            f"Dostupné endpointy: {available}"
                        )
                else:
                    # Bez endpointu → JSON Schema logika (vrátí spec přímo)
                    return spec
            except TalosForgeException:
                raise
            except Exception as e:
                raise TalosForgeException(f"Chyba při zpracování {openapi_url}: {e}")

        # Z endpointu (vyžaduje načtené OpenAPI)
        if endpoint:
            if not self._loaded_openapi_schemas:
                log_error(
                    "Žádné OpenAPI schéma není načteno. Nejprve použijte keyword 'Load Schema'."
                )
                raise TalosForgeException(
                    "Žádné OpenAPI schéma není načteno. Nejprve použijte keyword 'Load Schema'."
                )

            endpoint_key = self._resolve_endpoint_key(method, endpoint)

            for loaded_schema in self._loaded_openapi_schemas.values():
                if endpoint_key in loaded_schema:
                    return loaded_schema[endpoint_key]

            raise TalosForgeException(
                f"Endpoint '{endpoint_key}' nebyl nalezen v žádném načteném OpenAPI schématu. "
                f"Dostupné endpointy: {self._get_available_endpoints()}"
            )

        raise TalosForgeException("Neplatná kombinace parametrů")

    def _get_available_endpoints(self) -> List[str]:
        """Vrátí seznam všech dostupných endpointů z načtených schémat."""
        endpoints = []
        for schema in self._loaded_openapi_schemas.values():
            endpoints.extend(schema.keys())
        return sorted(list(set(endpoints)))

    @keyword
    def validate_data_against_schema(
        self,
        data: Any,
        schema_path: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        openapi_url: Optional[str] = None,
        response_code: int = 200,
        return_errors: bool = False,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Validuje data proti JSON Schema nebo OpenAPI 3.0 response schématu.

        Strict mode je vždy zapnutý:
        - Extra pole, která nejsou ve schématu, vyhazují chybu
        - Chybějící required pole vyhazují chybu
        - Type/format/range nesoulady vyhazují chybu

        Zdroje (právě jeden musí být specifikován):
        1. schema_path - lokální JSON Schema soubor (Phase 1)
        2. endpoint (+ method) - endpoint z předem načtené OpenAPI specifikace (Phase 2)
        3. openapi_url (+ endpoint + method) - online OpenAPI specifikace (Phase 3)

        Args:
            data: Data k validaci (slovník nebo seznam).
            schema_path: Cesta k lokálnímu JSON schématu.
            endpoint: Endpoint z načteného OpenAPI (Phase 2).
            method: HTTP metoda pro endpoint (Phase 2).
            openapi_url: URL k OpenAPI specifikaci (Phase 3).
            response_code: HTTP status code response schématu (default 200, Phase 2).
            return_errors: Pokud True, vrátí seznam chyb místo raise (default False).

        Returns:
            None pokud return_errors=False a validace prošla.
            Seznam chybových slovníků pokud return_errors=True (prázdný = validní).

        Raises:
            DataValidationError: Pokud return_errors=False a validace selhala.
            TalosForgeException: Pokud zdroj není platný nebo není schéma nalezeno.

        Example:
            *** Test Cases ***
            Validate User Data
                ${data}=    Create Dictionary    name=Jan    email=jan@example.cz
                Validate Data Against Schema    data=${data}    schema_path=./user.json
        """
        from .validation.validator import SchemaValidator

        # Phase 1: schema_path
        if schema_path:
            schema = self.schema_loader.load_json_schema(schema_path)
            validator = SchemaValidator(schema)
            return validator.validate(data, return_errors=return_errors)

        # Dispatch order: openapi_url > endpoint > schema_path. openapi_url
        # is checked BEFORE endpoint because it uses endpoint+method as
        # sub-parameters; running endpoint branch first when both are set
        # would hit "no spec loaded" (URL specs are not in _loaded_specs).

        # Phase 3: openapi_url
        if openapi_url:
            if not endpoint:
                raise TalosForgeException(
                    "Při použití openapi_url musí být specifikován i endpoint."
                )
            key = self._resolve_endpoint_key(method, endpoint)
            # SimpleCache TTL=3600s on the underlying SchemaLoader instance.
            # No public Clear Schema Cache keyword yet - tracked as follow-up
            # GitHub issue #TODO.
            spec = self.schema_loader.load_openapi_spec_from_url(openapi_url)
            return self._validate_against_spec(
                spec,
                key,
                response_code,
                data,
                return_errors,
                source_label=f"spec at {openapi_url}",
            )

        # Phase 2: endpoint (bez openapi_url)
        if endpoint:
            key = self._resolve_endpoint_key(method, endpoint)
            if not self._loaded_specs:
                raise TalosForgeException(
                    "Žádná OpenAPI specifikace není načtena. "
                    "Nejprve použijte keyword 'Load Schema'."
                )
            for spec in self._loaded_specs.values():
                if key in self.schema_loader.extract_response_schemas(spec):
                    return self._validate_against_spec(
                        spec,
                        key,
                        response_code,
                        data,
                        return_errors,
                        source_label="any loaded OpenAPI spec",
                    )
            raise TalosForgeException(f"Endpoint '{key}' not found in any loaded OpenAPI spec")

        raise TalosForgeException(
            "Musí být specifikován právě jeden zdroj: schema_path, endpoint nebo openapi_url"
        )

    def _validate_against_spec(
        self,
        spec: Dict[str, Any],
        key: str,
        response_code: int,
        data: Any,
        return_errors: bool,
        source_label: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Validate data against the response_code schema for `key` in `spec`.

        Shared between the endpoint branch (Phase 2) and the openapi_url
        branch (Phase 3) of validate_data_against_schema. source_label is
        embedded in error messages so the user knows which spec source
        the error came from.
        """
        from .validation.validator import SchemaValidator

        response_schemas = self.schema_loader.extract_response_schemas(spec)
        if key not in response_schemas:
            raise TalosForgeException(f"Endpoint '{key}' not found in {source_label}")
        # Resolution order: exact numeric → 'NXX' range bucket → 'default'.
        schema = self.schema_loader.resolve_response_schema(response_schemas[key], response_code)
        if schema is None:
            available = sorted(response_schemas[key].keys(), key=str)
            raise TalosForgeException(
                f"No schema for status code {response_code} (no exact, range "
                f"or default match). Available: {available}"
            )
        registry = self.schema_loader.build_registry(spec)
        validator = SchemaValidator(schema, registry=registry)
        return validator.validate(data, return_errors=return_errors)

    def _format_for_sql(self, data: Dict[str, Any], schema: Dict[str, Any]) -> str:
        """
        Formátuje vygenerovaná data jako SQL VALUES řetězec pro DatabaseLibrary.

        Args:
            data: Vygenerovaný slovník s daty
            schema: JSON Schema s informacemi o typech

        Returns:
            SQL VALUES řetězec např: "'Jan', 'Novák', 123, NULL"

        Example:
            >>> _format_for_sql({'name': 'Jan', 'age': 25}, {...})
            "'Jan', 25"
        """
        values = []

        # Získání pořadí sloupců ze schématu (properties zachovávají pořadí z DB)
        column_names = list(schema.get("properties", {}).keys())

        for col in column_names:
            if col not in data:
                continue

            value = data[col]

            if value is None:
                values.append("NULL")
            elif isinstance(value, str):
                # Escapování jednoduchých uvozovek (SQL injection protection)
                escaped = value.replace("'", "''")
                values.append(f"'{escaped}'")
            elif isinstance(value, bool):
                values.append("TRUE" if value else "FALSE")
            else:
                values.append(str(value))

        return ", ".join(values)

    def _convert_decimals(self, data: Any) -> Any:
        """
        Rekurzivně převede všechny Decimal hodnoty na float.

        Řeší problém JSON serializace - Decimal není JSON serializovatelný.
        Faker.latitude() a Faker.longitude() vrací Decimal.

        Args:
            data: Data k převedení (dict, list, tuple, nebo skalární hodnota)

        Returns:
            Data s převedenými Decimal hodnotami na float
        """
        from decimal import Decimal

        if isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, dict):
            return {key: self._convert_decimals(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_decimals(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(self._convert_decimals(item) for item in data)
        return data

    def _exclude_by_path(self, data: Any, exclude_paths: List[str], current_path: str) -> Any:
        """
        Rekurzivně odstraní pole podle JSON cest.

        Prochází data a odstraňuje všechny klíče, jejichž plná cesta
        odpovídá některé z cest v exclude_paths.

        Args:
            data: Data k filtrování (dict, list, nebo primitivní typ)
            exclude_paths: Seznam JSON cest k vyloučení (např. ["id", "user.id"])
            current_path: Aktuální cesta v rekurzi (např. "user")

        Returns:
            Filtrovaná data bez vyloučených polí.

        Example:
            >>> data = {"id": 1, "user": {"id": 2, "name": "Jan"}}
            >>> tf._exclude_by_path(data, ["user.id"], "")
            {"id": 1, "user": {"name": "Jan"}}
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                full_path = f"{current_path}.{key}" if current_path else key

                if full_path in exclude_paths:
                    logger.debug(f"Vyloučeno pole: {full_path}")
                    continue

                result[key] = self._exclude_by_path(value, exclude_paths, full_path)
            return result

        elif isinstance(data, list):
            return [self._exclude_by_path(item, exclude_paths, current_path) for item in data]

        else:
            return data


__all__ = ["TalosForge"]
