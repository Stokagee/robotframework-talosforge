# TalosForge: Validation Feature — Implementation Plan

> **Audience**: Claude Code (and human reviewer)
> **Branch**: `feat/validation-keyword`
> **Target version**: 0.4.0
> **Approach**: TDD (tests first, then implementation), incremental phases

---

## 1. Executive Summary

Přidáváme do TalosForge **druhý směr** schema-driven workflow: validaci dat proti
JSON Schema / OpenAPI 3.0 specifikaci. Knihovna se tím posune z čistého
generátoru na kompletní schema-driven test toolkit (gen + validate sdílí
schémata = single source of truth pro contract testing).

Nový Robot Framework keyword: `Validate Data Against Schema`

Nová Python metoda v `TalosForge` třídě: `validate_data_against_schema(...)`

### Key constraints (rozhodnuto uživatelem)

- **Strict validation always ON** — hardcoded, není to parametr.
  Vyhodí chybu když:
  - Pole v datech není ve schématu (`additionalProperties: false`)
  - Required pole chybí v datech
  - Typ neodpovídá, format selže, range mimo, atd. (standardní validace)
- **Default behavior**: raise s detailní chybovou hláškou (Robot test spadne s jasným důvodem)
- **Optional**: `return_errors=True` → vrátí list chyb místo raise
- **OpenAPI verze**: pouze 3.0 (3.1 se může přidat později)
- **Format**: pouze JSON (jiné media types později)
- **Validation scope**: response body (Phase 1-3), request body + headers + query params (Phase 4+)
- **Negative data generation**: design extensibility teď, implementace později (Phase 5)

---

## 2. Library Choice: `openapi-schema-validator`

### Decision

**Použít `openapi-schema-validator>=0.7.0`**, který staví nad `jsonschema>=4.18.0`.

### Rationale

| Knihovna | Pros | Cons | Verdikt |
|----------|------|------|---------|
| `jsonschema` (samotná) | Lightweight, standard | Nezvládá OAS 3.0 specifika (`nullable`, format `int32`/`binary`) | ❌ Nedostatečné |
| `openapi-core` | Full-stack OpenAPI | Heavyweight, řeší server-side wrapping | ❌ Overkill |
| `jsonschema-rs` | 40-200× rychlejší | Rust binding, OAS 3.0 dialect podporuje hůře | ❌ Zbytečné |
| **`openapi-schema-validator`** | **Dedikovaný `OAS30Validator`, native `nullable` support, integrace s `jsonschema` registry** | — | ✅ **Use this** |

### Klíčové API patterns

```python
from openapi_schema_validator import OAS30Validator
from jsonschema.exceptions import ValidationError

# Raise mode (první chyba)
OAS30Validator(schema).validate(instance)

# Iterate all errors (return mode)
errors = list(OAS30Validator(schema).iter_errors(instance))

# Each error has rich context:
# - error.message     : human-readable
# - error.path        : deque of path segments, e.g. deque(['users', 0, 'email'])
# - error.schema_path : path within the schema
# - error.validator   : which keyword failed ('type', 'required', 'format', ...)
# - error.instance    : the actual value that failed
# - error.validator_value : the constraint value (e.g. 'email' for format)
```

### $ref resolution via Registry

Pro OpenAPI specs s `$ref: '#/components/schemas/User'` musíme postavit
`referencing.Registry` z plné OpenAPI specifikace:

```python
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012  # works for OAS 3.0 too

def build_registry(spec: dict) -> Registry:
    """Build a jsonschema Registry from full OpenAPI spec for $ref resolution."""
    resource = Resource.from_contents(spec, default_specification=DRAFT202012)
    return Registry().with_resource(uri="", resource=resource)

# Usage
registry = build_registry(openapi_spec)
validator = OAS30Validator(schema, registry=registry)
validator.validate(instance)
```

**Důležité**: `referencing` knihovna je už dependency `jsonschema>=4.18.0`. Žádná
dodatečná dependency.

---

## 3. Critical Findings in Existing Code

### 3.1 `loader.py` — chybí response schema extraction

**Současný stav** (`extract_endpoint_schemas`, řádky 130-184):
- Extrahuje **pouze request body** schémata
- Vrací: `{"POST /users": <request_body_schema>}`
- **Pro validaci nedostatečné** — chceme primárně response schémata

**Potřebná změna**: nová metoda nebo rozšíření existující, aby vracela:

```python
{
    "POST /users": {
        "request": <schema>,                    # nepovinné, jen pokud requestBody existuje
        "responses": {
            200: <schema>,
            201: <schema>,
            400: <schema>,
            ...
        }
    }
}
```

OpenAPI 3.0 struktura responses:
```yaml
paths:
  /users:
    post:
      requestBody: {...}
      responses:
        '201':
          content:
            application/json:
              schema: {...}
        '400':
          content:
            application/json:
              schema: {...}
```

### 3.2 `loader.py` — částečné $ref resolution (jen top-level)

**Současný stav** (`_resolve_ref`, `loader.py:132`): top-level `$ref` chains se
resolvují rekurzivně (ref → ref → ref). `extract_endpoint_schemas` (řádek 258)
volá `_resolve_ref` na schéma vrácené z `requestBody.content.application/json.schema`,
takže pokud je tam `{"$ref": "#/components/schemas/User"}`, dostaneme expandovaný
User. **Ale**: nested `$ref` uvnitř properties (např. `User.address: {$ref: ...}`)
se **nesubstituují** — loader nechodí dovnitř schématu a refy uvnitř zůstávají
jako literály.

