"""
Integration tests for CORS (Cross-Origin Resource Sharing) functionality.

Tests verify that the Xian UWP server properly handles CORS requests
from web-based DApps hosted on different domains.
"""

import pytest
from fastapi.testclient import TestClient

from xian_uwp import create_server, CORSConfig
from xian_uwp.models import WalletType


class TestCORSConfiguration:
    """Test CORS configuration classes and presets."""

    @pytest.mark.unit
    def test_cors_config_development(self):
        """Test development CORS configuration."""
        config = CORSConfig.development()
        
        assert config.allow_origins == ["*"]
        assert config.allow_credentials is True
        assert "GET" in config.allow_methods
        assert "POST" in config.allow_methods
        assert "OPTIONS" in config.allow_methods

    @pytest.mark.unit
    def test_cors_config_production(self):
        """Test production CORS configuration."""
        origins = ["https://mydapp.com", "https://app.mydapp.com"]
        config = CORSConfig.production(origins)
        
        assert config.allow_origins == origins
        assert config.allow_credentials is True
        assert "GET" in config.allow_methods
        assert "POST" in config.allow_methods

    @pytest.mark.unit
    def test_cors_config_localhost_dev(self):
        """Test localhost development CORS configuration."""
        config = CORSConfig.localhost_dev()
        
        # Should include common development ports
        assert "http://localhost:3000" in config.allow_origins
        assert "http://localhost:5173" in config.allow_origins
        assert "http://localhost:8080" in config.allow_origins
        
        # Should include 127.0.0.1 variants
        assert "http://127.0.0.1:3000" in config.allow_origins
        assert "http://127.0.0.1:8080" in config.allow_origins

    @pytest.mark.unit
    def test_server_with_cors_config(self):
        """Test server creation with CORS configuration."""
        cors_config = CORSConfig.production(["https://mydapp.com"])
        server = create_server(
            wallet_type=WalletType.DESKTOP,
            cors_config=cors_config
        )
        
        assert server.cors_config == cors_config

    @pytest.mark.unit
    def test_server_default_cors_config(self):
        """Test server with default CORS configuration."""
        server = create_server(wallet_type=WalletType.DESKTOP)
        
        # Should use localhost_dev by default
        assert server.cors_config is not None
        assert "http://localhost:3000" in server.cors_config.allow_origins


