"""Integration tests for openapi_url validation source (Phase 3).

Uses responses>=0.23 to mock HTTP responses without a real network round-trip.
The fixture YAML is the same one used by Phase 2 (tests/fixtures/test_api_responses.yaml)
so the request/response schemas are identical between local-spec and URL-spec
tests, which keeps round-trip determinism guarantees the same.
"""

from pathlib import Path

import pytest
import responses

from TalosForge import TalosForge
from TalosForge.core.exceptions import TalosForgeException
from TalosForge.validation.exceptions import DataValidationError


FIXTURE_URL = "http://api.test/openapi.yaml"


@pytest.fixture
def yaml_spec_content():
    fixture_path = (
        Path(__file__).parent.parent / "fixtures" / "test_api_responses.yaml"
    )
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def tf():
    """Fresh TalosForge instance per test (isolates SimpleCache)."""
    return TalosForge()


class TestValidateAgainstURL:
    @responses.activate
    def test_validate_passes_for_valid_data(self, tf, yaml_spec_content):
        responses.add(
            responses.GET,
            FIXTURE_URL,
            body=yaml_spec_content,
            content_type="application/yaml",
            status=200,
        )
        data = {"id": 1, "name": "Item Name"}
        tf.validate_data_against_schema(
            data=data,
            openapi_url=FIXTURE_URL,
            method="POST",
            endpoint="/items",
            response_code=201,
        )

    @responses.activate
    def test_validate_raises_for_invalid_data(self, tf, yaml_spec_content):
        responses.add(
            responses.GET,
            FIXTURE_URL,
            body=yaml_spec_content,
            content_type="application/yaml",
            status=200,
        )
        # name "X" is below minLength: 2
        data = {"id": 1, "name": "X"}
        with pytest.raises(DataValidationError):
            tf.validate_data_against_schema(
                data=data,
                openapi_url=FIXTURE_URL,
                method="POST",
                endpoint="/items",
                response_code=201,
            )

    @responses.activate
    def test_validate_without_endpoint_raises(self, tf):
        # openapi_url without endpoint is rejected before any HTTP call
        with pytest.raises(TalosForgeException) as exc:
            tf.validate_data_against_schema(
                data={}, openapi_url=FIXTURE_URL,
            )
        assert "endpoint" in str(exc.value).lower()
        # No HTTP call should have happened
        assert len(responses.calls) == 0

    @responses.activate
    def test_validate_unknown_endpoint_raises(self, tf, yaml_spec_content):
        responses.add(
            responses.GET,
            FIXTURE_URL,
            body=yaml_spec_content,
            content_type="application/yaml",
            status=200,
        )
        with pytest.raises(TalosForgeException) as exc:
            tf.validate_data_against_schema(
                data={},
                openapi_url=FIXTURE_URL,
                method="GET",
                endpoint="/nonexistent",
                response_code=200,
            )
        assert "not found" in str(exc.value).lower()

    @responses.activate
    def test_validate_unknown_response_code_raises(self, tf, yaml_spec_content):
        responses.add(
            responses.GET,
            FIXTURE_URL,
            body=yaml_spec_content,
            content_type="application/yaml",
            status=200,
        )
        with pytest.raises(TalosForgeException) as exc:
            tf.validate_data_against_schema(
                data={},
                openapi_url=FIXTURE_URL,
                method="POST",
                endpoint="/items",
                response_code=999,
            )
        assert "status code" in str(exc.value).lower()


class TestValidateURLCaching:
    @responses.activate
    def test_url_fetched_only_once_per_session(self, tf, yaml_spec_content):
        """Two consecutive validates against same URL hit HTTP exactly once
        (SimpleCache TTL=3600s on the SchemaLoader instance)."""
        responses.add(
            responses.GET,
            FIXTURE_URL,
            body=yaml_spec_content,
            content_type="application/yaml",
            status=200,
        )
        data = {"id": 1, "name": "Item Name"}
        tf.validate_data_against_schema(
            data=data,
            openapi_url=FIXTURE_URL,
            method="POST",
            endpoint="/items",
            response_code=201,
        )
        tf.validate_data_against_schema(
            data=data,
            openapi_url=FIXTURE_URL,
            method="POST",
            endpoint="/items",
            response_code=201,
        )
        assert len(responses.calls) == 1


class TestValidateURLErrorHandling:
    @responses.activate
    def test_404_url_raises_talosforge_exception(self, tf):
        responses.add(responses.GET, FIXTURE_URL, status=404)
        with pytest.raises(TalosForgeException):
            tf.validate_data_against_schema(
                data={},
                openapi_url=FIXTURE_URL,
                method="GET",
                endpoint="/items",
                response_code=200,
            )

    @responses.activate
    def test_invalid_yaml_url_raises(self, tf):
        responses.add(
            responses.GET,
            FIXTURE_URL,
            body="this: is: not: valid: yaml: [unclosed",
            content_type="application/yaml",
            status=200,
        )
        with pytest.raises(TalosForgeException):
            tf.validate_data_against_schema(
                data={},
                openapi_url=FIXTURE_URL,
                method="GET",
                endpoint="/items",
                response_code=200,
            )


class TestValidateURLPlusGenerator:
    @responses.activate
    def test_generate_then_validate_roundtrip_via_url(
        self, tf, yaml_spec_content
    ):
        """Generate from /items request body via URL, validate same data
        against /items 201 response via same URL. Cache hit on second call."""
        responses.add(
            responses.GET,
            FIXTURE_URL,
            body=yaml_spec_content,
            content_type="application/yaml",
            status=200,
        )
        data = tf.generate_data_from_schema(
            method="POST", endpoint="/items", openapi_url=FIXTURE_URL
        )
        tf.validate_data_against_schema(
            data=data,
            openapi_url=FIXTURE_URL,
            method="POST",
            endpoint="/items",
            response_code=201,
        )
        # Generate + validate share cache: only one HTTP fetch
        assert len(responses.calls) == 1
