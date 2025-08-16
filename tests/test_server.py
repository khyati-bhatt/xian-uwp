"""
Unit tests for Xian UWP server functionality.

Tests cover server creation, configuration, endpoint routing,
and basic HTTP functionality.
"""

import pytest
from fastapi.testclient import TestClient

from xian_uwp import create_server, CORSConfig
from xian_uwp.models import WalletType, Permission, AuthorizationRequest
from xian_uwp.server import WalletProtocolServer


class TestServerCreation:
    """Test server creation and configuration."""
    
    @pytest.mark.unit
    def test_server_creation_basic(self):
        """Test basic server creation."""
        server = WalletProtocolServer(wallet_type=WalletType.DESKTOP)
        
        assert server.wallet_type == WalletType.DESKTOP
        assert server.app is not None
        assert server.cors_config is not None
    
    @pytest.mark.unit
    def test_server_creation_with_cors(self):
        """Test server creation with CORS configuration."""
        cors_config = CORSConfig.production(["https://mydapp.com"])
        server = WalletProtocolServer(
            wallet_type=WalletType.DESKTOP,
            cors_config=cors_config
        )
        
        assert server.cors_config == cors_config
        assert server.cors_config.allow_origins == ["https://mydapp.com"]
    
    @pytest.mark.unit
    def test_server_creation_factory(self):
        """Test server creation using factory function."""
        server = create_server(
            wallet_type=WalletType.CLI,
            cors_config=CORSConfig.development()
        )
        
        assert isinstance(server, WalletProtocolServer)
        assert server.wallet_type == WalletType.CLI
    
    @pytest.mark.unit
    def test_server_with_wallet(self, mock_wallet):
        """Test server with wallet instance."""
        server = WalletProtocolServer(wallet_type=WalletType.DESKTOP)
        server.wallet = mock_wallet
        
        assert server.wallet is not None
        assert server.wallet.is_locked() is False


class TestServerEndpoints:
    """Test server HTTP endpoints."""
    
    @pytest.mark.unit
    def test_status_endpoint(self, test_client):
        """Test wallet status endpoint."""
        response = test_client.get("/api/v1/wallet/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert "wallet_type" in data
        assert data["wallet_type"] == "desktop"
    
    @pytest.mark.unit
    def test_auth_request_endpoint(self, test_client):
        """Test authentication request endpoint."""
        auth_data = {
            "app_name": "Test DApp",
            "app_url": "https://testdapp.com",
            "permissions": ["wallet_info", "balance"]
        }
        
        response = test_client.post("/api/v1/auth/request", json=auth_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert data["app_name"] == "Test DApp"
        assert data["status"] == "pending"
    
    @pytest.mark.unit
    def test_wallet_info_endpoint_unauthorized(self, test_client):
        """Test wallet info endpoint without authorization."""
        response = test_client.get("/api/v1/wallet/info")
        
        # Should require authorization
        assert response.status_code in [401, 403]
    
    @pytest.mark.unit
    def test_balance_endpoint_unauthorized(self, test_client):
        """Test balance endpoint without authorization."""
        response = test_client.get("/api/v1/balance/TAU")
        
        # Should require authorization
        assert response.status_code in [401, 403]
    
    @pytest.mark.unit
    def test_invalid_endpoint(self, test_client):
        """Test invalid endpoint returns 404."""
        response = test_client.get("/api/v1/invalid/endpoint")
        
        assert response.status_code == 404


class TestServerValidation:
    """Test server request validation."""
    
    @pytest.mark.unit
    def test_auth_request_validation_empty_name(self, test_client):
        """Test auth request validation with empty app name."""
        auth_data = {
            "app_name": "",
            "app_url": "https://testdapp.com",
            "permissions": ["wallet_info"]
        }
        
        response = test_client.post("/api/v1/auth/request", json=auth_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.unit
    def test_auth_request_validation_invalid_url(self, test_client):
        """Test auth request validation with invalid URL."""
        auth_data = {
            "app_name": "Test DApp",
            "app_url": "not-a-url",
            "permissions": ["wallet_info"]
        }
        
        response = test_client.post("/api/v1/auth/request", json=auth_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.unit
    def test_auth_request_validation_empty_permissions(self, test_client):
        """Test auth request validation with empty permissions."""
        auth_data = {
            "app_name": "Test DApp",
            "app_url": "https://testdapp.com",
            "permissions": []
        }
        
        response = test_client.post("/api/v1/auth/request", json=auth_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.unit
    def test_auth_request_validation_invalid_permission(self, test_client):
        """Test auth request validation with invalid permission."""
        auth_data = {
            "app_name": "Test DApp",
            "app_url": "https://testdapp.com",
            "permissions": ["invalid_permission"]
        }
        
        response = test_client.post("/api/v1/auth/request", json=auth_data)
        
        assert response.status_code == 422  # Validation error


class TestServerConfiguration:
    """Test server configuration options."""
    
    @pytest.mark.unit
    def test_server_default_cors_config(self):
        """Test server uses default CORS config."""
        server = WalletProtocolServer(wallet_type=WalletType.DESKTOP)
        
        # Should have default localhost development config
        assert server.cors_config is not None
        assert "http://localhost:3000" in server.cors_config.allow_origins
    
    @pytest.mark.unit
    def test_server_custom_cors_config(self):
        """Test server with custom CORS config."""
        cors_config = CORSConfig.production(["https://mydapp.com"])
        server = WalletProtocolServer(
            wallet_type=WalletType.DESKTOP,
            cors_config=cors_config
        )
        
        assert server.cors_config.allow_origins == ["https://mydapp.com"]
        assert server.cors_config.allow_credentials is True
    
    @pytest.mark.unit
    def test_server_wallet_types(self):
        """Test server with different wallet types."""
        for wallet_type in WalletType:
            server = WalletProtocolServer(wallet_type=wallet_type)
            assert server.wallet_type == wallet_type


class TestServerMiddleware:
    """Test server middleware functionality."""
    
    @pytest.mark.unit
    def test_cors_middleware_applied(self, test_client):
        """Test that CORS middleware is applied."""
        response = test_client.options(
            "/api/v1/wallet/status",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
    
    @pytest.mark.unit
    def test_json_response_headers(self, test_client):
        """Test that JSON responses have correct headers."""
        response = test_client.get("/api/v1/wallet/status")
        
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")


class TestServerErrorHandling:
    """Test server error handling."""
    
    @pytest.mark.unit
    def test_malformed_json_request(self, test_client):
        """Test handling of malformed JSON requests."""
        response = test_client.post(
            "/api/v1/auth/request",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    @pytest.mark.unit
    def test_missing_content_type(self, test_client):
        """Test handling of requests without content type."""
        response = test_client.post(
            "/api/v1/auth/request",
            json={"app_name": "Test"}
        )
        
        # Should still work with proper JSON
        assert response.status_code in [200, 422]  # Either success or validation error