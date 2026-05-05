"""Unit tests for validation.error_formatter (Phase 1)."""

from jsonschema import Draft7Validator

from TalosForge.validation.error_formatter import (
    error_to_dict,
    errors_to_message,
    format_path,
)


def test_format_path_jsonpath_style():
    assert format_path(["users", 0, "email"]) == "$.users[0].email"
    assert format_path([]) == "$"
    assert format_path(["name"]) == "$.name"


def test_format_error_to_dict():
    schema = {
        "type": "object",
        "properties": {"email": {"type": "string", "format": "email"}},
    }
    instance = {"email": 123}
    errors = list(Draft7Validator(schema).iter_errors(instance))
    assert errors, "test setup: expected at least one ValidationError"

    err_dict = error_to_dict(errors[0])

    assert "path" in err_dict
    assert "path_parts" in err_dict
    assert "message" in err_dict
    assert "validator" in err_dict
    assert "validator_value" in err_dict
    assert "instance" in err_dict
    assert err_dict["instance"] == 123


def test_format_errors_to_message():
    err_list = [
        {"path": "$.email", "message": "'foo' is not a 'email'", "validator": "format"},
        {"path": "$.age", "message": "minimum is 0", "validator": "minimum"},
    ]
    msg = errors_to_message(err_list)

    assert "2" in msg
    assert "$.email" in msg
    assert "$.age" in msg
    assert "format" in msg
