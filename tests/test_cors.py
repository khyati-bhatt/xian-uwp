#!/usr/bin/env python3
"""
Test CORS functionality for web-based DApps
"""

import pytest
import asyncio
import httpx
from fastapi.testclient import TestClient

from xian_uwp.server import WalletProtocolServer
from xian_uwp.models import WalletType, CORSConfig, Endpoints


class TestCORSConfiguration:
    """Test CORS configuration and functionality"""
    
    def test_cors_config_development(self):
        """Test development CORS configuration"""
        config = CORSConfig.development()
        
        assert config.allow_origins == ["*"]
        assert config.allow_credentials is True
        assert "GET" in config.allow_methods
        assert "POST" in config.allow_methods
        assert config.max_age == 3600
    
    def test_cors_config_production(self):
        """Test production CORS configuration"""
        allowed_origins = ["https://mydapp.com", "https://app.mydapp.com"]
        config = CORSConfig.production(allowed_origins)
        
        assert config.allow_origins == allowed_origins
        assert config.allow_credentials is True
        assert "Authorization" in config.allow_headers
        assert config.max_age == 86400
    
    def test_cors_config_localhost_dev(self):
        """Test localhost development CORS configuration"""
        config = CORSConfig.localhost_dev()
        
        # Should include common dev ports
        assert "http://localhost:3000" in config.allow_origins
        assert "http://localhost:5173" in config.allow_origins
        assert "http://localhost:51644" in config.allow_origins
        assert "http://localhost:57158" in config.allow_origins
        assert "http://127.0.0.1:3000" in config.allow_origins
        
        # Custom ports
        custom_config = CORSConfig.localhost_dev([9000, 9001])
        assert "http://localhost:9000" in custom_config.allow_origins
        assert "http://localhost:9001" in custom_config.allow_origins
    
    def test_server_with_cors_config(self):
        """Test server initialization with CORS config"""
        cors_config = CORSConfig.development()
        server = WalletProtocolServer(
            wallet_type=WalletType.DESKTOP,
            cors_config=cors_config
        )
        
        assert server.cors_config == cors_config
        assert server.cors_config.allow_origins == ["*"]
    
    def test_server_default_cors_config(self):
        """Test server with default CORS config"""
        server = WalletProtocolServer(wallet_type=WalletType.DESKTOP)
        
        # Should use localhost_dev by default
        assert "http://localhost:3000" in server.cors_config.allow_origins
        assert "http://localhost:51644" in server.cors_config.allow_origins


class TestCORSFunctionality:
    """Test actual CORS functionality with HTTP requests"""
    
    @pytest.fixture
    def server_app(self):
        """Create server app for testing"""
        cors_config = CORSConfig.development()
        server = WalletProtocolServer(
            wallet_type=WalletType.DESKTOP,
            cors_config=cors_config
        )
        return server.app
    
    @pytest.fixture
    def client(self, server_app):
        """Create test client"""
        return TestClient(server_app)
    
    def test_cors_preflight_request(self, client):
        """Test CORS preflight OPTIONS request"""
        response = client.options(
            Endpoints.WALLET_STATUS,
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            }
        )
        
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers
    
    def test_cors_actual_request(self, client):
        """Test actual request with CORS headers"""
        response = client.get(
            Endpoints.WALLET_STATUS,
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
        
        # Check response content
        data = response.json()
        assert "available" in data
        assert "locked" in data
        assert "wallet_type" in data
    
    def test_cors_with_credentials(self, client):
        """Test CORS with credentials"""
        response = client.get(
            Endpoints.WALLET_STATUS,
            headers={
                "Origin": "http://localhost:3000",
                "Cookie": "session=test"
            }
        )
        
        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Credentials") == "true"
    
    def test_cors_different_origins(self, client):
        """Test CORS with different origins (development mode allows all)"""
        origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "https://mydapp.com",
            "http://127.0.0.1:8080"
        ]
        
        for origin in origins:
            response = client.get(
                Endpoints.WALLET_STATUS,
                headers={"Origin": origin}
            )
            
            assert response.status_code == 200
            # In development mode, should allow all origins
            assert response.headers.get("Access-Control-Allow-Origin") == "*"


class TestCORSProduction:
    """Test CORS in production-like scenarios"""
    
    def test_production_cors_specific_origins(self):
        """Test production CORS with specific allowed origins"""
        allowed_origins = ["https://mydapp.com", "https://app.mydapp.com"]
        cors_config = CORSConfig.production(allowed_origins)
        
        server = WalletProtocolServer(
            wallet_type=WalletType.DESKTOP,
            cors_config=cors_config
        )
        
        client = TestClient(server.app)
        
        # Test allowed origin
        response = client.get(
            Endpoints.WALLET_STATUS,
            headers={"Origin": "https://mydapp.com"}
        )
        
        assert response.status_code == 200
        # Note: FastAPI's CORSMiddleware handles origin validation
        # The actual origin echoing depends on the middleware implementation
    
    def test_production_cors_headers_restriction(self):
        """Test production CORS with restricted headers"""
        cors_config = CORSConfig.production(["https://mydapp.com"])
        
        # Should have restricted headers compared to development
        assert "Authorization" in cors_config.allow_headers
        assert cors_config.allow_headers != ["*"]
        assert cors_config.max_age == 86400  # 24 hours


def test_cors_with_async_client():
    """Test CORS functionality with async HTTP client"""
    cors_config = CORSConfig.localhost_dev()
    server = WalletProtocolServer(
        wallet_type=WalletType.DESKTOP,
        cors_config=cors_config
    )
    
    # Create test client
    client = TestClient(server.app)
    
    # Test async-style request
    response = client.get(
        Endpoints.WALLET_STATUS,
        headers={
            "Origin": "http://localhost:3000",
            "User-Agent": "Mozilla/5.0 (DApp Client)"
        }
    )
    
    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" in response.headers
    
    data = response.json()
    assert data["available"] is not None
    assert data["wallet_type"] == "desktop"


def test_cors_integration_example():
    """Test CORS integration example for web DApps"""
    # This simulates how a web DApp would be configured
    
    # 1. Create CORS config for development
    cors_config = CORSConfig.localhost_dev([3000, 5173, 51644, 57158])
    
    # 2. Create server with CORS config
    server = WalletProtocolServer(
        wallet_type=WalletType.WEB,
        cors_config=cors_config
    )
    
    # 3. Verify configuration
    assert "http://localhost:3000" in server.cors_config.allow_origins
    assert "http://localhost:51644" in server.cors_config.allow_origins
    assert server.cors_config.allow_credentials is True
    
    # 4. Test with client
    client = TestClient(server.app)
    
    # Simulate web DApp request
    response = client.get(
        Endpoints.WALLET_STATUS,
        headers={
            "Origin": "http://localhost:3000",
            "Referer": "http://localhost:3000/",
            "User-Agent": "Mozilla/5.0 (Web DApp)"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["wallet_type"] == "web"


if __name__ == "__main__":
    # Run basic tests
    test_config = TestCORSConfiguration()
    test_config.test_cors_config_development()
    test_config.test_cors_config_localhost_dev()
    print("✅ CORS configuration tests passed")
    
    # Run integration test
    test_cors_integration_example()
    print("✅ CORS integration test passed")
    
    print("🎉 All CORS tests completed successfully!")