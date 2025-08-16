"""
Simple tests to verify basic components work correctly.

These are quick smoke tests to ensure the core functionality
is working before running more complex test suites.
"""

import pytest

from xian_uwp import create_server, CORSConfig
from xian_uwp.models import WalletType, Permission
from xian_uwp.client import XianWalletClientSync


class TestBasicComponents:
    """Test basic component functionality."""
    
    @pytest.mark.unit
    def test_enums_work(self):
        """Test that enums are properly defined."""
        # Test WalletType enum
        assert WalletType.DESKTOP == "desktop"
        assert WalletType.CLI == "cli"
        assert WalletType.WEB == "web"
        
        # Test Permission enum
        assert Permission.WALLET_INFO == "wallet_info"
        assert Permission.BALANCE == "balance"
        assert Permission.TRANSACTIONS == "transactions"
        assert Permission.SIGN_MESSAGE == "sign_message"
    
    @pytest.mark.unit
    def test_cors_config_creation(self):
        """Test CORS configuration creation."""
        # Development config
        dev_config = CORSConfig.development()
        assert dev_config.allow_origins == ["*"]
        assert dev_config.allow_credentials is True
        
        # Production config
        prod_config = CORSConfig.production(["https://mydapp.com"])
        assert prod_config.allow_origins == ["https://mydapp.com"]
        assert prod_config.allow_credentials is True
        
        # Localhost dev config
        localhost_config = CORSConfig.localhost_dev()
        assert "http://localhost:3000" in localhost_config.allow_origins
        assert localhost_config.allow_credentials is True
    
    @pytest.mark.unit
    def test_server_creation(self):
        """Test server creation."""
        server = create_server(wallet_type=WalletType.DESKTOP)
        
        assert server.wallet_type == WalletType.DESKTOP
        assert server.app is not None
        assert server.cors_config is not None
    
    @pytest.mark.unit
    def test_client_creation(self):
        """Test client creation."""
        client = XianWalletClientSync("Test App")
        
        assert client.client.app_name == "Test App"
        assert client.client.server_url == "http://127.0.0.1:8545"
        assert client.client.session_token is None
    
    @pytest.mark.unit
    def test_server_with_custom_cors(self):
        """Test server creation with custom CORS."""
        cors_config = CORSConfig.production(["https://mydapp.com"])
        server = create_server(
            wallet_type=WalletType.WEB,
            cors_config=cors_config
        )
        
        assert server.wallet_type == WalletType.WEB
        assert server.cors_config.allow_origins == ["https://mydapp.com"]
    
    @pytest.mark.unit
    def test_client_with_custom_url(self):
        """Test client creation with custom URL."""
        client = XianWalletClientSync(
            app_name="Custom App",
            app_url="https://myapp.com",
            server_url="http://localhost:8546"
        )
        
        assert client.client.app_name == "Custom App"
        assert client.client.app_url == "https://myapp.com"
        assert client.client.server_url == "http://localhost:8546"


@pytest.mark.unit
def test_imports_work():
    """Test that all imports work correctly."""
    # Test main imports
    from xian_uwp import create_server, CORSConfig
    from xian_uwp.models import WalletType, Permission
    from xian_uwp.client import XianWalletClientSync, XianWalletClient
    from xian_uwp.server import WalletProtocolServer
    
    # All imports should work without errors
    assert create_server is not None
    assert CORSConfig is not None
    assert WalletType is not None
    assert Permission is not None
    assert XianWalletClientSync is not None
    assert XianWalletClient is not None
    assert WalletProtocolServer is not None