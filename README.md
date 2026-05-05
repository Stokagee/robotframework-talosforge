# TalosForge

**Schema-driven test data generator for Robot Framework**

TalosForge is a Python library for Robot Framework that generates tailored test data based on JSON Schema and OpenAPI specifications. It combines the speed of the Faker library with the intelligence of AI models (OpenAI, Zhipu) for complex cases.

## Features

- **Tailored generation**: Define data structure using JSON Schema or OpenAPI
- **Hybrid approach**: Faker for speed + AI for complex cases
- **Universal output**: Python dictionaries compatible with RequestsLibrary, Browser, DatabaseLibrary
- **Simple API**: Only two main keywords
- **Caching**: Automatic caching of URL specifications
- **Multiple languages**: Default Czech locale, easy to change

## Requirements

- Python 3.11+
- Robot Framework 7.0+

## Installation

### Basic installation

```bash
pip install TalosForge
```

### With AI support (optional)

```bash
# For OpenAI
pip install openai>=1.0
export OPENAI_API_KEY=your_key_here

# For Zhipu AI
pip install zhipuai
export ZHIPU_API_KEY=your_key_here
```

## Quick start

### 1. Create a JSON schema

**user_schema.json:**
```json
{
  "type": "object",
  "properties": {
    "username": {
      "type": "string",
      "minLength": 5
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
  "required": ["username", "email"]
}
```

### 2. Use it in Robot Framework

```robotframework
*** Settings ***
Library     talosforge.TalosForge

*** Test Cases ***
Generate User Data
    ${user}=    Generate Data From Schema    schema_path=./user_schema.json
    Log    ${user}
    # Output: {'username': 'Jan Novák', 'email': 'jan.novak@example.cz', 'age': 25}
```

## Keywords

### Load Schema

Loads an OpenAPI file into memory for faster access during repeated generation.

**Syntax:**
```robotframework
Load Schema    swagger_path=<path>    [force_reload=False]
```

**Parameters:**
- `swagger_path` (required): Path to a local OpenAPI (Swagger) file (JSON or YAML)
- `force_reload` (optional): Forces a reload even if the file is already in memory. Default: False

**Example:**
```robotframework
*** Test Cases ***
Load Large API
    Load Schema    swagger_path=./petstore.yaml
    ${pet}=    Generate Data From Schema    endpoint=POST /pet
    ${order}=    Generate Data From Schema    endpoint=POST /store/order
```

### Generate Data From Schema

Generates test data based on the provided schema.

**Syntax:**
```robotframework
${data}=    Generate Data From Schema    [source]    [target=api|ui]    [amount=1]    [use_ai=False]
```

**Data sources (exactly one must be specified):**
- `schema_path`: Path to a local JSON schema
- `endpoint`: Endpoint in the format `METHOD /path` (e.g. `POST /users`). Requires a prior `Load Schema`
- `openapi_url`: URL to an online OpenAPI specification. Requires `endpoint`

**Parameters:**
- `method` (optional): HTTP method (e.g. `POST`, `GET`). Also requires `endpoint`. This is the preferred way to specify the HTTP method, since it avoids issues with whitespace parsing in Robot Framework.
- `target` (optional): Output format. Options: `"api"` (default) or `"ui"`
- `amount` (optional): Number of records to generate. Default: 1
- `use_ai` (optional): Enables AI generation for complex cases. Default: False

**Return value:**
- If `amount=1`: Returns a single dictionary (dict)
- If `amount>1`: Returns a list of dictionaries (list)

**Examples:**

```robotframework
# From a local JSON schema
${user}=    Generate Data From Schema    schema_path=./user.json

# From a loaded OpenAPI file - NEW SYNTAX (recommended)
Load Schema    swagger_path=./api.yaml
${data}=    Generate Data From Schema    method=POST    endpoint=/users    amount=5

# From a loaded OpenAPI file - OLD SYNTAX (still works)
Load Schema    swagger_path=./api.yaml
${data}=    Generate Data From Schema    endpoint=POST /users    amount=5

# From an online OpenAPI specification
${item}=    Generate Data From Schema    openapi_url=https://api.example.com/swagger.json    method=GET    endpoint=/items

# For UI testing
${form}=    Generate Data From Schema    schema_path=./login.json    target=ui

# With AI generation
${content}=    Generate Data From Schema    schema_path=./article.json    use_ai=True
```

**HTTP Methods**

There are two ways to specify the HTTP method:

1. **Separate `method=` parameter (recommended)** - avoids issues with whitespace parsing in Robot Framework:
   ```robotframework
   ${data}=    Generate Data From Schema    method=POST    endpoint=/api/v1/couriers/
   ```

2. **Written directly in the endpoint (backward compatibility)** - works, but Robot Framework may parse the space as a separator:
   ```robotframework
   ${data}=    Generate Data From Schema    endpoint=POST /api/v1/couriers/
   ```

## Supported JSON Schema types

