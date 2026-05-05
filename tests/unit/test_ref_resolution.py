"""
Testy pro $ref resolution v SchemaLoader.
"""

import pytest

from TalosForge.schema.loader import SchemaLoader
from TalosForge.core.exceptions import TalosForgeException


class TestResolveRef:
    """Testy pro metodu _resolve_ref."""

    def test_resolve_ref_components_schemas(self):
        """Test rozlišení reference v #/components/schemas/."""
        loader = SchemaLoader()
        spec = {
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "email": {"type": "string"}
                        }
                    }
                }
            }
        }

        result = loader._resolve_ref(spec, "#/components/schemas/User")

        assert result["type"] == "object"
        assert "name" in result["properties"]
        assert "email" in result["properties"]

    def test_resolve_ref_definitions(self):
        """Test rozlišení reference v #/definitions/ (Swagger 2.0)."""
        loader = SchemaLoader()
        spec = {
            "definitions": {
                "Product": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"}
                    }
                }
            }
        }

        result = loader._resolve_ref(spec, "#/definitions/Product")

        assert result["type"] == "object"
        assert "id" in result["properties"]
        assert "name" in result["properties"]

    def test_resolve_ref_nested_path(self):
        """Test rozlišení reference s hlubší cestou."""
        loader = SchemaLoader()
        spec = {
            "components": {
                "schemas": {
                    "nested": {
                        "deep": {
                            "schema": {
                                "type": "string"
                            }
                        }
                    }
                }
            }
        }

        result = loader._resolve_ref(spec, "#/components/schemas/nested/deep/schema")

        assert result["type"] == "string"

    def test_resolve_ref_recursive(self):
        """Test rekurzivního rozlišení reference (schéma obsahuje další $ref)."""
        loader = SchemaLoader()
        spec = {
            "components": {
                "schemas": {
                    "BaseUser": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"}
                        }
                    },
                    "ExtendedUser": {
                        "$ref": "#/components/schemas/BaseUser"
                    }
                }
            }
        }

        result = loader._resolve_ref(spec, "#/components/schemas/ExtendedUser")

        assert result["type"] == "object"
        assert "id" in result["properties"]

    def test_resolve_ref_external_raises_error(self):
        """Test že externí reference vyhodí výjímku."""
        loader = SchemaLoader()
        spec = {"components": {}}

        with pytest.raises(TalosForgeException) as excinfo:
            loader._resolve_ref(spec, "http://example.com/schema.json")

        assert "Externí reference nejsou podporovány" in str(excinfo.value)

    def test_resolve_ref_not_found_raises_error(self):
        """Test že neexistující reference vyhodí výjímku."""
        loader = SchemaLoader()
        spec = {"components": {"schemas": {}}}

        with pytest.raises(TalosForgeException) as excinfo:
            loader._resolve_ref(spec, "#/components/schemas/NonExistent")

        assert "nebyla nalezena" in str(excinfo.value)

    def test_resolve_ref_invalid_target_raises_error(self):
        """Test že reference ukazující na ne-objekt vyhodí výjímku."""
        loader = SchemaLoader()
        spec = {
            "components": {
                "schemas": {
                    "BadRef": "just a string"
                }
            }
        }

        with pytest.raises(TalosForgeException) as excinfo:
            loader._resolve_ref(spec, "#/components/schemas/BadRef")

        assert "neukazuje na objekt" in str(excinfo.value)


class TestExtractEndpointSchemasWithRef:
    """Testy pro extract_endpoint_schemas s $ref."""

    def test_extract_with_ref(self):
        """Test extrakce endpointu s $ref."""
        loader = SchemaLoader()
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/User"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "email": {"type": "string"}
                        },
                        "required": ["name", "email"]
                    }
                }
            }
        }

        endpoints = loader.extract_endpoint_schemas(spec)

        assert "POST /users" in endpoints
        schema = endpoints["POST /users"]
        assert schema["type"] == "object"
        assert "name" in schema["properties"]
        assert "email" in schema["properties"]

    def test_extract_with_multiple_refs(self):
        """Test extrakce více endpointů s $ref."""
        loader = SchemaLoader()
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        }
                    }
                },
                "/products": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Product"}
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}}
                    },
                    "Product": {
                        "type": "object",
                        "properties": {"id": {"type": "integer"}}
                    }
                }
            }
        }

        endpoints = loader.extract_endpoint_schemas(spec)

        assert "POST /users" in endpoints
        assert "POST /products" in endpoints
        assert endpoints["POST /users"]["type"] == "object"
        assert endpoints["POST /products"]["type"] == "object"

    def test_extract_mixed_ref_and_inline(self):
        """Test extrakce s mixem $ref a inline schématu."""
        loader = SchemaLoader()
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        }
                    }
                },
                "/simple": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"value": {"type": "string"}}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}}
                    }
                }
            }
        }

        endpoints = loader.extract_endpoint_schemas(spec)

        assert "POST /users" in endpoints
        assert "POST /simple" in endpoints
        # Oba by měly mít type object
        assert endpoints["POST /users"]["type"] == "object"
        assert endpoints["POST /simple"]["type"] == "object"

    def test_extract_with_invalid_ref_raises_error(self):
        """Test že neplatná $ref v endpointu vyhodí výjímku."""
        loader = SchemaLoader()
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Missing"}
                                }
                            }
                        }
                    }
                }
            },
            "components": {"schemas": {}}
        }

        with pytest.raises(TalosForgeException) as excinfo:
            loader.extract_endpoint_schemas(spec)

        assert "nebyla nalezena" in str(excinfo.value)
