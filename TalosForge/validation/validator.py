"""SchemaValidator wraps OAS30Validator with strict mode hardcoded ON.

Implements IMPLEMENTATION_PLAN.md section 8.3.
"""

from copy import deepcopy
from typing import Any, Dict, List, Optional

from openapi_schema_validator import OAS30Validator, oas30_format_checker
from referencing import Registry

from .error_formatter import error_to_dict, errors_to_message
from .exceptions import DataValidationError


# URI used by SchemaLoader.build_registry to register the OpenAPI spec, and
# by SchemaValidator to rewrite fragment-only $refs into absolute references.
# A registry resource registered under URI "" does not satisfy referencing's
# fragment resolution for an outer schema with no $id - the validator treats
# the schema itself as the current resource and looks up "/components/..."
# inside it. A non-empty URI fixes this.
SPEC_URI = "urn:talosforge:spec"


class SchemaValidator:
    """Validates data against a JSON Schema or OpenAPI 3.0 schema.

    Strict mode is ALWAYS enabled - additionalProperties: false is
    enforced on all object schemas, even if the source schema does not
    specify it. This is intentional and not configurable.
    """

    def __init__(
        self,
        schema: Dict[str, Any],
        registry: Optional[Registry] = None,
    ):
        self.schema = self._enforce_strict(deepcopy(schema))
        self.registry = registry
        if registry is not None:
            self._rewrite_fragment_refs(self.schema, SPEC_URI)
        validator_kwargs = {"format_checker": oas30_format_checker}
        if registry is not None:
            validator_kwargs["registry"] = registry
        self._validator = OAS30Validator(self.schema, **validator_kwargs)

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
                if key == "$ref" and isinstance(value, str) and value.startswith("#"):
                    node[key] = base_uri + value
                else:
                    SchemaValidator._rewrite_fragment_refs(value, base_uri)
        elif isinstance(node, list):
            for item in node:
                SchemaValidator._rewrite_fragment_refs(item, base_uri)

    @staticmethod
    def _enforce_strict(schema: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively default `additionalProperties` to False on object schemas."""
        if not isinstance(schema, dict):
            return schema
        if schema.get("type") == "object" or "properties" in schema:
            schema.setdefault("additionalProperties", False)
            for prop_schema in schema.get("properties", {}).values():
                SchemaValidator._enforce_strict(prop_schema)
        if schema.get("type") == "array" and "items" in schema:
            SchemaValidator._enforce_strict(schema["items"])
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
        """Validate `data` against the schema.

        With return_errors=False (default), raises DataValidationError on
        any failure. With return_errors=True, returns the list of error
        dicts (empty list = valid).
        """
        errors = [error_to_dict(e) for e in self._validator.iter_errors(data)]
        if return_errors:
            return errors
        if errors:
            raise DataValidationError(errors_to_message(errors), errors=errors)
        return None