**Pro validaci**: nested refy musí být řešitelné při validaci. Dvě možnosti:
- (A) Resolvovat všechny refy v loaderu před vrácením schématu (deep substitution)
- (B) Předat plnou spec validátoru přes Registry (refy se resolvnou při validaci)

**Rozhodnuto: (B)** — méně invazivní, neporušuje existující generator chování,
respektuje `referencing` knihovnu, kterou má `jsonschema` 4.18+ jako dependency.

### 3.3 `generator.py` — `nullable: true` se ignoruje (helper existuje, ale není zapojený)

**Současný stav**: `_is_nullable()` (`generator.py:540`) **existuje** a vrací
správně `schema.get("nullable", False)`. Docstring slibuje 20% None probability.
**Ale**: nikdo `_is_nullable` nevolá — `_generate_object` (řádky 1270–1292) prochází
properties a vždy generuje hodnotu, nullable flag ignoruje. Funkce je hluchá větev.

**Implikace pro validaci**: Round-trip test (Generate → Validate) na schématu
s `nullable: true` neodhalí — generátor totiž nikdy None nevrátí, takže validace
proti `nullable: true` projde (stejně non-null hodnota je validní). Skutečná díra
se ukáže až při testu, kde `nullable: true` slíbil 20% None a tester to měří.
**Toto NENÍ úkol pro tento PR**, ale měl by se založit issue.

### 3.4 `generator.py` — `_handle_oneof_anyof_allof` se nikdy nevolá

V `generate()` dispatcheru (`generator.py:433–508`) chybí větev pro
oneOf/anyOf/allOf. Metoda `_handle_oneof_anyof_allof` (`generator.py:1318`)
existuje, ale nikdy se nevolá. S `use_ai=True` to AI nahradí přes `_should_use_ai`
(eskaluje pokud jsou oneOf/anyOf/allOf, `generator.py:1399`). S default `use_ai=False`
schéma typu `{oneOf: [...]}` nemá `type` a vrátí `None` (řádek 491).
Round-trip test to odhalí. **Také mimo scope tohoto PR**.

### 3.5 Konzistence: generator + validator musí používat stejnou cestu k schématu

Pokud uživatel zavolá:
```robotframework
Load Schema    swagger_path=./api.yaml
${data}=    Generate Data From Schema    method=POST    endpoint=/users
Validate Data Against Schema    ${data}    method=POST    endpoint=/users
```

…musí oba keywordy resolvovat schéma identicky. Implementace musí sdílet
`SchemaLoader` instanci a její cache.

---

## 4. New Module Structure

```
TalosForge/
├── validation/                          # NEW
│   ├── __init__.py
│   ├── validator.py                     # SchemaValidator class
│   ├── error_formatter.py               # ValidationError → human-readable string / dict
│   └── exceptions.py                    # DataValidationError(TalosForgeException)
│
├── schema/
│   └── loader.py                        # MODIFY: add extract_response_schemas() + extract_full_endpoint_info()
│
├── core/
│   └── exceptions.py                    # MODIFY: pokud bude potřeba dědičnost
│
└── __init__.py                          # MODIFY: add validate_data_against_schema() method to TalosForge class
```

---

## 5. Final API Design

### 5.1 Robot Framework keyword

```robotframework
*** Keywords ***

# Plný signature
${result}=    Validate Data Against Schema
...    data=${data}                        # REQUIRED: data k validaci (dict or list)
...    schema_path=${EMPTY}                # Source 1: cesta k JSON Schema souboru
...    endpoint=${EMPTY}                   # Source 2: endpoint v OpenAPI (vyžaduje předchozí Load Schema)
...    method=${EMPTY}                     # HTTP metoda pro endpoint (POST, GET, ...)
...    openapi_url=${EMPTY}                # Source 3: URL k OpenAPI spec
...    response_code=200                   # Který response status code (default 200)
...    return_errors=${False}              # True = vrátí list chyb místo raise
```

### 5.2 Python signature

```python
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
    Validates data against a JSON Schema or OpenAPI response schema.

    Strict validation is always enabled:
    - Extra fields not in schema → error
    - Missing required fields → error
    - Type/format/range mismatches → error

    Source priority (exactly one must be specified):
    1. schema_path — local JSON Schema file
    2. endpoint (+ method) — endpoint from previously loaded OpenAPI spec
    3. openapi_url (+ endpoint + method) — online OpenAPI spec

    Returns:
        None if return_errors=False and validation passes
        List of error dicts if return_errors=True (empty list = valid)

    Raises:
        DataValidationError: if return_errors=False and validation fails
        TalosForgeException: if source is invalid or schema not found
    """
```

### 5.3 Error format (return_errors=True)

```python
[
    {
        "path": "$.users[0].email",       # JSONPath-like for human reading
        "path_parts": ["users", 0, "email"],  # programmatic access
        "message": "'foo' is not a 'email'",
        "validator": "format",
        "validator_value": "email",
        "instance": "foo",
    },
    ...
]
```

### 5.4 Error format (raise mode)

```
DataValidationError: Validation failed with 2 error(s):
  - $.users[0].email: 'foo' is not a 'email' (validator: format)
  - $.users[1].age: -5 is less than the minimum of 0 (validator: minimum)
```

---

## 6. Implementation Phases

Každá fáze = samostatný PR / commit set, vlastní testy první.

### Phase 1: Core validator + JSON Schema source (`schema_path`)

**Goal**: Validate data against a local JSON Schema file. No OpenAPI yet.

**Deliverables**:
- `TalosForge/validation/exceptions.py` — `DataValidationError`
- `TalosForge/validation/error_formatter.py` — formátování chyb
- `TalosForge/validation/validator.py` — `SchemaValidator` třída (wraps OAS30Validator)
- `TalosForge/__init__.py` — nová metoda `validate_data_against_schema()` (jen větev `schema_path`)
- pyproject.toml — přidat `openapi-schema-validator>=0.7.0`

