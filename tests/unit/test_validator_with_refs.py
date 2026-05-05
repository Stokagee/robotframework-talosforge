"""Unit tests for SchemaValidator with referencing.Registry (Phase 2).

These tests verify that $ref resolution works through the registry
constructed by SchemaLoader.build_registry().
"""

import pytest

from TalosForge.schema.loader import SchemaLoader
from TalosForge.validation.exceptions import DataValidationError
from TalosForge.validation.validator import SchemaValidator


SPEC_USER_ADDRESS = {
    "openapi": "3.0.0",
    "info": {"title": "Test", "version": "1.0"},
    "components": {
        "schemas": {
            "Address": {
                "type": "object",
                "required": ["city"],
                "properties": {
                    "city": {"type": "string"},
                    "country": {"type": "string"},
                },
            },
            "User": {
                "type": "object",
                "required": ["id", "name", "address"],
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "address": {"$ref": "#/components/schemas/Address"},
                },
            },
        }
    },
}


SPEC_REF_CHAIN = {
    "components": {
        "schemas": {
            "A": {"$ref": "#/components/schemas/B"},
            "B": {"$ref": "#/components/schemas/C"},
            "C": {"type": "string", "minLength": 2},
        }
    }
}


SCHEMA_USER = {"$ref": "#/components/schemas/User"}


@pytest.fixture
def loader():
    return SchemaLoader()


class TestSchemaValidatorWithRegistry:
    def test_top_level_ref_resolves_via_registry(self, loader):
        registry = loader.build_registry(SPEC_USER_ADDRESS)
        validator = SchemaValidator(SCHEMA_USER, registry=registry)
        validator.validate(
            {"id": 1, "name": "Jan", "address": {"city": "Praha"}}
        )

    def test_nested_ref_in_property_resolves(self, loader):
        registry = loader.build_registry(SPEC_USER_ADDRESS)
        validator = SchemaValidator(SCHEMA_USER, registry=registry)
        with pytest.raises(DataValidationError) as exc:
            validator.validate(
                {"id": 1, "name": "Jan", "address": {"country": "CZ"}}
            )
        assert "city" in str(exc.value).lower()

    def test_ref_chain_resolves(self, loader):
        registry = loader.build_registry(SPEC_REF_CHAIN)
        schema = {"$ref": "#/components/schemas/A"}
        validator = SchemaValidator(schema, registry=registry)
        validator.validate("hello")

    def test_ref_chain_violation_raises(self, loader):
        registry = loader.build_registry(SPEC_REF_CHAIN)
        schema = {"$ref": "#/components/schemas/A"}
        validator = SchemaValidator(schema, registry=registry)
        with pytest.raises(DataValidationError):
            validator.validate("x")


class TestSchemaValidatorRegistryStrictMode:
    def test_referenced_object_rejects_extra_field(self, loader):
        """Strict mode applies to ref'd components: extra fields in
        Address (referenced from User) must be rejected."""
        registry = loader.build_registry(SPEC_USER_ADDRESS)
        validator = SchemaValidator(SCHEMA_USER, registry=registry)
        with pytest.raises(DataValidationError):
            validator.validate(
                {
                    "id": 1,
                    "name": "Jan",
                    "address": {"city": "Praha", "extra": "x"},
                }
            )
