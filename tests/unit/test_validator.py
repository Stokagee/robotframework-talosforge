"""Unit tests for SchemaValidator (Phase 1).

Round-trip-determinism note: any fixture used by Generate-then-Validate tests in
this module MUST avoid `description`, long `pattern` (>20 chars), and
`oneOf/anyOf/allOf`. Those triggers activate AI escalation in
`_should_use_ai()` (TalosForge/core/generator.py:1366) when use_ai=True and
produce non-deterministic data.
"""

import pytest

from TalosForge.validation.exceptions import DataValidationError
from TalosForge.validation.validator import SchemaValidator


class TestSchemaValidatorHappyPath:
    def test_valid_simple_object(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        SchemaValidator(schema).validate({"name": "Jan"})

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
