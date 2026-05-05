"""
Integrační testy pro TalosForge.
"""

import json
import tempfile
from pathlib import Path

from TalosForge import TalosForge
from TalosForge.core.exceptions import TalosForgeException


def test_talosforge_initialization():
    """Test inicializace TalosForge."""
    talosforge = TalosForge()
    assert talosforge.schema_loader is not None
    assert talosforge.data_generator is not None
    assert talosforge._loaded_openapi_schemas == {}


def test_generate_from_schema_path():
    """Test generování z cesty k JSON schématu."""
    talosforge = TalosForge()

    # Vytvořit dočasný soubor se schématem
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"},
        },
        "required": ["name", "email"],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(schema, f)
        temp_path = f.name

    try:
        result = talosforge.generate_data_from_schema(schema_path=temp_path)
        assert isinstance(result, dict)
        assert "name" in result
        assert "email" in result
        assert "@" in result["email"]
    finally:
        Path(temp_path).unlink()


def test_generate_multiple_records():
    """Test generování více záznamů."""
    talosforge = TalosForge()

    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "value": {"type": "string"},
        },
        "required": ["id", "value"],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(schema, f)
        temp_path = f.name

    try:
        result = talosforge.generate_data_from_schema(schema_path=temp_path, amount=3)
        assert isinstance(result, list)
        assert len(result) == 3
        for item in result:
            assert isinstance(item, dict)
            assert "id" in item
            assert "value" in item
    finally:
        Path(temp_path).unlink()


def test_generate_with_target_ui():
    """Test generování s target=ui."""
    talosforge = TalosForge()

    schema = {
        "type": "object",
        "properties": {
            "username": {"type": "string"},
            "password": {"type": "string"},
        },
        "required": ["username", "password"],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(schema, f)
        temp_path = f.name

    try:
        result = talosforge.generate_data_from_schema(schema_path=temp_path, target="ui")
        assert isinstance(result, dict)
        assert "username" in result
        assert "password" in result
    finally:
        Path(temp_path).unlink()


def test_error_no_source_specified():
    """Test chyby když není specifikován žádný zdroj."""
    talosforge = TalosForge()

    try:
        talosforge.generate_data_from_schema()
        assert False, "Měla vyhodit TalosForgeException"
    except TalosForgeException as e:
        assert "alespoň jeden zdroj" in str(e)


def test_error_multiple_sources():
    """Test chyby když je specifikováno více zdrojů."""
    talosforge = TalosForge()

    schema = {"type": "string"}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(schema, f)
        temp_path = f.name

    try:
        talosforge.generate_data_from_schema(
            schema_path=temp_path,
            endpoint="POST /users"
        )
        assert False, "Měla vyhodit TalosForgeException"
    except TalosForgeException as e:
        assert "právě jeden zdroj" in str(e)
    finally:
        Path(temp_path).unlink()


def test_load_openapi_schema():
    """Test načtení OpenAPI schématu."""
    talosforge = TalosForge()

    # Vytvořit jednoduché OpenAPI schéma
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string"},
                                    },
                                    "required": ["name", "email"],
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Created"}}
                }
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(openapi_spec, f)
        temp_path = f.name

    try:
        # Načíst schéma
        talosforge.load_schema(swagger_path=temp_path)

        # Ověřit, že bylo načteno
        assert temp_path in talosforge._loaded_openapi_schemas
        assert "POST /users" in talosforge._loaded_openapi_schemas[temp_path]

        # Generovat data z endpointu
        result = talosforge.generate_data_from_schema(endpoint="POST /users")
        assert isinstance(result, dict)
        assert "name" in result
        assert "email" in result
    finally:
        Path(temp_path).unlink()


def test_force_reload_schema():
    """Test force_reload parametru."""
    talosforge = TalosForge()

    openapi_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/items": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"name": {"type": "string"}},
                                    "required": ["name"],
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Created"}}
                }
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(openapi_spec, f)
        temp_path = f.name

    try:
        # První načtení
        talosforge.load_schema(swagger_path=temp_path)
        first_call_count = len(talosforge._loaded_openapi_schemas[temp_path])

        # Druhé načtení bez force_reload (nemělo by znovu načítat)
        talosforge.load_schema(swagger_path=temp_path, force_reload=False)
        assert len(talosforge._loaded_openapi_schemas[temp_path]) == first_call_count

        # S force_reload (mělo by znovu načíst)
        talosforge.load_schema(swagger_path=temp_path, force_reload=True)
        # Schéma by mělo být stále tam, ale znovu načteno
        assert "POST /items" in talosforge._loaded_openapi_schemas[temp_path]
    finally:
        Path(temp_path).unlink()


def test_openapi_example_ignored_integration():
    """Test, že OpenAPI 'example' je ignorováno v reálném scénáři."""
    talosforge = TalosForge()

    # OpenAPI spec s 'example' polem
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0"},
        "paths": {
            "/users": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "example": "Jan Novák"
                                        },
                                        "email": {
                                            "type": "string",
                                            "format": "email",
                                            "example": "test@example.com"
                                        }
                                    },
                                    "required": ["name", "email"]
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(openapi_spec, f)
        temp_path = f.name

    try:
        talosforge.load_schema(swagger_path=temp_path)

        # Generovat více uživatelů
        users = talosforge.generate_data_from_schema(
            method="POST",
            endpoint="/users",
            amount=10
        )

        # Ověřit různorodost jmen
        names = [u["name"] for u in users]
        assert len(set(names)) > 1, "Jména by měla být různá"

        # Ověřit různorodost emailů
        emails = [u["email"] for u in users]
        assert len(set(emails)) > 1, "Emaily by měly být různé"

        # Původní example hodnoty by se neměly objevit
        assert "Jan Novák" not in names
        assert "test@example.com" not in emails
    finally:
        Path(temp_path).unlink()
