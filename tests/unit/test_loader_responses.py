"""Unit tests for SchemaLoader.extract_response_schemas (Phase 2)."""

import pytest

from TalosForge.schema.loader import SchemaLoader


SPEC_SINGLE_201 = {
    "openapi": "3.0.0",
    "info": {"title": "Test", "version": "1.0"},
    "paths": {
        "/users": {
            "post": {
                "responses": {
                    "201": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"id": {"type": "integer"}},
                                }
                            }
                        }
                    }
                }
            }
        }
    },
}


SPEC_MULTIPLE_CODES = {
    "paths": {
        "/users": {
            "get": {
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {"schema": {"type": "array"}}
                        }
                    },
                    "400": {
                        "content": {
                            "application/json": {"schema": {"type": "object"}}
                        }
                    },
                    "404": {
                        "content": {
                            "application/json": {"schema": {"type": "object"}}
                        }
                    },
                }
            }
        }
    }
}


SPEC_NO_RESPONSES = {
    "paths": {
        "/users": {
            "post": {
                "summary": "Create user, no responses defined"
            }
        }
    }
}


SPEC_NO_JSON_CONTENT = {
    "paths": {
        "/users": {
            "post": {
                "responses": {
                    "201": {
                        "content": {
                            "application/xml": {"schema": {"type": "object"}}
                        }
                    }
                }
            }
        }
    }
}


SPEC_ALL_METHODS = {
    "paths": {
        "/r": {
            method: {
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {"schema": {"type": "object"}}
                        }
                    }
                }
            }
            for method in ("get", "post", "put", "patch", "delete", "head", "options")
        }
    }
}


SPEC_UNKNOWN_METHODS = {
    "paths": {
        "/r": {
            "trace": {
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {"schema": {"type": "object"}}
                        }
                    }
                }
            },
            "x-custom": {
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {"schema": {"type": "object"}}
                        }
                    }
                }
            },
        }
    }
}


SPEC_DEFAULT_ONLY = {
    "paths": {
        "/users": {
            "post": {
                "responses": {
                    "default": {
                        "content": {
                            "application/json": {"schema": {"type": "object"}}
                        }
                    }
                }
            }
        }
    }
}


SPEC_RANGE_AND_NUMERIC = {
    "paths": {
        "/users": {
            "post": {
                "responses": {
                    "2XX": {
                        "content": {
                            "application/json": {"schema": {"type": "object"}}
                        }
                    },
                    "201": {
                        "content": {
                            "application/json": {"schema": {"type": "object"}}
                        }
                    },
                }
            }
        }
    }
}


SPEC_TOP_LEVEL_REF = {
    "paths": {
        "/users": {
            "post": {
                "responses": {
                    "201": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
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
                "properties": {"id": {"type": "integer"}},
            }
        }
    },
}


SPEC_NESTED_REF = {
    "paths": {
        "/users": {
            "post": {
                "responses": {
                    "201": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "address": {
                                            "$ref": "#/components/schemas/Address"
                                        }
                                    },
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "Address": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
            }
        }
    },
}


@pytest.fixture
def loader():
    return SchemaLoader()


class TestExtractResponseSchemasBasic:
    def test_single_endpoint_with_201(self, loader):
        result = loader.extract_response_schemas(SPEC_SINGLE_201)
        assert "POST /users" in result
        assert 201 in result["POST /users"]
        assert result["POST /users"][201]["type"] == "object"

    def test_endpoint_with_multiple_codes(self, loader):
        result = loader.extract_response_schemas(SPEC_MULTIPLE_CODES)
        assert "GET /users" in result
        assert set(result["GET /users"].keys()) == {200, 400, 404}

    def test_endpoint_without_responses_excluded(self, loader):
        result = loader.extract_response_schemas(SPEC_NO_RESPONSES)
        assert "POST /users" not in result

    def test_endpoint_without_application_json_excluded(self, loader):
        result = loader.extract_response_schemas(SPEC_NO_JSON_CONTENT)
        assert "POST /users" not in result


class TestExtractResponseSchemasMethods:
    def test_all_http_methods_extracted(self, loader):
        result = loader.extract_response_schemas(SPEC_ALL_METHODS)
        for method in ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"):
            assert f"{method} /r" in result

    def test_unknown_method_ignored(self, loader):
        result = loader.extract_response_schemas(SPEC_UNKNOWN_METHODS)
        assert "TRACE /r" not in result
        assert "X-CUSTOM /r" not in result


class TestExtractResponseSchemasStatusCodes:
    def test_numeric_string_codes_parsed_as_int(self, loader):
        result = loader.extract_response_schemas(SPEC_SINGLE_201)
        codes = list(result["POST /users"].keys())
        assert codes == [201]
        assert isinstance(codes[0], int)

    def test_default_code_included(self, loader):
        result = loader.extract_response_schemas(SPEC_DEFAULT_ONLY)
        assert "POST /users" in result
        assert "default" in result["POST /users"]
        assert result["POST /users"]["default"]["type"] == "object"

    def test_xx_range_codes_included(self, loader):
        result = loader.extract_response_schemas(SPEC_RANGE_AND_NUMERIC)
        assert "POST /users" in result
        codes = result["POST /users"]
        assert 201 in codes
        assert "2XX" in codes
        # numeric codes stay as int, range codes are upper-case strings
        assert isinstance([k for k in codes if k == 201][0], int)

    def test_lowercase_xx_normalized_to_uppercase(self, loader):
        spec = {
            "paths": {
                "/users": {
                    "get": {
                        "responses": {
                            "2xx": {
                                "content": {
                                    "application/json": {"schema": {"type": "object"}}
                                }
                            }
                        }
                    }
                }
            }
        }
        result = loader.extract_response_schemas(spec)
        assert "GET /users" in result
        assert "2XX" in result["GET /users"]

    def test_all_range_buckets_included(self, loader):
        spec = {
            "paths": {
                "/r": {
                    "get": {
                        "responses": {
                            code: {
                                "content": {
                                    "application/json": {"schema": {"type": "object"}}
                                }
                            }
                            for code in ("1XX", "2XX", "3XX", "4XX", "5XX")
                        }
                    }
                }
            }
        }
        result = loader.extract_response_schemas(spec)
        assert set(result["GET /r"].keys()) == {"1XX", "2XX", "3XX", "4XX", "5XX"}

    def test_non_numeric_non_range_codes_ignored(self, loader):
        spec = {
            "paths": {
                "/users": {
                    "post": {
                        "responses": {
                            "not-a-code": {
                                "content": {
                                    "application/json": {"schema": {"type": "object"}}
                                }
                            }
                        }
                    }
                }
            }
        }
        result = loader.extract_response_schemas(spec)
        assert "POST /users" not in result


class TestExtractResponseSchemasRefHandling:
    def test_top_level_ref_returned_as_ref_unchanged(self, loader):
        result = loader.extract_response_schemas(SPEC_TOP_LEVEL_REF)
        schema = result["POST /users"][201]
        assert "$ref" in schema
        assert schema["$ref"] == "#/components/schemas/User"

    def test_nested_ref_in_properties_unchanged(self, loader):
        result = loader.extract_response_schemas(SPEC_NESTED_REF)
        schema = result["POST /users"][201]
        assert schema["type"] == "object"
        assert (
            schema["properties"]["address"]["$ref"]
            == "#/components/schemas/Address"
        )