**Tests** (write first):
- `tests/unit/test_validator.py` — pytest pro `SchemaValidator` třídu
- `tests/unit/test_error_formatter.py` — pytest pro formátování
- `tests/robot/test_validation_phase1.robot` — Robot smoke testy

### Phase 2: OpenAPI 3.0 endpoint source (loaded spec)

**Goal**: Validate against response schema z `Load Schema` + `endpoint` + `method`.

**Deliverables**:
- `TalosForge/schema/loader.py` — nová metoda `extract_response_schemas(spec)` →
  `{"POST /users": {200: schema, 201: schema, ...}}`
- `TalosForge/schema/loader.py` — nová metoda `build_registry(spec)` pro $ref resolution
- `TalosForge/__init__.py` — rozšířit `validate_data_against_schema()` o `endpoint`/`method`/`response_code`
- `TalosForge/validation/validator.py` — accept registry parameter

**Tests** (write first):
- `tests/unit/test_loader_responses.py` — extract_response_schemas, $ref handling
- `tests/unit/test_validator_with_refs.py` — validace s OpenAPI specs obsahujícími $refs
- `tests/robot/test_validation_phase2.robot` — round-trip Generate→Validate test

### Phase 3: Online OpenAPI URL source

**Goal**: `openapi_url` parameter — stáhnout spec z URL a validovat.

**Deliverables**:
- Recyklace existující `load_openapi_spec_from_url()` v loaderu
- `TalosForge/__init__.py` — rozšířit `validate_data_against_schema()` o `openapi_url` větev
- Reuse cache mechanism (už existuje v `SimpleCache`)
- Refactor `_validate_against_spec` private helper sdílený s endpoint branch (§9.3)
- Branch reorder fix: `openapi_url` check **před** `endpoint` check (§9.3)

**Tests**:
- `tests/integration/test_validation_url.py` — 9 tests s `responses>=0.23` lib pro HTTP mock
- `tests/robot/test_validation_phase3.robot` — 3 tests s `python -m http.server` startovaným přes `Process` library v Suite Setup

**Notes** (drobné odchylky od plánu):
- Plán očekával ~10 pytest tests, finální count je 9. Dropnutý `test_timeout_handling`
  — `responses` lib's RequestException simulation pro timeout je awkward (skutečný
  network timeout neumí mockovat čistě). 404 + invalid YAML testy pokrývají
  `requests.exceptions.RequestException` catch-all větev v `load_openapi_spec_from_url`
  efektivně. Net coverage equivalent.

### Phase 4 (later): Request body, query params, headers, jiné media types

**Out of scope for v0.4.0.** Designově ale příprava:
- `validate_data_against_schema()` může v budoucnu mít parametr `target="response" | "request" | "query" | "header"`
- Loader bude mít `extract_full_endpoint_info()` vracející kompletní strukturu

### Phase 5 (later): Negative data generation

**Out of scope for v0.3.0.** Designově:
- Nový keyword `Generate Invalid Data From Schema`
- Strategie: vyber random required pole → vynech ho; vyber random pole → poruš typ;
  přidej extra pole s random klíčem
- Reuse `SchemaValidator` pro self-check (vygenerovaná data MUSÍ failnout validaci)

---

## 7. TDD Test Plan (Phase 1 detail)

Toto je nejdůležitější část — Claude Code by měl psát tyto testy PŘED implementací.

### 7.1 `tests/unit/test_validator.py`

