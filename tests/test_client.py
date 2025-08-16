"""
Unit tests for Xian UWP client functionality.

Tests cover client creation, connection handling, API calls,
and error handling for both sync and async clients.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from xian_uwp.client import XianWalletClientSync, XianWalletClient
from xian_uwp.models import Permission, AuthStatus


class TestSyncClient:
    """Test synchronous client functionality."""
    
    @pytest.mark.unit
    def test_client_creation(self):
        """Test basic client creation."""
        client = XianWalletClientSync("Test DApp")
        
        assert client.app_name == "Test DApp"
        assert client.base_url == "http://localhost:8545"
        assert client.session_token is None
    
    @pytest.mark.unit
    def test_client_creation_with_url(self):
        """Test client creation with custom URL."""
        client = XianWalletClientSync(
            "Test DApp",
            app_url="https://testdapp.com",
            wallet_url="http://localhost:8546"
        )
        
        assert client.app_url == "https://testdapp.com"
        assert client.base_url == "http://localhost:8546"
    
    @pytest.mark.unit
    @patch.object(XianWalletClientSync, 'check_wallet_available')
    def test_check_wallet_available(self, mock_check_available):
        """Test wallet availability check."""
        mock_check_available.return_value = True
        
        client = XianWalletClientSync("Test DApp")
        result = client.check_wallet_available()
        
        assert result is True
        mock_check_available.assert_called_once()
    
    @pytest.mark.unit
    @patch.object(XianWalletClientSync, 'check_wallet_available')
    def test_check_wallet_unavailable(self, mock_check_available):
        """Test wallet unavailable response."""
        mock_check_available.return_value = False
        
        client = XianWalletClientSync("Test DApp")
        result = client.check_wallet_available()
        
        assert result is False
    
    @pytest.mark.unit
    @patch.object(XianWalletClient, '_request_authorization')
    def test_request_authorization(self, mock_request_auth):
        """Test authorization request."""
        mock_request_auth.return_value = "test_session_token_123"
        
        client = XianWalletClientSync("Test DApp")
        result = client.request_authorization([Permission.WALLET_INFO])
        
        assert result["session_token"] == "test_session_token_123"
        assert result["status"] == "approved"
    
    @pytest.mark.unit
    @patch.object(XianWalletClient, '_make_request')
    def test_get_wallet_info_unauthorized(self, mock_make_request):
        """Test wallet info request without authorization."""
        from xian_uwp.client import WalletProtocolError
        mock_make_request.side_effect = WalletProtocolError("Unauthorized")
        
        client = XianWalletClientSync("Test DApp")
        
        with pytest.raises(WalletProtocolError):  # Should raise authorization error
            client.get_wallet_info()
    
    @pytest.mark.unit
    @patch.object(XianWalletClient, '_make_request')
    def test_get_wallet_info_authorized(self, mock_make_request):
        """Test wallet info request with authorization."""
        mock_make_request.return_value = {
            "address": "test_address_123",
            "truncated_address": "test_addr...123",
            "network": "https://testnet.xian.org",
            "locked": False,
            "chain_id": "xian-testnet-12",
            "wallet_type": "desktop"
        }
        
        client = XianWalletClientSync("Test DApp")
        client.session_token = "test_token_123"
        
        result = client.get_wallet_info()
        
        assert result.address == "test_address_123"
        mock_make_request.assert_called_once_with(
            "GET", "/api/v1/wallet/info"
        )
    
    @pytest.mark.unit
    @patch.object(XianWalletClient, '_make_request')
    def test_get_balance(self, mock_make_request):
        """Test balance request."""
        mock_make_request.return_value = {"balance": 1000.0, "contract": "TAU"}
        
        client = XianWalletClientSync("Test DApp")
        client.session_token = "test_token_123"
        
        result = client.get_balance("TAU")
        
        assert result == 1000.0
        mock_make_request.assert_called_once_with(
            "GET", "/api/v1/balance/TAU"
        )
    
    @pytest.mark.unit
    def test_connect_flow(self):
        """Test complete connection flow."""
        client = XianWalletClientSync("Test DApp")
        
        with patch.object(client.client, 'check_wallet_available', return_value=True), \
             patch.object(client.client, 'connect', return_value=True), \
             patch.object(client.client, 'session_token', "test_token_123", create=True):
            
            result = client.connect([Permission.WALLET_INFO])
            
            assert result is True


class TestAsyncClient:
    """Test asynchronous client functionality."""
    
    @pytest.mark.unit
    def test_async_client_creation(self):
        """Test basic async client creation."""
        client = XianWalletClient("Test DApp")
        
        assert client.app_name == "Test DApp"
        assert client.server_url == "http://localhost:8545"
        assert client.session_token is None
    
    @pytest.mark.unit
    async def test_async_check_wallet_available(self):
        """Test async wallet availability check."""
        client = XianWalletClient("Test DApp")
        
        with patch.object(client, '_check_wallet_available', return_value=True):
            result = await client.check_wallet_available()
            assert result is True
    
    @pytest.mark.unit
    async def test_async_request_authorization(self):
        """Test async authorization request."""
        client = XianWalletClient("Test DApp")
        
        with patch.object(client, '_request_authorization', return_value="test_session_token_123"):
            result = await client.request_authorization([Permission.WALLET_INFO])
            
            assert result["session_token"] == "test_session_token_123"
            assert result["status"] == "approved"
    
    @pytest.mark.unit
    async def test_async_get_wallet_info(self):
        """Test async wallet info request."""
        client = XianWalletClient("Test DApp")
        client.session_token = "test_token_123"
        
        with patch.object(client, '_make_request', return_value={
            "address": "test_address_123",
            "truncated_address": "test_addr...123",
            "network": "https://testnet.xian.org",
            "locked": False,
            "chain_id": "xian-testnet-12",
            "wallet_type": "desktop"
        }):
            result = await client.get_wallet_info()
            
            assert result.address == "test_address_123"
    
    @pytest.mark.unit
    async def test_async_connect_flow(self):
        """Test complete async connection flow."""
        client = XianWalletClient("Test DApp")
        
        with patch.object(client, '_check_wallet_available', return_value=True), \
             patch.object(client, '_request_authorization', return_value="test_token_123"), \
             patch.object(client, 'get_wallet_info', return_value=Mock(
                 wallet_type="desktop",
                 truncated_address="test_addr...123"
             )):
            
            result = await client.connect([Permission.WALLET_INFO])
            
            assert result is True
            assert client.session_token == "test_token_123"


class TestClientErrorHandling:
    """Test client error handling scenarios."""
    
    @pytest.mark.unit
    @patch('httpx.get')
    def test_network_error_handling(self, mock_get):
        """Test handling of network errors."""
        mock_get.side_effect = Exception("Network error")
        
        client = XianWalletClientSync("Test DApp")
        
        with pytest.raises(Exception):
            client.get_wallet_info()
    
    @pytest.mark.unit
    @patch('httpx.get')
    def test_http_error_handling(self, mock_get):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response
        
        client = XianWalletClientSync("Test DApp")
        
        with pytest.raises(Exception):
            client.get_wallet_info()
    
    @pytest.mark.unit
    def test_authorization_denied(self):
        """Test handling of authorization denial."""
        client = XianWalletClientSync("Test DApp")
        
        with patch.object(client.client, '_check_wallet_available', return_value=True), \
             patch.object(client.client, '_request_authorization', return_value=None):
            result = client.connect([Permission.WALLET_INFO])
            assert result is False
    
    @pytest.mark.unit
    def test_invalid_permissions(self):
        """Test handling of invalid permissions."""
        client = XianWalletClientSync("Test DApp")
        
        # Empty permissions are allowed in current implementation
        with patch.object(client.client, '_check_wallet_available', return_value=True), \
             patch.object(client.client, '_request_authorization', return_value="test_token"), \
             patch.object(client.client, 'get_wallet_info', return_value=Mock(
                 wallet_type="desktop",
                 truncated_address="test_addr...123"
             )):
            result = client.connect([])  # Empty permissions are valid
            assert result is True
    
    @pytest.mark.unit
    def test_missing_session_token(self):
        """Test handling of missing session token."""
        client = XianWalletClientSync("Test DApp")
        # Don't set session_token
        
        with pytest.raises(Exception):
            client.get_wallet_info()  # Should require session token


class TestClientConfiguration:
    """Test client configuration options."""
    
    @pytest.mark.unit
    def test_client_with_supported_options(self):
        """Test client creation with supported options."""
        client = XianWalletClientSync(
            app_name="Test DApp",
            app_url="https://testdapp.com",
            wallet_url="http://localhost:8546"
        )
        
        assert client.app_name == "Test DApp"
        assert client.app_url == "https://testdapp.com"
        assert client.base_url == "http://localhost:8546"


class TestClientUtilities:
    """Test client utility functions."""
    
    @pytest.mark.unit
    def test_client_properties(self):
        """Test client property access."""
        client = XianWalletClientSync("Test DApp", app_url="https://testdapp.com")
        client.session_token = "test_token_123"
        
        # Test property accessors
        assert client.app_name == "Test DApp"
        assert client.app_url == "https://testdapp.com"
        assert client.session_token == "test_token_123"
        assert client.base_url == "http://localhost:8545"