| Type | Supported properties |
|------|----------------------|
| `string` | format, minLength, maxLength, pattern, description, examples |
| `integer` | minimum, maximum, exclusiveMinimum, exclusiveMaximum, examples |
| `number` | minimum, maximum, exclusiveMinimum, exclusiveMaximum, examples |
| `boolean` | examples |
| `array` | items, minItems, maxItems |
| `object` | properties, required, default |
| `enum` | Enumeration of values |
| `oneOf`, `anyOf`, `allOf` | Basic support (with AI) |

## Examples support

TalosForge supports the `examples` field in JSON Schema:

```json
{
  "name": {"type": "string", "examples": ["Jan Novák", "Petr Svoboda"]},
  "age": {"type": "integer", "examples": [25, 30, 42]},
  "tags": {
    "type": "array",
    "items": {"type": "string", "examples": ["vip", "urgent"]}
  }
}
```

## Schema processing priority

TalosForge processes JSON Schema in the following order:

1. **enum** - Picks a random value from the enum list (validation constraint)
2. **examples** - Picks a random value from the examples list
3. **example** - *Ignored* (a single value would block Faker)
4. **AI** - AI generation (if `use_ai=True`)
5. **Faker** - Generation by type/format

**Important:** The `example` field (singular) in OpenAPI specifications is ignored
because it contains only a single value. For more varied test data, use Faker
or specify `examples` (plural) with multiple values.

## Contextual generation (50+ field variants)

For common fields, TalosForge automatically uses the right Faker methods. Offline mode works without AI for:

**Personal data:** name, first_name, last_name, username, email, phone
**Address:** address, street, city, zip, state, country, lat, lng
**Organization:** company, department, position
**Time:** date, time, datetime, created_at, updated_at
**Content:** title, description, content, message, subject
**Identifiers:** id, uuid, code, sku
**WWW:** url, domain, hostname
**Finance:** price, cost, currency, account, iban
**Technical:** ip, port, user_agent, mac, token
**Status:** status, priority, level
**Special:** tags, categories, type

**Example:**
```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "email": {"type": "string"},
    "phone": {"type": "string"},
    "address": {"type": "string"},
    "company": {"type": "string"},
    "created_at": {"type": "string"}
  }
}
```

Generates realistic data such as:
```json
{
  "name": "Jan Novák",
  "email": "jan.novak@example.cz",
  "phone": "+420 123 456 789",
  "address": "Nová 123, Praha",
  "company": "Firma s.r.o.",
  "created_at": "2025-01-31T12:34:56"
}
```

## Nullable support (OpenAPI)

For fields with `nullable: true`, there is a 20% chance of returning `None`:

```json
{
  "lat": {"type": "number", "nullable": true}
}
```

### Supported formats (string)

- `email` - Email address
- `date` - Date (YYYY-MM-DD)
- `date-time` - Date and time (ISO 8601)
- `time` - Time (HH:MM:SS)
- `uri` - URL address
- `uuid` - UUID version 4
- `hostname` - Hostname
- `ipv4`, `ipv6` - IP addresses
- `password` - Password
- `phone` - Phone number

## AI Generation

AI is used for complex cases such as:
- Presence of `description` in the schema
- Complex regular expressions (`pattern`)
- `oneOf`/`anyOf`/`allOf` constructs
- Specific formats (e.g. `czech-id`, `ssn`)

**Example with description:**
```json
{
  "type": "string",
  "description": "Generate a realistic Czech full name"
}
```

With `use_ai=True`, TalosForge uses an AI model to generate a Czech name.

## Configuration

### Locale

```python
import os
os.environ["TAOSFORGE_LOCALE"] = "en_US"  # English locale
```

### AI Provider

```python
import os

# Provider selection
os.environ["TAOSFORGE_AI_PROVIDER"] = "openai"  # or "zhipu"

# Specific models
os.environ["TAOSFORGE_OPENAI_MODEL"] = "gpt-4"
os.environ["TAOSFORGE_ZHIPU_MODEL"] = "glm-4"
```

## Development

### Development installation

```bash
git clone https://github.com/yourusername/TalosForge.git
cd TalosForge
pip install -e ".[dev]"
```

### Running tests

```bash
# All pytest tests
pytest

# Unit tests only
pytest tests/unit

# Integration tests
pytest tests/integration

# Robot Framework tests
robot --outputdir results/robot tests/robot
```

### Code formatting

```bash
# Flake8 linting
flake8 talosforge/ --max-line-length=100

# Black formatting
black talosforge/
```

## Project structure

```
talosforge/
├── __init__.py         # Main TalosForge class
├── core/
│   ├── config.py       # Configuration
│   ├── generator.py    # DataGenerator (Faker + AI)
│   ├── ai_generator.py # AIGenerator
│   └── exceptions.py   # Exceptions
├── schema/
│   └── loader.py       # SchemaLoader
└── utils/
    └── cache.py        # SimpleCache
```

## License

Apache License 2.0

## Status

**Version 0.2.0** - Production ready

- ✅ Schema-driven generation (JSON Schema, OpenAPI)
- ✅ Hybrid generation (Faker + AI)
- ✅ URL support with caching
- ✅ 44 tests (100% coverage)
- ✅ Complete documentation
- ✅ Support for `examples` and `example` fields in JSON Schema
- ✅ Contextual generation for 50+ field variants
- ✅ Nullable support (OpenAPI specification)
