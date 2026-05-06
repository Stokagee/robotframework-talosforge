"""
Načítání a parsování JSON a OpenAPI schémat.

Tento modul poskytuje SchemaLoader třídu pro načítání a parsování
JSON Schema a OpenAPI specifikací z lokálních souborů i URL.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Union

import requests
import yaml

from ..core.exceptions import TalosForgeException
from ..utils.cache import SimpleCache

logger = logging.getLogger(__name__)


class SchemaLoader:
    """
    Načítá a parsuje JSON Schema a OpenAPI specifikace.

    Tato třída poskytuje metody pro načítání schémat z různých zdrojů
    (lokální soubory, URL) a různých formátů (JSON, YAML).

    Example:
        >>> loader = SchemaLoader()
        >>> schema = loader.load_json_schema("user.json")
        >>> spec = loader.load_openapi_spec("api.yaml")
        >>> endpoints = loader.extract_endpoint_schemas(spec)
    """

    def __init__(self, use_cache: bool = True, cache_ttl: int = 3600):
        """
        Inicializuje SchemaLoader instanci.

        Args:
            use_cache: Používat cache pro URL specifikace. Default: True.
            cache_ttl: TTL pro cache v sekundách. Default: 3600 (1 hodina).
        """
        self._cache = SimpleCache(ttl=cache_ttl) if use_cache else None
        logger.debug(f"SchemaLoader inicializován s cache={use_cache}, ttl={cache_ttl}s")

    def load_json_schema(self, schema_path: str) -> Dict[str, Any]:
        """
        Načte JSON schéma ze souboru.

        Args:
            schema_path: Cesta k JSON souboru se schématem.

        Returns:
            Slovník reprezentující JSON schéma.

        Raises:
            TalosForgeException: Pokud soubor neexistuje nebo není platný JSON.

        Example:
            >>> loader = SchemaLoader()
            >>> schema = loader.load_json_schema("user.json")
            >>> print(schema["type"])
            'object'
        """
        path = Path(schema_path)

        if not path.exists():
            raise TalosForgeException(f"Soubor neexistuje: {schema_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            logger.debug(f"Načteno JSON schéma z: {schema_path}")
            return schema
        except json.JSONDecodeError as e:
            raise TalosForgeException(f"Neplatný JSON formát v souboru {schema_path}: {e}")
        except Exception as e:
            raise TalosForgeException(f"Chyba při čtení souboru {schema_path}: {e}")

    def load_openapi_spec(self, spec_path: str) -> Dict[str, Any]:
        """
        Načte OpenAPI specifikaci (JSON nebo YAML).

        Metoda automaticky detekuje formát podle přípony souboru.
        Podporuje .json, .yaml a .yml soubory.

        Args:
            spec_path: Cesta k OpenAPI souboru.

        Returns:
            Slovník reprezentující OpenAPI specifikaci.

        Raises:
            TalosForgeException: Pokud soubor neexistuje, má nepodporovaný formát
                nebo nelze parsovat.

        Example:
            >>> loader = SchemaLoader()
            >>> spec = loader.load_openapi_spec("petstore.yaml")
            >>> print(spec["info"]["title"])
            'Petstore API'
        """
        path = Path(spec_path)

        if not path.exists():
            raise TalosForgeException(f"Soubor neexistuje: {spec_path}")

        suffix = path.suffix.lower()

        try:
            with open(path, "r", encoding="utf-8") as f:
                if suffix == ".json":
                    spec = json.load(f)
                elif suffix in (".yaml", ".yml"):
                    spec = yaml.safe_load(f)
                else:
                    raise TalosForgeException(
                        f"Nepodporovaný formát souboru: {suffix}. "
                        "Podporované formáty: .json, .yaml, .yml"
                    )

            logger.debug(f"Načtena OpenAPI specifikace z: {spec_path}")
            return spec
        except json.JSONDecodeError as e:
            raise TalosForgeException(f"Neplatný JSON formát v souboru {spec_path}: {e}")
        except yaml.YAMLError as e:
            raise TalosForgeException(f"Neplatný YAML formát v souboru {spec_path}: {e}")
        except Exception as e:
            raise TalosForgeException(f"Chyba při čtení souboru {spec_path}: {e}")

    def _resolve_ref(self, spec: Dict[str, Any], ref: str) -> Dict[str, Any]:
        """
        Přeloží $ref reference v OpenAPI specifikaci.

        Podporuje:
        - #/components/schemas/SchemaName (OpenAPI 3.0)
        - #/definitions/SchemaName (Swagger 2.0)

        Args:
            spec: Kompletní OpenAPI specifikace
            ref: Reference string (např. "#/components/schemas/Courier")

        Returns:
            Rozlišené schéma

        Raises:
            TalosForgeException: Pokud reference neexistuje nebo je externí.

        Example:
            >>> loader = SchemaLoader()
            >>> spec = loader.load_openapi_spec("api.yaml")
            >>> schema = loader._resolve_ref(spec, "#/components/schemas/User")
            >>> print(schema["type"])
            'object'
        """
        # Kontrola externí reference
        if not ref.startswith("#/"):
            raise TalosForgeException(
                f"Externí reference nejsou podporovány: {ref}. "
                "Podporovány jsou jen interní reference začínající '#/'"
            )

        # Rozdělení reference na části
        parts = ref[2:].split("/")  # Odstranit "#/" a rozdělit
        current = spec

        # Navigace přes cestu
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                raise TalosForgeException(
                    f"Reference '{ref}' nebyla nalezena. "
                    f"Část '{part}' neexistuje."
                )

        # Validace výsledku
        if not isinstance(current, dict):
            raise TalosForgeException(
                f"Reference '{ref}' neukazuje na objekt, ale na {type(current).__name__}"
            )

        # Rekurzivně rozlišit vnořené $ref
        if "$ref" in current:
            logger.debug(f"Rekurzivní rozlišení reference: {current.get('$ref')}")
            return self._resolve_ref(spec, current["$ref"])

        logger.debug(f"Rozlišena reference: {ref}")
        return current

    def extract_endpoint_schemas(self, spec: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Extrahuje schémata z requestBody pro všechny endpointy v OpenAPI specifikaci.

        Metoda projde všechny cesty a metody v OpenAPI specifikaci a extrahuje
        schémata z requestBody. Vrací slovník kde klíčem je "METODA /cesta"
        a hodnotou je odpovídající schéma.

        Args:
            spec: OpenAPI specifikace jako slovník.

        Returns:
            Slovník ve formátu {"METODA /cesta": schema_dict}.
            Pokud endpoint nemá requestBody, není zahrnut ve výstupu.

        Raises:
            TalosForgeException: Pokud je specifikace neplatná.

        Example:
            >>> loader = SchemaLoader()
            >>> spec = loader.load_openapi_spec("api.yaml")
            >>> endpoints = loader.extract_endpoint_schemas(spec)
            >>> print(endpoints.keys())
            dict_keys(['POST /users', 'PUT /users/{id}'])
        """
        endpoints = {}

        # Získání paths části z OpenAPI specifikace
        paths = spec.get("paths", {})
        if not paths:
            raise TalosForgeException("OpenAPI specifikace neobsahuje žádné paths")

        # Procházení všech cest
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            # Procházení všech HTTP metod v cestě
            for method, method_spec in path_item.items():
                # Zajímají nás jen HTTP metody
                if method.lower() not in ("get", "post", "put", "patch", "delete", "options", "head"):
                    continue

                if not isinstance(method_spec, dict):
                    continue

                # Extrahování requestBody
                request_body = method_spec.get("requestBody")
                if not request_body:
                    continue

                # Získání content části
                content = request_body.get("content", {})
                if not content:
                    continue

                # Hledáme application/json nebo */*
                json_content = content.get("application/json") or content.get("*/*")
                if not json_content:
                    continue

                # Získání schématu
                schema = json_content.get("schema")
                if schema:
                    # Rozlišit $ref pokud existuje
                    if "$ref" in schema:
                        schema = self._resolve_ref(spec, schema["$ref"])

                    endpoint_key = f"{method.upper()} {path}"
                    endpoints[endpoint_key] = schema
                    logger.debug(f"Extrahováno schéma pro endpoint: {endpoint_key}")

        logger.info(f"Extrahováno {len(endpoints)} endpoint schémat")
        return endpoints

    def load_openapi_spec_from_url(self, spec_url: str) -> Dict[str, Any]:
        """
        Stáhne OpenAPI specifikaci z URL.

        Tato metoda stáhne OpenAPI specifikaci z URL, zkusí ji parsovat
        podle Content-Type nebo přípony a vrátí jako slovník.

        Args:
            spec_url: URL adresa OpenAPI specifikace.

        Returns:
            Slovník reprezentující OpenAPI specifikaci.

        Raises:
            TalosForgeException: Pokud stahování selže nebo nelze parsovat.

        Example:
            >>> loader = SchemaLoader()
            >>> spec = loader.load_openapi_spec_from_url("https://api.example.com/swagger.json")
            >>> print(spec["info"]["title"])
            'Example API'
        """
        # Zkusit cache
        if self._cache:
            cached = self._cache.get(spec_url)
            if cached is not None:
                logger.debug(f"Načteno z cache: {spec_url}")
                return cached

        try:
            # Stáhnout specifikaci
            response = requests.get(spec_url, timeout=30)
            response.raise_for_status()

            # Získat obsah
            content = response.text

            # Detekce formátu podle Content-Type
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                spec = json.loads(content)
            elif "application/yaml" in content_type or "text/yaml" in content_type:
                spec = yaml.safe_load(content)
            else:
                # Detekce podle přípony URL
                if spec_url.endswith(".json"):
                    spec = json.loads(content)
                elif spec_url.endswith(".yaml") or spec_url.endswith(".yml"):
                    spec = yaml.safe_load(content)
                else:
                    # Zkusit JSON jako výchozí
                    try:
                        spec = json.loads(content)
                    except json.JSONDecodeError:
                        spec = yaml.safe_load(content)

            # Uložit do cache
            if self._cache:
                self._cache.set(spec_url, spec)

            logger.info(f"Stažena OpenAPI specifikace z: {spec_url}")
            return spec

        except requests.exceptions.RequestException as e:
            raise TalosForgeException(f"Chyba při stahování z {spec_url}: {e}")
        except json.JSONDecodeError as e:
            raise TalosForgeException(f"Neplatný JSON formát v odpovědi z {spec_url}: {e}")
        except yaml.YAMLError as e:
            raise TalosForgeException(f"Neplatný YAML formát v odpovědi z {spec_url}: {e}")
        except Exception as e:
            raise TalosForgeException(f"Neočekávaná chyba při zpracování {spec_url}: {e}")

    @staticmethod
    def _normalize_response_key(status_code: str) -> Union[int, str, None]:
        """Normalize an OpenAPI response key to int (numeric), str (range/default), or None.

        Accepted forms:
        - "200" → 200
        - "2XX"/"2xx" → "2XX" (1XX-5XX only)
        - "default" → "default"
        Anything else returns None.
        """
        if not isinstance(status_code, str):
            return None
        if status_code == "default":
            return "default"
        if re.fullmatch(r"[1-5][xX]{2}", status_code):
            return status_code.upper()
        try:
            return int(status_code)
        except ValueError:
            return None

    def extract_response_schemas(
        self, spec: Dict[str, Any]
    ) -> Dict[str, Dict[Union[int, str], Dict[str, Any]]]:
        """
        Extrahuje response schémata z OpenAPI 3.0 specifikace.

        Vrací slovník mapující "METHOD /path" na {status_key: schema}, kde
        status_key je:
        - int — explicitní numerický kód (200, 404, ...)
        - str "1XX".."5XX" — range kód (vždy normalizovaný na uppercase)
        - str "default" — fallback definice

        Validace s fallbackem (numeric → range → default) je řešena ve
        validate_data_against_schema (TalosForge.__init__).

        Schémata se vrací beze změny — $refs nejsou pre-resolvnuty.
        Pro $ref resolution použij build_registry() a předej ho do
        SchemaValidator (Possibility B per IMPLEMENTATION_PLAN.md §3.2).

        Args:
            spec: OpenAPI 3.0 specifikace.

        Returns:
            Slovník {"METHOD /path": {status_key: schema}}.
            Endpointy bez rozpoznatelných response kódů nebo bez
            application/json content nejsou zahrnuty.

        Raises:
            TalosForgeException: pokud spec neobsahuje paths.
        """
        result: Dict[str, Dict[Union[int, str], Dict[str, Any]]] = {}

        paths = spec.get("paths", {})
        if not paths:
            raise TalosForgeException("OpenAPI specifikace neobsahuje žádné paths")

        valid_methods = ("get", "post", "put", "patch", "delete", "options", "head")

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method, method_spec in path_item.items():
                if method.lower() not in valid_methods:
                    continue
                if not isinstance(method_spec, dict):
                    continue

                responses = method_spec.get("responses", {})
                response_schemas: Dict[Union[int, str], Dict[str, Any]] = {}
                for status_code, response_def in responses.items():
                    if not isinstance(response_def, dict):
                        continue
                    key = self._normalize_response_key(status_code)
                    if key is None:
                        continue

                    content = response_def.get("content", {})
                    json_content = content.get("application/json") or content.get("*/*")
                    if not json_content:
                        continue

                    schema = json_content.get("schema")
                    if schema:
                        response_schemas[key] = schema

                if response_schemas:
                    endpoint_key = f"{method.upper()} {path}"
                    result[endpoint_key] = response_schemas

        return result

    @staticmethod
    def resolve_response_schema(
        schemas: Dict[Union[int, str], Dict[str, Any]],
        response_code: int,
    ) -> Union[Dict[str, Any], None]:
        """Resolve a numeric response_code against a status→schema map.

        Resolution order: exact numeric → matching XX range bucket → default.
        Returns None if nothing matches.
        """
        if response_code in schemas:
            return schemas[response_code]
        bucket = f"{response_code // 100}XX"
        if bucket in schemas:
            return schemas[bucket]
        if "default" in schemas:
            return schemas["default"]
        return None

    def build_registry(self, spec: Dict[str, Any]):
        """
        Postaví referencing.Registry z OpenAPI specifikace pro $ref resolution.

        Components.schemas se hluboce zkopírují a každá komponenta se prožene
        SchemaValidator._enforce_strict (varianta (b) per Q1) — tj. registry
        rozlišuje refy na strict-ifikované verze, ale originální spec dict
        zůstává nezměněný.

        Args:
            spec: OpenAPI 3.0 specifikace (nebude mutována).

        Returns:
            referencing.Registry s root resource pod URI '' (relativní refy
            jako '#/components/schemas/User' se resolvnou skrz tuto registry).
        """
        from copy import deepcopy

        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012

        from ..validation.validator import SPEC_URI, SchemaValidator

        spec_copy = deepcopy(spec)
        components_schemas = spec_copy.get("components", {}).get("schemas", {})
        for comp_schema in components_schemas.values():
            SchemaValidator._enforce_strict(comp_schema)

        resource = Resource.from_contents(
            spec_copy, default_specification=DRAFT202012
        )
        return Registry().with_resource(uri=SPEC_URI, resource=resource)
