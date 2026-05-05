"""
TalosForge - Schema-driven test data generator for Robot Framework.

Tento modul poskytuje hlavní TalosForge třídu s keywords pro Robot Framework.
TalosForge generuje testovací data na základě JSON Schema a OpenAPI specifikací.
"""

import logging
from typing import Any, Dict, List, Optional

from robot.api.deco import keyword

from .core.exceptions import TalosForgeException
from .core.generator import DataGenerator
from .schema.loader import SchemaLoader

logger = logging.getLogger(__name__)


class TalosForge:
    """
    Hlavní třída TalosForge knihovny.

    Poskytuje dva hlavní keywords pro Robot Framework:
    - Load Schema: Načte OpenAPI soubor do paměti
    - Generate Data From Schema: Generuje testovací data ze schématu

    Example:
        *** Settings ***
        Library     TalosForge

        *** Test Cases ***
        Generate User Data
            ${user}=    Generate Data From Schema    schema_path=user.json
            Log    ${user}
    """

    def __init__(self):
        """Inicializuje TalosForge instanci."""
        self.schema_loader = SchemaLoader()
        self.data_generator = DataGenerator()
        self._loaded_openapi_schemas: Dict[str, Dict[str, Any]] = {}
        self._loaded_specs: Dict[str, Dict[str, Any]] = {}
        logger.info("TalosForge inicializován")

    @keyword
    def load_schema(self, swagger_path: str, force_reload: bool = False) -> None:
        """
        Načte OpenAPI soubor do paměti pro rychlejší přístup.

        Tato metoda načte lokální OpenAPI soubor, zpracuje jej a uloží
        do paměti pro následné použití s keywordem Generate Data From Schema.
        Je doporučeno pro velké OpenAPI soubory s mnoha endpointy.

        Args:
            swagger_path: Cesta k lokálnímu OpenAPI (Swagger) souboru (JSON nebo YAML).
            force_reload: Pokud je True, vynutí znovunačtení souboru,
                i když byl již načten. Default: False.

        Raises:
            TalosForgeException: Pokud soubor neexistuje nebo nelze parsovat.

        Example:
            *** Test Cases ***
            Load API Specification
                Load Schema    swagger_path=./petstore.yaml
                ${pet}=    Generate Data From Schema    endpoint=POST /pet
        """
        # Pokud není force_reload a schéma je již načteno, přeskočíme
        if not force_reload and swagger_path in self._loaded_openapi_schemas:
            logger.info(f"Schéma {swagger_path} je již načteno v paměti")
            return

        try:
            # Načtení OpenAPI specifikace
            spec = self.schema_loader.load_openapi_spec(swagger_path)

            # Extrakce endpoint schémat
            endpoint_schemas = self.schema_loader.extract_endpoint_schemas(spec)

            # Uložení do paměti
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
    ) -> Any:
        """
        Generuje testovací data na základě poskytnutého schématu.

        Toto je hlavní keyword pro generování testovacích dat. Podporuje tři zdroje:
        - schema_path: Vlastní JSON schéma
        - endpoint: Endpoint z načteného OpenAPI souboru (vyžaduje Load Schema)
        - openapi_url: Online OpenAPI specifikace (vyžaduje endpoint, implementace ve Fázi 4)

        Args:
            schema_path: Cesta k lokálnímu JSON schématu.
            method: HTTP metoda (např. "POST", "GET"). Vyžaduje také parametr
                endpoint. Toto je preferovaný způsob specifikace HTTP metody.
            endpoint: Cesta k endpointu. Pokud je zadán parametr method, pouze
                cesta (např. "/users"). Pokud není zadán method, musí být ve
                formátu "METODA /cesta" (např. "POST /users") pro zpětnou
                kompatibilitu. Vyžaduje předchozí volání Load Schema.
            openapi_url: URL k online OpenAPI specifikaci. Vyžaduje endpoint.
                Implementace ve Fázi 4.
            target: Formát výstupu. Možnosti: "api" (default) nebo "ui".
                "api" vrací čistý slovník, "ui" vrací slovník pro UI testy.
            amount: Počet generovaných záznamů. Default: 1.
            use_ai: Povolí použití AI pro složité případy. Default: False.
                Implementace ve Fázi 2 (Faker) a Fázi 3 (AI).

        Returns:
            Jeden slovník (pokud amount=1) nebo seznam slovníků (pokud amount>1).

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
        """
        # Validace: method vyžaduje endpoint
        if method and not endpoint:
            raise TalosForgeException("Parametr 'method' vyžaduje také parametr 'endpoint'.")

        # Validace: openapi_url vyžaduje endpoint
        if openapi_url and not endpoint:
            raise TalosForgeException(
                "Při použití openapi_url musí být specifikován i endpoint."
            )

        # Validace: musí být specifikován právě jeden zdroj
        # schema_path je jeden zdroj
        # endpoint (bez openapi_url) je jeden zdroj - použije načtené schéma
        # openapi_url s endpointem je jeden zdroj
        sources_specified = 0
        if schema_path:
            sources_specified += 1
        if endpoint and not openapi_url:
            sources_specified += 1
        if openapi_url:
            sources_specified += 1

        if sources_specified == 0:
            raise TalosForgeException(
                "Musí být specifikován alespoň jeden zdroj dat: "
                "schema_path, endpoint nebo openapi_url (s endpoint)"
            )
        if sources_specified > 1:
            raise TalosForgeException(
                "Musí být specifikován právě jeden zdroj dat, "
                "ne více najednou"
            )

        # Získání schématu ze zadaného zdroje
        schema = self._get_schema(schema_path, method, endpoint, openapi_url)

        # Generování dat pomocí DataGenerator (Fáze 2)
        results = []
        for _ in range(amount):
            generated = self.data_generator.generate(schema, target, use_ai)
            results.append(generated)

        # Vrácení jednoho slovníku nebo seznamu
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

            # Pokud endpoint obsahuje metodu, extrahujeme jen cestu
            parts = endpoint.split(None, 1)
            if len(parts) == 2:
                endpoint = parts[1]

            # Přidáme lomítko na začátek, pokud chybí
            if not endpoint.startswith('/'):
                endpoint = '/' + endpoint

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
    ) -> Dict[str, Any]:
        """
        Získá schéma ze zadaného zdroje.

        Args:
            schema_path: Cesta k JSON schématu.
            method: HTTP metoda (např. "POST", "GET").
            endpoint: Endpoint z načteného OpenAPI.
            openapi_url: URL k OpenAPI specifikaci.

        Returns:
            Slovník reprezentující JSON schéma.

        Raises:
            TalosForgeException: Pokud nelze získat schéma.
        """
        # Z lokálního JSON schématu
        if schema_path:
            return self.schema_loader.load_json_schema(schema_path)

        # Z URL OpenAPI (má přednost před načtenými schématy)
        if openapi_url:
            if not endpoint:
                raise TalosForgeException(
                    "Při použití openapi_url musí být specifikován i endpoint."
                )

            try:
                # Načíst specifikaci z URL
                spec = self.schema_loader.load_openapi_spec_from_url(openapi_url)

                # Extrakce endpoint schémat
                endpoint_schemas = self.schema_loader.extract_endpoint_schemas(spec)

                # Převíst method+endpoint na klíč
                endpoint_key = self._resolve_endpoint_key(method, endpoint)

                # Najít požadovaný endpoint
                if endpoint_key in endpoint_schemas:
                    return endpoint_schemas[endpoint_key]
                else:
                    available = list(endpoint_schemas.keys())
                    raise TalosForgeException(
                        f"Endpoint '{endpoint_key}' nebyl nalezen v "
                        f"OpenAPI specifikaci z {openapi_url}. "
                        f"Dostupné endpointy: {available}"
                    )
            except TalosForgeException:
                raise
            except Exception as e:
                raise TalosForgeException(f"Chyba při zpracování OpenAPI z {openapi_url}: {e}")

        # Z endpointu (vyžaduje načtené OpenAPI)
        if endpoint:
            if not self._loaded_openapi_schemas:
                raise TalosForgeException(
                    "Žádné OpenAPI schéma není načteno. "
                    "Nejprve použijte keyword 'Load Schema'."
                )

            # Převést method+endpoint na klíč
            endpoint_key = self._resolve_endpoint_key(method, endpoint)

            # Najdeme endpoint ve všech načtených schématech
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

        # Phase 3: openapi_url (zkontrolovat PŘED endpoint-only větví,
        # protože openapi_url používá endpoint+method jako podparametry)
        if openapi_url:
            raise NotImplementedError(
                "Validation against online OpenAPI URL is coming in Phase 3"
            )

        # Phase 2: endpoint (bez openapi_url)
        if endpoint:
            key = self._resolve_endpoint_key(method, endpoint)

            if not self._loaded_specs:
                raise TalosForgeException(
                    "Žádná OpenAPI specifikace není načtena. "
                    "Nejprve použijte keyword 'Load Schema'."
                )

            matched_spec = None
            response_schemas_for_key = None
            for spec in self._loaded_specs.values():
                response_schemas = self.schema_loader.extract_response_schemas(spec)
                if key in response_schemas:
                    matched_spec = spec
                    response_schemas_for_key = response_schemas[key]
                    break

            if matched_spec is None:
                raise TalosForgeException(
                    f"Endpoint '{key}' not found in any loaded OpenAPI spec"
                )

            if response_code not in response_schemas_for_key:
                available = sorted(response_schemas_for_key.keys())
                raise TalosForgeException(
                    f"No schema for status code {response_code}. "
                    f"Available: {available}"
                )

            schema = response_schemas_for_key[response_code]
            registry = self.schema_loader.build_registry(matched_spec)
            validator = SchemaValidator(schema, registry=registry)
            return validator.validate(data, return_errors=return_errors)

        raise TalosForgeException(
            "Musí být specifikován právě jeden zdroj: schema_path, endpoint nebo openapi_url"
        )

    def _generate_placeholder_data(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generuje placeholder data pro Fázi 1.

        Toto je dočasná metoda, která bude nahrazena plnohodnotným generátorem
        ve Fázi 2 (Faker) a Fázi 3 (AI).

        Args:
            schema: JSON schéma.

        Returns:
            Slovník s placeholder daty.
        """
        result = {}

        if schema.get("type") == "object":
            properties = schema.get("properties", {})
            for key, value_schema in properties.items():
                value_type = value_schema.get("type", "string")
                result[key] = f"generated_{key}_{value_type}"
        else:
            # Pro ne-objektové typy vrátíme jednoduchou hodnotu
            value_type = schema.get("type", "string")
            return f"generated_value_{value_type}"

        return result


__all__ = ["TalosForge"]
