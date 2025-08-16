"""
Tests for server-hosted DApp CORS functionality.

This test suite verifies that DApps hosted on external servers can properly
connect to local wallets using CORS-enabled HTTP requests.
"""

import pytest
import httpx
from xian_uwp import create_server, CORSConfig
from xian_uwp.models import WalletType


class TestServerHostedDApp:
    """Test CORS functionality for server-hosted DApps."""

    @pytest.fixture
    def server_with_production_cors(self):
        """Create server with production CORS configuration."""
        cors_config = CORSConfig.production([
            "https://mydapp.com",
            "https://app.mydapp.com",
            "http://localhost:57158"  # Test origin
        ])
        
        server = create_server(
            wallet_type=WalletType.DESKTOP,
            cors_config=cors_config
        )
        
        # Start server
        import threading
        import time
        
        def run_server():
            server.run(host="127.0.0.1", port=8546)  # Use different port for testing
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(1)  # Wait for server to start
        
        yield server
        
        # Server will stop when thread ends

    @pytest.mark.asyncio
    async def test_cors_preflight_request(self, server_with_production_cors):
        """Test CORS preflight (OPTIONS) request."""
        async with httpx.AsyncClient() as client:
            response = await client.options(
                "http://127.0.0.1:8546/api/v1/wallet/status",
                headers={
                    "Origin": "https://mydapp.com",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Content-Type, Authorization"
                }
            )
            
            assert response.status_code == 200
            assert response.headers["access-control-allow-origin"] == "https://mydapp.com"
            assert "GET" in response.headers["access-control-allow-methods"]
            assert response.headers["access-control-allow-credentials"] == "true"

    @pytest.mark.asyncio
    async def test_cors_actual_request(self, server_with_production_cors):
        """Test actual CORS request with proper headers."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://127.0.0.1:8546/api/v1/wallet/status",
                headers={"Origin": "https://mydapp.com"}
            )
            
            assert response.status_code == 200
            assert response.headers["access-control-allow-origin"] == "https://mydapp.com"
            
            data = response.json()
            assert "available" in data
            assert "wallet_type" in data

    @pytest.mark.asyncio
    async def test_cors_blocked_origin(self, server_with_production_cors):
        """Test that non-allowed origins are blocked."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://127.0.0.1:8546/api/v1/wallet/status",
                headers={"Origin": "https://malicious-site.com"}
            )
            
            # Request succeeds but CORS headers are not set for blocked origin
            assert response.status_code == 200
            assert "access-control-allow-origin" not in response.headers or \
                   response.headers.get("access-control-allow-origin") != "https://malicious-site.com"

    @pytest.mark.asyncio
    async def test_cors_multiple_allowed_origins(self, server_with_production_cors):
        """Test that multiple allowed origins work correctly."""
        origins_to_test = [
            "https://mydapp.com",
            "https://app.mydapp.com",
            "http://localhost:57158"
        ]
        
        async with httpx.AsyncClient() as client:
            for origin in origins_to_test:
                response = await client.get(
                    "http://127.0.0.1:8546/api/v1/wallet/status",
                    headers={"Origin": origin}
                )
                
                assert response.status_code == 200
                assert response.headers["access-control-allow-origin"] == origin

    @pytest.mark.asyncio
    async def test_cors_auth_request(self, server_with_production_cors):
        """Test CORS with authentication request."""
        async with httpx.AsyncClient() as client:
            # Test auth request with CORS
            auth_data = {
                "app_name": "Server-Hosted DApp",
                "app_url": "https://mydapp.com",
                "permissions": ["wallet_info", "balance"]
            }
            
            response = await client.post(
                "http://127.0.0.1:8546/api/v1/auth/request",
                json=auth_data,
                headers={"Origin": "https://mydapp.com"}
            )
            
            assert response.status_code == 200
            assert response.headers["access-control-allow-origin"] == "https://mydapp.com"
            
            data = response.json()
            assert "request_id" in data

    def test_cors_config_production_preset(self):
        """Test production CORS configuration preset."""
        origins = ["https://mydapp.com", "https://app.mydapp.com"]
        config = CORSConfig.production(origins)
        
        assert config.allow_origins == origins
        assert config.allow_credentials is True
        assert "GET" in config.allow_methods
        assert "POST" in config.allow_methods
        assert "Authorization" in config.allow_headers

    def test_cors_config_localhost_dev_preset(self):
        """Test localhost development CORS configuration preset."""
        config = CORSConfig.localhost_dev()
        
        # Should include common development ports
        assert "http://localhost:3000" in config.allow_origins
        assert "http://localhost:5173" in config.allow_origins
        assert "http://localhost:8080" in config.allow_origins
        assert "http://localhost:57158" in config.allow_origins  # OpenHands port
        
        # Should include 127.0.0.1 variants
        assert "http://127.0.0.1:3000" in config.allow_origins
        assert "http://127.0.0.1:8080" in config.allow_origins

    def test_cors_config_development_preset(self):
        """Test development CORS configuration preset."""
        config = CORSConfig.development()
        
        # Should allow all origins
        assert config.allow_origins == ["*"]
        assert config.allow_credentials is True

    @pytest.mark.asyncio
    async def test_server_hosted_dapp_scenario(self):
        """Test complete server-hosted DApp scenario."""
        # This test simulates the real-world scenario where:
        # 1. DApp is hosted on external server (e.g., Vercel)
        # 2. User runs local wallet with CORS configured for that domain
        # 3. DApp makes CORS requests to local wallet
        
        # Create server with specific domain CORS
        dapp_origin = "https://my-awesome-dapp.vercel.app"
        cors_config = CORSConfig.production([dapp_origin])
        
        server = create_server(
            wallet_type=WalletType.DESKTOP,
            cors_config=cors_config
        )
        
        # Start server
        import threading
        import time
        
        def run_server():
            server.run(host="0.0.0.0", port=8547)  # Allow external connections
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(1)
        
        # Test the complete flow
        async with httpx.AsyncClient() as client:
            # 1. DApp tests connection
            status_response = await client.get(
                "http://127.0.0.1:8547/api/v1/wallet/status",
                headers={"Origin": dapp_origin}
            )
            assert status_response.status_code == 200
            assert status_response.headers["access-control-allow-origin"] == dapp_origin
            
            # 2. DApp requests authorization
            auth_response = await client.post(
                "http://127.0.0.1:8547/api/v1/auth/request",
                json={
                    "app_name": "My Awesome DApp",
                    "app_url": dapp_origin,
                    "permissions": ["wallet_info", "balance", "transactions"]
                },
                headers={"Origin": dapp_origin}
            )
            assert auth_response.status_code == 200
            assert auth_response.headers["access-control-allow-origin"] == dapp_origin
            
            # 3. Verify auth request was created
            auth_data = auth_response.json()
            assert "request_id" in auth_data
            assert auth_data["app_name"] == "My Awesome DApp"
            assert auth_data["app_url"] == dapp_origin


if __name__ == "__main__":
    pytest.main([__file__, "-v"])