```python
import pytest
from TalosForge.validation.validator import SchemaValidator
from TalosForge.validation.exceptions import DataValidationError


class TestSchemaValidatorHappyPath:
    def test_valid_simple_object(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        SchemaValidator(schema).validate({"name": "Jan"})  # nesmí raise

    def test_valid_with_optional_fields(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],
        }
        SchemaValidator(schema).validate({"name": "Jan", "age": 30})

    def test_valid_nested_object(self):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {"email": {"type": "string", "format": "email"}},
                    "required": ["email"],
                }
            },
        }
        SchemaValidator(schema).validate({"user": {"email": "x@y.cz"}})

    def test_valid_array_of_objects(self):
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "integer"}},
                "required": ["id"],
            },
        }
        SchemaValidator(schema).validate([{"id": 1}, {"id": 2}])


class TestSchemaValidatorStrictMode:
    """Strict mode is ALWAYS on. These tests verify it cannot be bypassed."""

    def test_extra_field_raises(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        with pytest.raises(DataValidationError) as exc:
            SchemaValidator(schema).validate({"name": "Jan", "extra": "x"})
        assert "extra" in str(exc.value).lower()

    def test_missing_required_raises(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "email": {"type": "string"}},
            "required": ["name", "email"],
        }
        with pytest.raises(DataValidationError) as exc:
            SchemaValidator(schema).validate({"name": "Jan"})
        assert "email" in str(exc.value).lower()
        assert "required" in str(exc.value).lower()

    def test_wrong_type_raises(self):
        schema = {"type": "object", "properties": {"age": {"type": "integer"}}}
        with pytest.raises(DataValidationError):
            SchemaValidator(schema).validate({"age": "thirty"})

    def test_invalid_format_email_raises(self):
        schema = {
            "type": "object",
            "properties": {"email": {"type": "string", "format": "email"}},
        }
        with pytest.raises(DataValidationError):
            SchemaValidator(schema).validate({"email": "not-an-email"})

    def test_below_minimum_raises(self):
        schema = {
            "type": "object",
            "properties": {"age": {"type": "integer", "minimum": 0}},
        }
        with pytest.raises(DataValidationError):
            SchemaValidator(schema).validate({"age": -5})

    def test_above_maximum_raises(self):
        schema = {
            "type": "object",
            "properties": {"age": {"type": "integer", "maximum": 150}},
        }
        with pytest.raises(DataValidationError):
            SchemaValidator(schema).validate({"age": 200})

    def test_string_too_short_raises(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string", "minLength": 3}},
        }
        with pytest.raises(DataValidationError):
            SchemaValidator(schema).validate({"name": "ab"})

    def test_strict_applies_to_nested_objects(self):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            },
        }
        with pytest.raises(DataValidationError):
            SchemaValidator(schema).validate({"user": {"name": "Jan", "extra": "x"}})


class TestSchemaValidatorReturnErrors:
    def test_return_errors_empty_on_valid(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        errors = SchemaValidator(schema).validate(
            {"name": "Jan"}, return_errors=True
        )
        assert errors == []

    def test_return_errors_lists_all_failures(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0},
                "email": {"type": "string", "format": "email"},
            },
            "required": ["name", "email"],
        }
        errors = SchemaValidator(schema).validate(
            {"age": -5, "email": "bad"}, return_errors=True
        )
        # missing name (required), age below minimum, bad email format
        assert len(errors) >= 3

    def test_error_dict_structure(self):
        schema = {
            "type": "object",
            "properties": {"email": {"type": "string", "format": "email"}},
        }
        errors = SchemaValidator(schema).validate(
            {"email": "bad"}, return_errors=True
        )
        err = errors[0]
        assert "path" in err
        assert "message" in err
        assert "validator" in err
        assert err["validator"] == "format"


class TestSchemaValidatorOAS30Specifics:
    def test_nullable_true_accepts_none(self):
        schema = {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "nullable": True}
            },
        }
        SchemaValidator(schema).validate({"lat": None})

    def test_nullable_false_rejects_none(self):
        schema = {
            "type": "object",
            "properties": {"lat": {"type": "number"}},
        }
        with pytest.raises(DataValidationError):
            SchemaValidator(schema).validate({"lat": None})

    def test_int32_format_accepts_integer(self):
        schema = {
            "type": "object",
            "properties": {"id": {"type": "integer", "format": "int32"}},
        }
        SchemaValidator(schema).validate({"id": 42})


class TestSchemaValidatorEnum:
    def test_valid_enum_value(self):
        schema = {
            "type": "object",
            "properties": {"role": {"type": "string", "enum": ["admin", "user"]}},
        }
        SchemaValidator(schema).validate({"role": "admin"})

    def test_invalid_enum_value_raises(self):
        schema = {
            "type": "object",
            "properties": {"role": {"type": "string", "enum": ["admin", "user"]}},
        }
        with pytest.raises(DataValidationError):
            SchemaValidator(schema).validate({"role": "superadmin"})
```

### 7.2 `tests/unit/test_error_formatter.py`

```python
def test_format_path_jsonpath_style():
    from TalosForge.validation.error_formatter import format_path
    assert format_path(["users", 0, "email"]) == "$.users[0].email"
    assert format_path([]) == "$"
    assert format_path(["name"]) == "$.name"

def test_format_error_to_dict():
    # Test conversion of jsonschema.ValidationError to our error dict format
    ...

def test_format_errors_to_message():
    # Test multi-error message construction
    ...
```

### 7.3 `tests/robot/test_validation_phase1.robot`

> **Pozor — fixture path**: Použij `${CURDIR}${/}..${/}fixtures${/}user.json`,
> ne `./tests/fixtures/user.json`. Robot Framework `${CURDIR}` se rozvine na
> umístění `.robot` souboru, takže path je relocatable nezávisle na tom, odkud
> se `robot` spouští. Plain relative path `./tests/...` selže, pokud uživatel
> spustí `robot` z jiné working directory.
>
> **Pozor — Length Should Be Greater Than neexistuje**: V Robot Framework
> Collections lib není keyword `Length Should Be Greater Than`. Pro check
> neprázdného seznamu stačí `Should Not Be Empty`. Pokud potřebuješ exact
> length, použij `Length Should Be    ${list}    N`.

```robotframework
*** Settings ***
Library     TalosForge
Library     Collections

*** Variables ***
${VALID_USER}       {"username": "honza123", "email": "honza@example.cz", "age": 25}
${INVALID_USER}     {"username": "x", "email": "not-email", "age": 200}

*** Test Cases ***
Validate Valid Data Passes
    ${data}=    Evaluate    ${VALID_USER}
    Validate Data Against Schema    data=${data}    schema_path=${CURDIR}${/}..${/}fixtures${/}user.json
    # No exception = pass

Validate Invalid Data Raises
    ${data}=    Evaluate    ${INVALID_USER}
    Run Keyword And Expect Error    *Validation failed*
    ...    Validate Data Against Schema    data=${data}    schema_path=${CURDIR}${/}..${/}fixtures${/}user.json

Validate With Return Errors Returns List
    ${data}=    Evaluate    ${INVALID_USER}
    ${errors}=    Validate Data Against Schema
    ...    data=${data}    schema_path=${CURDIR}${/}..${/}fixtures${/}user.json    return_errors=${True}
    Should Not Be Empty    ${errors}

Validate Empty Errors For Valid Data
    ${data}=    Evaluate    ${VALID_USER}
    ${errors}=    Validate Data Against Schema
    ...    data=${data}    schema_path=${CURDIR}${/}..${/}fixtures${/}user.json    return_errors=${True}
    Should Be Empty    ${errors}

Generate Then Validate Round Trip
    # Critical test: generated data must pass its own schema's validation
    ${data}=    Generate Data From Schema    schema_path=${CURDIR}${/}..${/}fixtures${/}user.json
    Validate Data Against Schema    data=${data}    schema_path=${CURDIR}${/}..${/}fixtures${/}user.json
```

