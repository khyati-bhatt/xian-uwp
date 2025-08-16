"""
End-to-end tests for the Xian UWP protocol.

Tests complete workflows from DApp client to wallet server,
including authentication, CORS, and API interactions.
"""

import pytest
from unittest.mock import patch, Mock

from xian_uwp import create_server, CORSConfig
from xian_uwp.client import XianWalletClientSync, XianWalletClient
from xian_uwp.models import WalletType, Permission


class TestE2EProtocol:
    """End-to-end protocol tests."""
    
    @pytest.mark.e2e
    async def test_complete_dapp_wallet_flow(self, test_server, mock_wallet):
        """Test complete DApp to wallet interaction flow."""
        # Setup server with mock wallet
        server_url = await test_server.start()
        test_server.wallet = mock_wallet
        
        # Create client
        client = XianWalletClientSync(
            app_name="Test DApp",
            app_url="https://testdapp.com",
            wallet_url=server_url
        )
        
        # 1. Check wallet availability
        available = client.check_wallet_available()
        assert available is True
        
        # 2. Request authorization
        auth_response = client.request_authorization([
            Permission.WALLET_INFO,
            Permission.BALANCE
        ])
        
        assert "request_id" in auth_response
        assert auth_response["app_name"] == "Test DApp"
        assert auth_response["status"] == "pending"
        assert "wallet_info" in auth_response["permissions"]
        assert "balance" in auth_response["permissions"]
    
    @pytest.mark.e2e
    async def test_cors_enabled_dapp_flow(self, cors_test_server, mock_wallet):
        """Test DApp flow with CORS configuration."""
        # Setup server with CORS
        server_url = await cors_test_server.start()
        cors_test_server.wallet = mock_wallet
        
        # Test CORS preflight
        response = await cors_test_server.options(
            "/api/v1/wallet/status",
            headers={
                "Origin": "https://mydapp.com",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "https://mydapp.com"
        
        # Test actual request with CORS
        response = await cors_test_server.get(
            "/api/v1/wallet/status",
            headers={"Origin": "https://mydapp.com"}
        )
        
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "https://mydapp.com"
        
        data = response.json()
        assert data["available"] is True
        assert data["wallet_type"] == "desktop"
    
    @pytest.mark.e2e
    async def test_async_client_flow(self, test_server, mock_wallet):
        """Test complete flow with async client."""
        # Setup server
        server_url = await test_server.start()
        test_server.wallet = mock_wallet
        
        # Create async client
        client = XianWalletClient(
            app_name="Async Test DApp",
            server_url=server_url
        )
        
        # Test wallet availability
        available = await client.check_wallet_available()
        assert available is True
        
        # Test authorization request
        auth_response = await client.request_authorization([Permission.WALLET_INFO])
        
        assert "request_id" in auth_response
        assert auth_response["app_name"] == "Async Test DApp"
        assert auth_response["status"] == "pending"
    
    @pytest.mark.e2e
    def test_client_error_handling(self):
        """Test client error handling with unavailable wallet."""
        # Create client pointing to non-existent server
        client = XianWalletClientSync(
            app_name="Test DApp",
            server_url="http://localhost:9999"  # Non-existent server
        )
        
        # Should handle connection errors gracefully
        available = client.check_wallet_available()
        assert available is False
    
    @pytest.mark.e2e
    def test_server_configuration_scenarios(self, mock_wallet):
        """Test different server configuration scenarios."""
        # Test desktop wallet
        desktop_server = create_server(
            wallet_type=WalletType.DESKTOP,
            cors_config=CORSConfig.localhost_dev()
        )
        desktop_server.wallet = mock_wallet
        
        assert desktop_server.wallet_type == WalletType.DESKTOP
        assert "http://localhost:3000" in desktop_server.cors_config.allow_origins
        
        # Test CLI wallet
        cli_server = create_server(
            wallet_type=WalletType.CLI,
            cors_config=CORSConfig.development()
        )
        cli_server.wallet = mock_wallet
        
        assert cli_server.wallet_type == WalletType.CLI
        assert cli_server.cors_config.allow_origins == ["*"]
        
        # Test web wallet with production CORS
        web_server = create_server(
            wallet_type=WalletType.WEB,
            cors_config=CORSConfig.production(["https://mydapp.com"])
        )
        web_server.wallet = mock_wallet
        
        assert web_server.wallet_type == WalletType.WEB
        assert web_server.cors_config.allow_origins == ["https://mydapp.com"]


class TestE2EIntegration:
    """Integration tests for complete scenarios."""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_multiple_client_connections(self, test_server, mock_wallet):
        """Test multiple clients connecting to same wallet."""
        # Setup server
        server_url = await test_server.start()
        test_server.wallet = mock_wallet
        
        # Create multiple clients
        clients = [
            XianWalletClientSync(f"DApp {i}", wallet_url=server_url)
            for i in range(3)
        ]
        
        # All clients should be able to check availability
        for client in clients:
            available = client.check_wallet_available()
            assert available is True
        
        # All clients should be able to request authorization
        for i, client in enumerate(clients):
            auth_response = client.request_authorization([Permission.WALLET_INFO])
            assert auth_response["app_name"] == f"DApp {i}"
            assert "request_id" in auth_response
    
    @pytest.mark.e2e
    def test_protocol_backwards_compatibility(self, mock_wallet):
        """Test that protocol maintains backwards compatibility."""
        # Test that old-style server creation still works
        from xian_uwp.server import WalletProtocolServer
        
        server = WalletProtocolServer(wallet_type=WalletType.DESKTOP)
        server.wallet = mock_wallet
        
        assert server.wallet_type == WalletType.DESKTOP
        assert server.cors_config is not None  # Should have default CORS config
        
        # Test that old-style client creation still works
        client = XianWalletClientSync("Legacy DApp")
        
        assert client.app_name == "Legacy DApp"
        assert client.base_url == "http://localhost:8545"  # Default port


@pytest.mark.e2e
def test_basic_protocol_functionality():
    """Basic protocol functionality test without server startup."""
    # Test server creation
    server = create_server(wallet_type=WalletType.DESKTOP)
    assert server.wallet_type == WalletType.DESKTOP
    assert server.app is not None
    assert server.cors_config is not None
    
    # Test client creation
    client = XianWalletClientSync("Test DApp")
    assert client.app_name == "Test DApp"
    assert client.base_url == "http://localhost:8545"
    
    # Test CORS configuration
    cors_config = CORSConfig.production(["https://mydapp.com"])
    assert cors_config.allow_origins == ["https://mydapp.com"]
    assert cors_config.allow_credentials is True