"""
Unit tests for app/middleware/security.py

TDD approach: Test security headers and HTTPS redirect middleware
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.middleware.security import (
    SecurityHeadersMiddleware,
    HTTPSRedirectMiddleware
)


@pytest.mark.unit
class TestSecurityHeadersMiddleware:
    """Test SecurityHeadersMiddleware"""

    def test_security_headers_added_to_response(self):
        """Test that security headers are added to all responses"""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        # Verify OWASP security headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert "Content-Security-Policy" in response.headers
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "Permissions-Policy" in response.headers

    def test_hsts_header_in_production_only(self, monkeypatch):
        """Test that HSTS header is only added in production"""
        # Test production mode
        from app.core import config
        mock_settings_prod = Mock()
        mock_settings_prod.APP_ENV = "prod"

        with patch.object(config, 'settings', mock_settings_prod):
            app = FastAPI()
            app.add_middleware(SecurityHeadersMiddleware)

            @app.get("/test")
            async def test_endpoint():
                return {"message": "test"}

            client = TestClient(app)
            response = client.get("/test")

            assert "Strict-Transport-Security" in response.headers
            assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
            assert "includeSubDomains" in response.headers["Strict-Transport-Security"]

    def test_no_hsts_header_in_dev_mode(self, monkeypatch):
        """Test that HSTS header is NOT added in dev mode"""
        from app.core import config
        mock_settings_dev = Mock()
        mock_settings_dev.APP_ENV = "dev"

        with patch.object(config, 'settings', mock_settings_dev):
            app = FastAPI()
            app.add_middleware(SecurityHeadersMiddleware)

            @app.get("/test")
            async def test_endpoint():
                return {"message": "test"}

            client = TestClient(app)
            response = client.get("/test")

            # HSTS should not be present in dev mode
            assert "Strict-Transport-Security" not in response.headers

    def test_csp_header_present(self):
        """Test that Content-Security-Policy header is present"""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        assert "Content-Security-Policy" in response.headers
        assert "default-src 'self'" in response.headers["Content-Security-Policy"]

    def test_permissions_policy_present(self):
        """Test that Permissions-Policy header restricts features"""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        permissions_policy = response.headers["Permissions-Policy"]
        assert "geolocation=()" in permissions_policy
        assert "microphone=()" in permissions_policy
        assert "camera=()" in permissions_policy


@pytest.mark.unit
class TestHTTPSRedirectMiddleware:
    """Test HTTPSRedirectMiddleware"""

    def test_https_redirect_in_production(self, monkeypatch):
        """Test that HTTP requests are redirected to HTTPS in production"""
        from app.core import config
        mock_settings = Mock()
        mock_settings.APP_ENV = "prod"

        with patch.object(config, 'settings', mock_settings):
            app = FastAPI()
            app.add_middleware(HTTPSRedirectMiddleware)

            @app.get("/test")
            async def test_endpoint():
                return {"message": "test"}

            client = TestClient(app, base_url="http://testserver")
            response = client.get("/test", follow_redirects=False)

            # Should redirect to HTTPS
            assert response.status_code == 301
            assert response.headers["location"].startswith("https://")

    def test_no_https_redirect_in_dev_mode(self, monkeypatch):
        """Test that HTTP requests are NOT redirected in dev mode"""
        from app.core import config
        mock_settings = Mock()
        mock_settings.APP_ENV = "dev"

        with patch.object(config, 'settings', mock_settings):
            app = FastAPI()
            app.add_middleware(HTTPSRedirectMiddleware)

            @app.get("/test")
            async def test_endpoint():
                return {"message": "test"}

            client = TestClient(app, base_url="http://testserver")
            response = client.get("/test")

            # Should NOT redirect in dev mode
            assert response.status_code == 200
            assert response.json() == {"message": "test"}

    def test_https_redirect_preserves_path(self, monkeypatch):
        """Test that HTTPS redirect preserves the original path"""
        from app.core import config
        mock_settings = Mock()
        mock_settings.APP_ENV = "prod"

        with patch.object(config, 'settings', mock_settings):
            app = FastAPI()
            app.add_middleware(HTTPSRedirectMiddleware)

            @app.get("/api/cases/{case_id}")
            async def test_endpoint(case_id: str):
                return {"case_id": case_id}

            client = TestClient(app, base_url="http://testserver")
            response = client.get("/api/cases/case_123", follow_redirects=False)

            assert response.status_code == 301
            redirect_url = response.headers["location"]
            assert redirect_url == "https://testserver/api/cases/case_123"

    def test_already_https_request_not_redirected(self, monkeypatch):
        """Test that HTTPS requests are not redirected"""
        from app.core import config
        mock_settings = Mock()
        mock_settings.APP_ENV = "prod"

        with patch.object(config, 'settings', mock_settings):
            app = FastAPI()
            app.add_middleware(HTTPSRedirectMiddleware)

            @app.get("/test")
            async def test_endpoint():
                return {"message": "test"}

            client = TestClient(app, base_url="https://testserver")
            response = client.get("/test")

            # HTTPS request should not be redirected
            assert response.status_code == 200
            assert response.json() == {"message": "test"}


@pytest.mark.unit
class TestMiddlewareIntegration:
    """Test middleware integration"""

    def test_both_middlewares_work_together(self, monkeypatch):
        """Test that both security middlewares work together"""
        from app.core import config
        mock_settings = Mock()
        mock_settings.APP_ENV = "prod"

        with patch.object(config, 'settings', mock_settings):
            app = FastAPI()
            app.add_middleware(HTTPSRedirectMiddleware)
            app.add_middleware(SecurityHeadersMiddleware)

            @app.get("/test")
            async def test_endpoint():
                return {"message": "test"}

            # Test HTTPS redirect happens first
            client = TestClient(app, base_url="http://testserver")
            response = client.get("/test", follow_redirects=False)
            assert response.status_code == 301

            # Test that HTTPS request gets security headers
            client_https = TestClient(app, base_url="https://testserver")
            response_https = client_https.get("/test")
            assert response_https.status_code == 200
            assert "X-Content-Type-Options" in response_https.headers
            assert "Strict-Transport-Security" in response_https.headers