### 7.4 Test fixtures

Vytvořit `tests/fixtures/user.json`:
```json
{
  "type": "object",
  "properties": {
    "username": {"type": "string", "minLength": 5, "maxLength": 20},
    "email": {"type": "string", "format": "email"},
    "age": {"type": "integer", "minimum": 18, "maximum": 99}
  },
  "required": ["username", "email"]
}
```

> **Pozor — round-trip determinismus**: Test fixtures pro round-trip testy
> (Generate → Validate na stejném schématu) NESMÍ obsahovat `description`,
> dlouhý `pattern` (>20 znaků), ani `oneOf/anyOf/allOf`. Tyto triggery
> aktivují AI escalation v `_should_use_ai()` (`TalosForge/core/generator.py:1366`)
> při `use_ai=True` a způsobí flaky chování (nedeterministická data → občasný
> validation fail). Round-trip test musí být plně deterministický.
>
> JSON komentáře neexistují, takže tohle varování dej jako modul-level docstring
> v Python testovacím souboru, kde se fixture používá.

---

## 8. Implementation Skeleton (after tests are written)

### 8.1 `TalosForge/validation/exceptions.py`

```python
from typing import List, Dict, Any, Optional
from ..core.exceptions import TalosForgeException


class DataValidationError(TalosForgeException):
    """Raised when data validation against schema fails (strict mode)."""

    def __init__(self, message: str, errors: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message)
        self.errors = errors or []
```

### 8.2 `TalosForge/validation/error_formatter.py`

```python
from typing import List, Dict, Any
from collections import deque
from jsonschema.exceptions import ValidationError


def format_path(path_parts) -> str:
    """Convert path deque/list to JSONPath-like string.

    Examples:
        []                      -> "$"
        ["users"]               -> "$.users"
        ["users", 0, "email"]   -> "$.users[0].email"
    """
    if not path_parts:
        return "$"
    result = "$"
    for part in path_parts:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += f".{part}"
    return result


def error_to_dict(error: ValidationError) -> Dict[str, Any]:
    """Convert jsonschema.ValidationError to our serializable dict."""
    path_parts = list(error.absolute_path)
    return {
        "path": format_path(path_parts),
        "path_parts": path_parts,
        "message": error.message,
        "validator": error.validator,
        "validator_value": error.validator_value,
        "instance": error.instance,
    }


def errors_to_message(errors: List[Dict[str, Any]]) -> str:
    """Build human-readable multi-error message for raise mode."""
    if not errors:
        return "Validation passed"
    lines = [f"Validation failed with {len(errors)} error(s):"]
    for err in errors:
        lines.append(
            f"  - {err['path']}: {err['message']} (validator: {err['validator']})"
        )
    return "\n".join(lines)
```

### 8.3 `TalosForge/validation/validator.py`

> **Pozor — format_checker je vyžadovaný**: Bez explicitního
> `format_checker=oas30_format_checker` při instanci `OAS30Validator`
> se **format constraints (`email`, `uuid`, `int32`, `date-time`, ...) tiše
> přeskakují**. Test `test_invalid_format_email_raises` to odhalí — schéma
> s `format: email` a hodnotou `"not-an-email"` neprodukuje žádnou chybu.
> Vždy ho předej.

```python
from typing import Any, Dict, List, Optional, Union
from copy import deepcopy
from openapi_schema_validator import OAS30Validator, oas30_format_checker
from referencing import Registry

from .exceptions import DataValidationError
from .error_formatter import error_to_dict, errors_to_message


class SchemaValidator:
    """
    Validates data against a JSON Schema or OpenAPI 3.0 schema.

    Strict mode is ALWAYS enabled — additionalProperties: false is enforced
    on all objects, even if the schema doesn't specify it.
    """

    def __init__(
        self,
        schema: Dict[str, Any],
        registry: Optional[Registry] = None,
    ):
        self.schema = self._enforce_strict(deepcopy(schema))
        self.registry = registry
        validator_kwargs = {"format_checker": oas30_format_checker}
        if registry is not None:
            validator_kwargs["registry"] = registry
        self._validator = OAS30Validator(self.schema, **validator_kwargs)

    @staticmethod
    def _enforce_strict(schema: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively set additionalProperties: false on all object schemas."""
        if not isinstance(schema, dict):
            return schema
        if schema.get("type") == "object" or "properties" in schema:
            schema.setdefault("additionalProperties", False)
            for prop_schema in schema.get("properties", {}).values():
                SchemaValidator._enforce_strict(prop_schema)
        if schema.get("type") == "array" and "items" in schema:
            SchemaValidator._enforce_strict(schema["items"])
        # Handle composition keywords
        for key in ("oneOf", "anyOf", "allOf"):
            if key in schema:
                for sub in schema[key]:
                    SchemaValidator._enforce_strict(sub)
        return schema

    def validate(
        self,
        data: Any,
        return_errors: bool = False,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Validate data against the schema.

        Args:
            data: data to validate
            return_errors: if True, return list of error dicts; if False, raise on failure

        Returns:
            None if return_errors=False and validation passes
            List of error dicts if return_errors=True (empty = valid)

        Raises:
            DataValidationError: if return_errors=False and validation fails
        """
        errors = [error_to_dict(e) for e in self._validator.iter_errors(data)]
        if return_errors:
            return errors
        if errors:
            raise DataValidationError(errors_to_message(errors), errors=errors)
        return None
```

### 8.4 Modifikace `TalosForge/__init__.py`

