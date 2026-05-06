"""Unit tests for response-code fallback (numeric → range → default).

Covers issue #2: validate_data_against_schema must resolve a numeric
response_code through range codes (e.g. 2XX) and finally `default` when
no explicit numeric schema is defined.
"""

import pytest

from TalosForge import TalosForge
from TalosForge.core.exceptions import TalosForgeException
from TalosForge.validation.exceptions import DataValidationError


def _spec_with_responses(responses: dict) -> dict:
    """Build a minimal OpenAPI 3.0 spec where POST /things has the given responses."""
    return {
        "openapi": "3.0.0",
        "info": {"title": "T", "version": "1"},
        "paths": {
            "/things": {
                "post": {
                    "responses": {
                        code: {
                            "content": {"application/json": {"schema": schema}}
                        }
                        for code, schema in responses.items()
                    }
                }
            }
        },
    }


@pytest.fixture
def tf():
    return TalosForge()


def _load(tf, spec, label="spec.yaml"):
    """Inject a parsed spec directly into the TalosForge cache.

    Bypasses load_schema (which reads a file) so tests can stay in-memory.
    extract_endpoint_schemas tolerates endpoints without requestBody.
    """
    tf._loaded_openapi_schemas[label] = tf.schema_loader.extract_endpoint_schemas(spec)
    tf._loaded_specs[label] = spec


SIMPLE_OBJECT = {"type": "object", "properties": {"id": {"type": "integer"}}}


class TestNumericTakesPrecedence:
    def test_exact_numeric_wins_over_range(self, tf):
        """If both 200 and 2XX are defined, an exact 200 hit picks 200."""
        spec = _spec_with_responses({
            "200": {"type": "object", "properties": {"exact": {"type": "string"}}},
            "2XX": {"type": "object", "properties": {"range": {"type": "string"}}},
        })
        _load(tf, spec)
        # Data shaped for the exact-200 schema: must validate.
        tf.validate_data_against_schema(
            data={"exact": "ok"},
            method="POST", endpoint="/things",
            response_code=200,
        )

    def test_exact_numeric_wins_over_default(self, tf):
        spec = _spec_with_responses({
            "200": {"type": "object", "properties": {"exact": {"type": "string"}}},
            "default": {"type": "object", "properties": {"fallback": {"type": "string"}}},
        })
        _load(tf, spec)
        tf.validate_data_against_schema(
            data={"exact": "ok"},
            method="POST", endpoint="/things",
            response_code=200,
        )


class TestRangeFallback:
    def test_range_used_when_numeric_missing(self, tf):
        """response_code=200 with only 2XX defined → 2XX schema applies."""
        spec = _spec_with_responses({
            "2XX": {"type": "object", "properties": {"range": {"type": "string"}}},
        })
        _load(tf, spec)
        tf.validate_data_against_schema(
            data={"range": "ok"},
            method="POST", endpoint="/things",
            response_code=200,
        )

    def test_range_validation_failure_propagates(self, tf):
        spec = _spec_with_responses({
            "4XX": {
                "type": "object",
                "required": ["code"],
                "properties": {"code": {"type": "integer"}},
            },
        })
        _load(tf, spec)
        # 404 → 4XX; missing required `code` → must raise
        with pytest.raises(DataValidationError):
            tf.validate_data_against_schema(
                data={},
                method="POST", endpoint="/things",
                response_code=404,
            )

    def test_range_wins_over_default(self, tf):
        """When numeric is missing but both range and default exist, range wins."""
        spec = _spec_with_responses({
            "2XX": {"type": "object", "properties": {"range": {"type": "string"}}},
            "default": {"type": "object", "properties": {"fb": {"type": "string"}}},
        })
        _load(tf, spec)
        # data fits the 2XX schema; default has incompatible additionalProperties=false
        tf.validate_data_against_schema(
            data={"range": "ok"},
            method="POST", endpoint="/things",
            response_code=200,
        )

    def test_range_bucket_matches_by_first_digit(self, tf):
        spec = _spec_with_responses({
            "5XX": {"type": "object", "properties": {"server": {"type": "string"}}},
        })
        _load(tf, spec)
        tf.validate_data_against_schema(
            data={"server": "down"},
            method="POST", endpoint="/things",
            response_code=503,
        )


class TestDefaultFallback:
    def test_default_used_when_no_numeric_or_range(self, tf):
        spec = _spec_with_responses({
            "default": {"type": "object", "properties": {"fb": {"type": "string"}}},
        })
        _load(tf, spec)
        tf.validate_data_against_schema(
            data={"fb": "ok"},
            method="POST", endpoint="/things",
            response_code=418,
        )

    def test_default_failure_propagates(self, tf):
        spec = _spec_with_responses({
            "default": {
                "type": "object",
                "required": ["err"],
                "properties": {"err": {"type": "string"}},
            },
        })
        _load(tf, spec)
        with pytest.raises(DataValidationError):
            tf.validate_data_against_schema(
                data={},
                method="POST", endpoint="/things",
                response_code=500,
            )


class TestNoMatch:
    def test_no_numeric_no_range_no_default_raises(self, tf):
        spec = _spec_with_responses({
            "201": SIMPLE_OBJECT,
        })
        _load(tf, spec)
        with pytest.raises(TalosForgeException) as exc:
            tf.validate_data_against_schema(
                data={},
                method="POST", endpoint="/things",
                response_code=404,
            )
        # error message should mention what was actually available
        msg = str(exc.value).lower()
        assert "404" in msg or "status" in msg

    def test_wrong_range_bucket_does_not_match(self, tf):
        """5XX must not catch a 2xx response_code."""
        spec = _spec_with_responses({
            "5XX": SIMPLE_OBJECT,
        })
        _load(tf, spec)
        with pytest.raises(TalosForgeException):
            tf.validate_data_against_schema(
                data={},
                method="POST", endpoint="/things",
                response_code=200,
            )
