# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TalosForge is a Python library for Robot Framework that generates test data based on JSON Schema and OpenAPI specifications. It uses a hybrid approach: fast offline generation with Faker, falling back to AI models (OpenAI, Zhipu) for complex cases like regex patterns, schema descriptions, or oneOf/anyOf/allOf constructs.

- **Python Version:** 3.11+
- **Build System:** setuptools with pyproject.toml
- **Primary Language:** Czech (documentation), English (code comments)
- **License:** Apache-2.0

## Development Commands

### Installation
```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Or install from requirements
pip install -r requirements.txt
pip install -e .
```

### Testing
```bash
# Run all pytest tests
pytest

# Run unit tests only
pytest tests/unit

# Run integration tests only
pytest tests/integration

# Run with verbose output
pytest -v --tb=short

# Run single test
pytest path/to/test_file.py::test_function_name

# Run Robot Framework tests
robot --outputdir results/robot --loglevel TRACE tests/robot
```

### Linting and Formatting
```bash
# Flake8 linting
flake8 talosforge/ --max-line-length=100

# Format code with black
black talosforge/

# Check black formatting (dry run)
black --check talosforge/
```

### Building and Publishing
```bash
# Build distribution package
python -m build

# Publish to PyPI
twine upload dist/*
```

### Documentation
```bash
# Build HTML documentation
cd docs && make html

# Serve documentation with live reload
cd docs && make livehtml
```

## Architecture

The codebase follows a clean, modular architecture with clear separation of concerns:

```
TalosForge (Main Class in __init__.py)
    ├── SchemaLoader → Loads/parses JSON & OpenAPI schemas
    ├── DataGenerator → Faker-based generation (fast, offline)
    └── AIGenerator → AI-based generation (complex cases)
        └── SimpleCache → Caches URL specifications
```

### Key Components

**Main Entry Point:** `talosforge/__init__.py` (270 lines)
- Contains the `TalosForge` class implementing Robot Framework library interface
- Only 2 main keywords: `Load Schema` and `Generate Data From Schema`
- Routes schema sources to appropriate handlers (local file, endpoint, URL)

**Core Generator:** `talosforge/core/generator.py` (~1400 lines)
- `DataGenerator` class handles all JSON Schema types
- Supports format constraints (email, date, uri, uuid, password, phone, etc.)
- Recursive generation for nested structures
- Implements the AI/Faker decision logic - delegates to AI for complex cases
- **UniversalFieldParser** (nové v 0.4.0): Inteligentní parser názvů polí
  - Token-based N-gram matching (nejrychlejší)
  - RapidFuzz fuzzy matching (řeší překlepy, varianty názvů)
  - Podporuje snake_case, camelCase, PascalCase, kebab-case
  - Rozpozná 50+ typů polí (email, phone, name, address, tags, atd.)
  - Automatická detekce kolekcí (tags, items, list, array)
  - Automatické odstraňování duplikátů v tag/categories polích

**AI Generator:** `talosforge/core/ai_generator.py` (331 lines)
- `AIGenerator` class integrates OpenAI and Zhipu AI
- Builds prompts for AI models based on schema constraints
- Handles response parsing and fallback to Faker if AI fails

**Schema Loader:** `talosforge/schema/loader.py` (273 lines)
- `SchemaLoader` class parses JSON and YAML
- Extracts endpoint schemas from OpenAPI specifications
- Downloads and caches URL-based schemas

**Configuration:** `talosforge/core/config.py`
- Environment-based configuration
- Locale settings (default: cs_CZ - Czech)
- AI provider selection and API key management

### Design Decisions

1. **Hybrid Generation Strategy:** Uses Faker by default for speed and offline capability, falls back to AI only when schema contains:
   - `description` field
   - Complex `pattern` (regex)
   - `oneOf`/`anyOf`/`allOf` constructs
   - Specific custom formats (e.g., `czech-id`, `ssn`)

2. **UniversalFieldParser (v0.4.0):** Inteligentní rozpoznávání typů polí z názvů
   - Pro prefixová pole (`customer_name`, `user_email`) automaticky generuje správný typ dat
   - Používá token-based matching a RapidFuzz pro fuzzy matching
   - Rozpozná kolekce (`tags`, `items`) a vynucuje unikátnost hodnot
   - Řeší problémy s garbage daty a duplicity

3. **Multiple Data Sources:** Three mutually exclusive sources:
   - `schema_path`: Local JSON schema files
   - `endpoint`: From pre-loaded OpenAPI file (requires `Load Schema` first)
   - `openapi_url`: URL-based OpenAPI spec (requires `endpoint`)

4. **Target Flexibility:** Generates data for:
   - API testing: nested JSON structures (`target=api`)
   - UI testing: flattened form data (`target=ui`)

5. **Caching:** URL-based schemas are cached with TTL to improve performance

## Important File Locations

- `pyproject.toml` - Project metadata, dependencies, black/flake8 config (line-length: 100)
- `requirements.txt` - Runtime and development dependencies
- `README.md` - User-facing documentation (in Czech)
- `.github/workflows/ci.yml` - CI/CD pipeline (tests on Python 3.11 and 3.12)
- `tests/` - Test suite (unit, integration, Robot Framework tests)
- `docs/` - Sphinx documentation (in Czech)

## Dependencies (nové v 0.4.0)

- **rapidfuzz>=3.0.0** - Fuzzy matching library pro UniversalFieldParser
  - 10-100x rychlejší než FuzzyWuzzy
  - WRatio algoritmus - řeší case, word order, překlepy
