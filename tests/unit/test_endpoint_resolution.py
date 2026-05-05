"""
Testy pro _resolve_endpoint_key metodu.
"""

import pytest

from TalosForge import TalosForge
from TalosForge.core.exceptions import TalosForgeException


class TestResolveEndpointKey:
    """Testy pro metodu _resolve_endpoint_key."""

    def test_method_with_leading_slash(self):
        """Test method s endpointem začínajícím lomítkem."""
        tf = TalosForge()
        result = tf._resolve_endpoint_key("POST", "/users")
        assert result == "POST /users"

    def test_method_without_leading_slash(self):
        """Test method s endpointem bez lomítka na začátku."""
        tf = TalosForge()
        result = tf._resolve_endpoint_key("POST", "users")
        assert result == "POST /users"

    def test_method_lowercase(self):
        """Test method s malými písmeny."""
        tf = TalosForge()
        result = tf._resolve_endpoint_key("get", "/api/v1/items")
        assert result == "GET /api/v1/items"

    def test_method_with_whitespace(self):
        """Test method s mezerami."""
        tf = TalosForge()
        result = tf._resolve_endpoint_key("  PUT  ", "  /products  ")
        assert result == "PUT /products"

    def test_method_with_endpoint_containing_method(self):
        """Test method kdy endpoint již obsahuje metodu."""
        tf = TalosForge()
        result = tf._resolve_endpoint_key("POST", "POST /users")
        assert result == "POST /users"

    def test_method_with_endpoint_containing_different_method(self):
        """Test method kdy endpoint obsahuje jinou metodu."""
        tf = TalosForge()
        result = tf._resolve_endpoint_key("GET", "POST /users")
        assert result == "GET /users"

    def test_backward_compatibility_with_method(self):
        """Test zpětné kompatibility - endpoint obsahuje metodu."""
        tf = TalosForge()
        result = tf._resolve_endpoint_key(None, "POST /users")
        assert result == "POST /users"

    def test_backward_compatibility_lowercase_method(self):
        """Test zpětné kompatibility - malá písmena."""
        tf = TalosForge()
        result = tf._resolve_endpoint_key(None, "get /users")
        assert result == "get /users"

    def test_backward_compatibility_with_whitespace(self):
        """Test zpětné kompatibility - mezery."""
        tf = TalosForge()
        result = tf._resolve_endpoint_key(None, "  POST  /users  ")
        assert result == "POST  /users"

    def test_error_no_method_no_endpoint_method(self):
        """Test chyby při chybějící metodě i v endpointu."""
        tf = TalosForge()
        with pytest.raises(TalosForgeException) as excinfo:
            tf._resolve_endpoint_key(None, "/users")
        assert "neobsahuje HTTP metodu" in str(excinfo.value)
        assert "method=" in str(excinfo.value)

    def test_error_only_path_no_method(self):
        """Test chyby při jen cestě bez metody."""
        tf = TalosForge()
        with pytest.raises(TalosForgeException) as excinfo:
            tf._resolve_endpoint_key(None, "users")
        assert "neobsahuje HTTP metodu" in str(excinfo.value)

    def test_complex_path(self):
        """Test složité cesty."""
        tf = TalosForge()
        result = tf._resolve_endpoint_key("DELETE", "/api/v1/couriers/{id}")
        assert result == "DELETE /api/v1/couriers/{id}"

    def test_all_http_methods(self):
        """Test všech HTTP metod."""
        tf = TalosForge()
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        for method in methods:
            result = tf._resolve_endpoint_key(method, "/test")
            assert result == f"{method} /test"