class TestCORSFunctionality:
    """Test actual CORS functionality with HTTP requests."""

    @pytest.fixture
    def cors_client(self, mock_wallet):
        """Create a test client with CORS configuration."""
        cors_config = CORSConfig.production([
            "https://mydapp.com",
            "https://app.mydapp.com",
            "http://localhost:3000"
        ])
        
        server = create_server(
            wallet_type=WalletType.DESKTOP,
            cors_config=cors_config
        )
        server.wallet = mock_wallet
        
        return TestClient(server.app)

    @pytest.mark.integration
    def test_cors_preflight_request(self, cors_client):
        """Test CORS preflight (OPTIONS) request."""
        response = cors_client.options(
            "/api/v1/wallet/status",
            headers={
                "Origin": "https://mydapp.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "https://mydapp.com"
        assert "GET" in response.headers["access-control-allow-methods"]
        assert response.headers["access-control-allow-credentials"] == "true"

    @pytest.mark.integration
    def test_cors_actual_request(self, cors_client):
        """Test actual CORS request with proper headers."""
        response = cors_client.get(
            "/api/v1/wallet/status",
            headers={"Origin": "https://mydapp.com"}
        )
        
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "https://mydapp.com"
        
        data = response.json()
        assert "available" in data

    @pytest.mark.integration
    def test_cors_with_credentials(self, cors_client):
        """Test CORS request with credentials."""
        response = cors_client.get(
            "/api/v1/wallet/status",
            headers={
                "Origin": "https://mydapp.com",
                "Cookie": "session=test_session"
            }
        )
        
        assert response.status_code == 200
        assert response.headers["access-control-allow-credentials"] == "true"

    @pytest.mark.integration
    def test_cors_different_origins(self, cors_client):
        """Test CORS with different allowed origins."""
        origins_to_test = [
            "https://mydapp.com",
            "https://app.mydapp.com",
            "http://localhost:3000"
        ]
        
        for origin in origins_to_test:
            response = cors_client.get(
                "/api/v1/wallet/status",
                headers={"Origin": origin}
            )
            
            assert response.status_code == 200
            assert response.headers["access-control-allow-origin"] == origin

    @pytest.mark.integration
    def test_cors_blocked_origin(self, cors_client):
        """Test that non-allowed origins are blocked."""
        response = cors_client.get(
            "/api/v1/wallet/status",
            headers={"Origin": "https://malicious-site.com"}
        )
        
        # Request succeeds but CORS headers are not set for blocked origin
        assert response.status_code == 200
        # CORS headers should not be set for disallowed origin
        cors_origin = response.headers.get("access-control-allow-origin")
        assert cors_origin != "https://malicious-site.com"


class TestCORSProduction:
    """Test production CORS scenarios."""

    @pytest.mark.integration
    def test_production_cors_specific_origins(self, mock_wallet):
        """Test production CORS allows only specific origins."""
        cors_config = CORSConfig.production(["https://mydapp.com"])
        server = create_server(
            wallet_type=WalletType.DESKTOP,
            cors_config=cors_config
        )
        server.wallet = mock_wallet
        
        client = TestClient(server.app)
        
        # Allowed origin should work
        response = client.get(
            "/api/v1/wallet/status",
            headers={"Origin": "https://mydapp.com"}
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "https://mydapp.com"
        
        # Disallowed origin should not get CORS headers
        response = client.get(
            "/api/v1/wallet/status",
            headers={"Origin": "https://malicious-site.com"}
        )
        assert response.status_code == 200  # Request succeeds
        # But CORS headers should not be set for disallowed origin
        assert response.headers.get("access-control-allow-origin") != "https://malicious-site.com"

    @pytest.mark.integration
    def test_production_cors_headers_restriction(self, mock_wallet):
        """Test production CORS header restrictions."""
        cors_config = CORSConfig.production(["https://mydapp.com"])
        server = create_server(
            wallet_type=WalletType.DESKTOP,
            cors_config=cors_config
        )
        server.wallet = mock_wallet
        
        client = TestClient(server.app)
        
        # Test preflight with allowed headers
        response = client.options(
            "/api/v1/wallet/status",
            headers={
                "Origin": "https://mydapp.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type, Authorization"
            }
        )
        
        assert response.status_code == 200
        allowed_headers = response.headers["access-control-allow-headers"]
        assert "Content-Type" in allowed_headers
        assert "Authorization" in allowed_headers


class TestCORSIntegration:
    """Test complete CORS integration scenarios."""

    @pytest.mark.integration
    def test_server_hosted_dapp_scenario(self, mock_wallet):
        """Test complete server-hosted DApp CORS scenario."""
        dapp_origin = "https://my-awesome-dapp.vercel.app"
        
        # Configure wallet with CORS for DApp domain
        cors_config = CORSConfig.production([dapp_origin])
        server = create_server(
            wallet_type=WalletType.DESKTOP,
            cors_config=cors_config
        )
        server.wallet = mock_wallet
        
        client = TestClient(server.app)
        
        # DApp checks wallet availability
        response = client.get(
            "/api/v1/wallet/status",
            headers={"Origin": dapp_origin}
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == dapp_origin
        
        # DApp requests authorization
        auth_data = {
            "app_name": "My Awesome DApp",
            "app_url": dapp_origin,
            "permissions": ["wallet_info", "balance"]
        }
        
        response = client.post(
            "/api/v1/auth/request",
            json=auth_data,
            headers={"Origin": dapp_origin}
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == dapp_origin
        
        # Verify auth request was created
        auth_response = response.json()
        assert "request_id" in auth_response
        assert auth_response["status"] == "pending"

    @pytest.mark.integration
    def test_development_cors_scenario(self, mock_wallet):
        """Test development CORS scenario with localhost."""
        cors_config = CORSConfig.localhost_dev()
        server = create_server(
            wallet_type=WalletType.DESKTOP,
            cors_config=cors_config
        )
        server.wallet = mock_wallet
        
        client = TestClient(server.app)
        
        # Test common development origins
        dev_origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:8080"
        ]
        
        for origin in dev_origins:
            response = client.get(
                "/api/v1/wallet/status",
                headers={"Origin": origin}
            )
            assert response.status_code == 200
            assert response.headers["access-control-allow-origin"] == origin