**Existující stav (`__init__.py:38–43`)**:
- Loader instance: `self.schema_loader` (NE `self._loader`)
- Generator instance: `self.data_generator`
- Endpoint cache (pre-extracted request bodies): `self._loaded_openapi_schemas: Dict[str, Dict[str, Any]]`
- Helper pro endpoint key resolution: `self._resolve_endpoint_key(method, endpoint)` (`__init__.py:189`)
- Robot keyword decorator: `from robot.api.deco import keyword` — všechny veřejné keywords musí být `@keyword`-dekorované, jinak je Robot neuvidí

**Změny v `__init__`** (přidat cache plné spec pro Phase 2 validaci):

```python
def __init__(self):
    self.schema_loader = SchemaLoader()
    self.data_generator = DataGenerator()
    self._loaded_openapi_schemas: Dict[str, Dict[str, Any]] = {}
    self._loaded_specs: Dict[str, Dict[str, Any]] = {}  # NEW: full specs for validation
    logger.info("TalosForge inicializován")
```

**Změna v `load_schema`** (přidat uložení plné spec):

```python
@keyword
def load_schema(self, swagger_path: str, force_reload: bool = False) -> None:
    if not force_reload and swagger_path in self._loaded_openapi_schemas:
        return
    spec = self.schema_loader.load_openapi_spec(swagger_path)
    self._loaded_openapi_schemas[swagger_path] = (
        self.schema_loader.extract_endpoint_schemas(spec)
    )
    self._loaded_specs[swagger_path] = spec  # NEW
    # ... existing logging / error handling beze změny
```

> **Architektonické rozhodnutí (cache)**: Držíme plnou spec **vedle** existující
> pre-extrahované cache (Option 1 ze dvou alternativ). Důvod: scope tohohle PR
> je validace, ne refaktor loader cache. Refaktor (sloučit obě cache, generátor
> by extrahoval lazy) jako follow-up PR. Cena: dvojí držení spec v paměti
> (~<1MB i pro velká API), zanedbatelné.

**Přidat novou metodu** `validate_data_against_schema` (Phase 1 verze, jen `schema_path`):

```python
@keyword
def validate_data_against_schema(
    self,
    data,
    schema_path=None,
    endpoint=None,
    method=None,
    openapi_url=None,
    response_code=200,
    return_errors=False,
):
    """Validates data against a JSON Schema or OpenAPI 3.0 schema."""
    from .validation.validator import SchemaValidator

    # Phase 1: only schema_path
    if schema_path:
        schema = self.schema_loader.load_json_schema(schema_path)
        validator = SchemaValidator(schema)
        return validator.validate(data, return_errors=return_errors)

    # Phase 2: endpoint
    if endpoint:
        # ... TBD in Phase 2 (uses self._loaded_specs + self._resolve_endpoint_key)
        raise NotImplementedError("OpenAPI endpoint source coming in Phase 2")

    # Phase 3: openapi_url
    if openapi_url:
        raise NotImplementedError("OpenAPI URL source coming in Phase 3")

    raise TalosForgeException(
        "Must specify exactly one of: schema_path, endpoint, openapi_url"
    )
```

### 8.5 Modifikace `pyproject.toml`

```toml
[project]
dependencies = [
    # existing deps...
    "openapi-schema-validator>=0.7.0",
    # jsonschema and referencing come transitively
]
```

---

## 9. Phase 2 Detail — Loader Extension

### 9.1 New `extract_response_schemas()` method

```python
def extract_response_schemas(
    self, spec: Dict[str, Any]
) -> Dict[str, Dict[int, Dict[str, Any]]]:
    """
    Extract response schemas from OpenAPI 3.0 spec.

    Returns:
        Dict mapping "METHOD /path" → {status_code: schema}.

    Example:
        >>> loader.extract_response_schemas(spec)
        {
            "POST /users": {201: {...}, 400: {...}},
            "GET /users/{id}": {200: {...}, 404: {...}}
        }

    Pozn.: 'default', '2XX', '4XX' a non-numerické response kódy se ignorují.
    Tracked jako follow-up: GitHub issue link patří jako code comment u tohoto
    chování (per Q4 rozhodnutí — out of scope pro Phase 2).

    Schémata se vrací as-is — $refs nejsou pre-resolvnuty (Possibility B per §3.2).
    Pro $ref resolution se používá build_registry() + SchemaValidator s registry.
    """
    result = {}
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
            response_schemas = {}
            for status_code, response_def in responses.items():
                if not isinstance(response_def, dict):
                    continue
                # status_code can be string ("200"), "default", or "2XX"
                # For Phase 1: only handle numeric status codes
                try:
                    code = int(status_code)
                except (ValueError, TypeError):
                    continue

                content = response_def.get("content", {})
                json_content = content.get("application/json") or content.get("*/*")
                if not json_content:
                    continue

                schema = json_content.get("schema")
                if schema:
                    response_schemas[code] = schema

            if response_schemas:
                key = f"{method.upper()} {path}"
                result[key] = response_schemas

    return result
```

### 9.2 New `build_registry()` method

