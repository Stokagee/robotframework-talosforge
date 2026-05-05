"""Error formatting helpers for validation results."""

from typing import Any, Dict, List

from jsonschema.exceptions import ValidationError


def format_path(path_parts) -> str:
    """Convert a path deque/list to a JSONPath-like string.

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
    """Convert a jsonschema.ValidationError to a serializable dict."""
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
    """Build a human-readable multi-error message for raise mode."""
    if not errors:
        return "Validation passed"
    lines = [f"Validation failed with {len(errors)} error(s):"]
    for err in errors:
        lines.append(
            f"  - {err['path']}: {err['message']} (validator: {err['validator']})"
        )
    return "\n".join(lines)