> **Pozor — empty URI nefunguje, fragment rewrite je mandatory**
>
> Naivní pattern `Registry().with_resource(uri="", resource=resource)` (původní plán)
> **selhává s `PointerToNowhere`**, protože `OAS30Validator(schema, registry=registry)`
> bere validovanou `schema` jako svůj „current resource" a `$ref: "#/..."` resolvuje
> *uvnitř ní*, ne přes registry. Registered resource pod `uri=""` se neuplatní,
> protože reference není absolutní.
>
> Reprodukce (testováno na `referencing 0.37` + `openapi-schema-validator 0.9`):
> ```
> uri="":           PointerToNowhere: '/components/schemas/User' does not exist
>                   within {'$ref': '#/components/schemas/User'}
> uri="urn:tf:spec" + absolute ref:  PASS
> ```
>
> **Řešení**: dvoukrokové.
> 1. Sdílená konstanta `SPEC_URI = "urn:talosforge:spec"` v `validation/validator.py`,
>    importovaná v `loader.py`. Registry registruje resource pod tímto URI.
> 2. `SchemaValidator._rewrite_fragment_refs(node, base_uri)` rekurzivně přepíše
>    všechny `{"$ref": "#/..."}` na `{"$ref": "<base_uri>#/..."}` v deepcopy
>    schématu, **před** předáním do `OAS30Validator`. Volá se z `__init__` jen
>    když je registry předaný.
>
> Bez obojího je `build_registry` non-functional — testy `test_top_level_ref_resolves_via_registry`
> a všechny ostatní `TestSchemaValidator*` s registry padnou.

#### 9.2.1 `SPEC_URI` konstanta (v `validation/validator.py`)

```python
# URI used by SchemaLoader.build_registry to register the OpenAPI spec, and
# by SchemaValidator to rewrite fragment-only $refs into absolute references.
SPEC_URI = "urn:talosforge:spec"
```

#### 9.2.2 `_rewrite_fragment_refs` static method (přidat do `SchemaValidator`)

```python
@staticmethod
def _rewrite_fragment_refs(node: Any, base_uri: str) -> None:
    """In-place rewrite of fragment-only $refs to absolute base_uri#... form.

    Walks the schema and replaces every {"$ref": "#/..."} with
    {"$ref": "<base_uri>#/..."} so OAS30Validator resolves them via
    the registry instead of treating them as fragments of the current
    schema. Refs that are already absolute (have a scheme) are left alone.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            if (
                key == "$ref"
                and isinstance(value, str)
                and value.startswith("#")
            ):
                node[key] = base_uri + value
            else:
                SchemaValidator._rewrite_fragment_refs(value, base_uri)
    elif isinstance(node, list):
        for item in node:
            SchemaValidator._rewrite_fragment_refs(item, base_uri)
```

A volání v `__init__` (po `_enforce_strict`, před stavbou validátoru):

```python
self.schema = self._enforce_strict(deepcopy(schema))
self.registry = registry
if registry is not None:
    self._rewrite_fragment_refs(self.schema, SPEC_URI)
validator_kwargs = {"format_checker": oas30_format_checker}
if registry is not None:
    validator_kwargs["registry"] = registry
self._validator = OAS30Validator(self.schema, **validator_kwargs)
```

#### 9.2.3 `build_registry()` se SPEC_URI

```python
def build_registry(self, spec: Dict[str, Any]):
    """
    Build a referencing.Registry from full OpenAPI spec for $ref resolution.

    Components.schemas are deep-copied and each component is strict-ified
    via SchemaValidator._enforce_strict (Q1 variant (b)). Registry registers
    the spec resource under SPEC_URI so absolute refs from rewritten schemas
    resolve correctly.
    """
    from copy import deepcopy
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
    from ..validation.validator import SPEC_URI, SchemaValidator

    spec_copy = deepcopy(spec)
    components_schemas = spec_copy.get("components", {}).get("schemas", {})
    for comp_schema in components_schemas.values():
        SchemaValidator._enforce_strict(comp_schema)

    resource = Resource.from_contents(spec_copy, default_specification=DRAFT202012)
    return Registry().with_resource(uri=SPEC_URI, resource=resource)
```

### 9.3 Phase 2 + Phase 3 update to `validate_data_against_schema()`

> **Dispatch order rule (mandatory)**: branche se musí zkontrolovat v pořadí
> **`openapi_url` > `endpoint` > `schema_path`**.
>
> Důvod: `openapi_url` používá `endpoint` + `method` jako podparametry. Pokud
> `endpoint` check přijde první, tak když uživatel zavolá s oběma (URL i
> endpoint), endpoint branch fires na prázdný `_loaded_specs` cache (URL
> specs tam nejsou) a vyhodí "no spec loaded" — nesprávný error type.
> Reorder fix byl proveden v Phase 3 red commit (`__init__.py:378`).
>
> **Refactor**: shared logika (response_code lookup + registry build +
> SchemaValidator instantiation) vyčleněna do private helperu
> `_validate_against_spec(spec, key, response_code, data, return_errors, source_label)`.
> Helper volají oba branche (Phase 2 endpoint + Phase 3 openapi_url).
> Deduplikuje ~12 řádků shared logic.

Použij existující `self._resolve_endpoint_key(method, endpoint)` (`__init__.py:189`)
místo ad-hoc split — helper už podporuje obě formy (`method=POST endpoint=/users`
i `endpoint="POST /users"`), normalizuje case, doplňuje leading `/` a hází
`TalosForgeException` když chybí metoda. Plná spec se čte z nového
`self._loaded_specs` (viz §8.4).

```python
if endpoint:
    # Reuse existing helper from __init__.py:189 — handles both call forms,
    # normalizes case, adds leading /, raises if method missing.
    key = self._resolve_endpoint_key(method, endpoint)

    if not self._loaded_specs:
        raise TalosForgeException(
            "No OpenAPI spec loaded; call Load Schema first"
        )

    # Find the spec containing this endpoint (Load Schema can be called
    # multiple times with different files)
    matched_spec = None
    response_schemas_for_key = None
    for path, spec in self._loaded_specs.items():
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
        available = list(response_schemas_for_key.keys())
        raise TalosForgeException(
            f"No schema for status code {response_code}. Available: {available}"
        )

    schema = response_schemas_for_key[response_code]
    registry = self.schema_loader.build_registry(matched_spec)
    validator = SchemaValidator(schema, registry=registry)
    return validator.validate(data, return_errors=return_errors)
```

> **Optimalizace (mimo Phase 2 scope, jako follow-up)**: Volání
> `extract_response_schemas` v každém `validate_data_against_schema` je redundantní
> — extrahuje to celý spec znova. Cache výsledku v `self._loaded_response_schemas`
> stejným patternem jako `_loaded_openapi_schemas`, pokud profiling ukáže, že
> brzdí. Stejně tak Registry — postavit lazy je levné, ale opakované volání
> taky redundantní. Necháme jako optimalizaci později; nejdřív správnost.

---

## 10. Open Decisions / Questions

1. **JSON Schema draft auto-detection** (`schema_path` zdroj)
   - Současný návrh: vždy použít `OAS30Validator`
   - Alternativa: detekovat `$schema` field a zvolit `Draft7Validator` / `Draft202012Validator`
   - **Doporučení**: zatím držet OAS30Validator (Phase 1), auto-detect přidat v Phase 4 pokud bude potřeba

2. **Co s `default` status codem v OpenAPI?**
   - OpenAPI umožňuje `responses: { default: {...} }` jako catch-all
   - **Doporučení**: V Phase 1-3 ignorovat, v Phase 4+ podporovat

3. **Co s range status codes (2XX, 4XX) v OpenAPI 3.x?**
   - Spec to umožňuje: `responses: { '2XX': {...} }`
   - **Doporučení**: V Phase 1-3 ignorovat, později přidat resolution

4. **Jak hluboko jít s `_enforce_strict` rekurzí?**
   - Současný návrh handle: `properties`, `items`, `oneOf`, `anyOf`, `allOf`
   - Co s `patternProperties`, `additionalProperties: <schema>`, `dependentSchemas`?
   - **Doporučení**: Phase 1 stačí basic, ostatní pokud testy odhalí potřebu

5. **Logging level pro validation failures**
   - DEBUG / INFO / WARNING?
   - **Doporučení**: WARNING při raise, DEBUG při return_errors

6. **Robot Framework — jak přesně signalizovat chybu?**
   - Standardní raise → Robot to chytí jako test failure
   - Doporučujeme custom exception, aby uživatelé mohli `Run Keyword And Expect Error`

---

## 11. Concrete First Steps (in order)

1. **Vytvořit feature branch**: `git checkout -b feat/validation-keyword`
2. **Přidat dependency**: edit `pyproject.toml`, run `pip install -e ".[dev]"`
3. **Vytvořit prázdné moduly**: `TalosForge/validation/{__init__.py,exceptions.py,error_formatter.py,validator.py}`
4. **Napsat testy z bodu 7.1, 7.2, 7.3** — všechny budou failovat (red)
5. **Vytvořit test fixtures**: `tests/fixtures/user.json` (a další podle potřeby)
6. **Implementovat skeleton z bodu 8.1, 8.2, 8.3** — testy začnou procházet (green)
7. **Refactor pokud je třeba** (refactor)
8. **Integrovat do `TalosForge/__init__.py`** (bod 8.4)
9. **Spustit Robot testy** — měly by procházet
10. **Commit**: `feat(validation): add Validate Data Against Schema keyword (Phase 1: schema_path source)`
11. **Otevřít PR** — Phase 2 jako navazující PR po review

---

## 12. Out of Scope for This PR

- ❌ Request body validation
- ❌ Query parameter validation
- ❌ Header validation
- ❌ Non-JSON media types
- ❌ OpenAPI 3.1 support
- ❌ Negative data generation (`Generate Invalid Data From Schema`)
- ❌ Auto-detection of JSON Schema draft from `$schema`
- ❌ `default` / range status codes (`2XX`, `4XX`)
  - Tracked: https://github.com/Stokagee/robotframework-talosforge/issues/2
- ❌ Public `Clear Schema Cache` keyword pro explicit URL cache invalidation
  - Tracked: GitHub issue (URL TBD)
- ❌ Fix existing generator bugs (`nullable: true`, `oneOf/anyOf/allOf` not dispatched)
  - **Action item**: založit GitHub issues pro tyto bugy

---

## 13. Success Criteria

Phase 1 PR je hotov, když:
- [x] Všechny pytest testy z bodu 7 procházejí
- [x] Robot smoke test z bodu 7.3 prochází
- [x] Round-trip test (Generate → Validate na stejném schématu) prochází pro `user.json`
- [x] CI v GitHub Actions zelené
- [x] README aktualizováno s novou keyword
- [x] CHANGELOG.md updated
- [x] Pokrytí ≥ 90% pro `TalosForge/validation/`

Phase 2 PR je hotov, když:
- [x] OpenAPI spec s `$ref: '#/components/schemas/...'` validuje korektně
- [x] Round-trip test funguje pro `Load Schema` + `endpoint` workflow
- [x] Různé `response_code` vrací různá schémata
- [x] Testy s vícerozměrnými refy procházejí

Phase 3 PR je hotov, když:
- [x] `openapi_url` parameter funguje pro stažení online OpenAPI spec
- [x] `responses>=0.23` HTTP mocking testy procházejí (9 pytest testů)
- [x] Round-trip test funguje pro `openapi_url` workflow přes mock HTTP server
- [x] Cache hit ověřený mezi `Generate Data From Schema` a `Validate Data Against Schema` při sdílené URL
- [x] `_validate_against_spec` private helper sdílený mezi endpoint a openapi_url branches
- [x] Robot suite zelená (21/21: 8 generator + 5 P1 + 5 P2 + 3 P3)

---

**End of plan.**
