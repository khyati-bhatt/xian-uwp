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
    @patch('httpx.get')
    def test_check_wallet_available(self, mock_get):
        """Test wallet availability check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"available": True}
        mock_get.return_value = mock_response
        
        client = XianWalletClientSync("Test DApp")
        result = client.check_wallet_available()
        
        assert result is True
        mock_get.assert_called_once_with(
            "http://localhost:8545/api/v1/wallet/status",
            timeout=5.0
        )
    
    @pytest.mark.unit
    @patch('httpx.get')
    def test_check_wallet_unavailable(self, mock_get):
        """Test wallet unavailable response."""
        mock_get.side_effect = Exception("Connection failed")
        
        client = XianWalletClientSync("Test DApp")
        result = client.check_wallet_available()
        
        assert result is False
    
    @pytest.mark.unit
    @patch('httpx.post')
    def test_request_authorization(self, mock_post):
        """Test authorization request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "request_id": "test_request_123",
            "app_name": "Test DApp",
            "status": "pending"
        }
        mock_post.return_value = mock_response
        
        client = XianWalletClientSync("Test DApp")
        result = client.request_authorization([Permission.WALLET_INFO])
        
        assert result["request_id"] == "test_request_123"
        assert result["status"] == "pending"
    
    @pytest.mark.unit
    @patch('httpx.get')
    def test_get_wallet_info_unauthorized(self, mock_get):
        """Test wallet info request without authorization."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        client = XianWalletClientSync("Test DApp")
        
        with pytest.raises(Exception):  # Should raise authorization error
            client.get_wallet_info()
    
    @pytest.mark.unit
    @patch('httpx.get')
    def test_get_wallet_info_authorized(self, mock_get):
        """Test wallet info request with authorization."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "address": "test_address_123",
            "network": "https://testnet.xian.org"
        }
        mock_get.return_value = mock_response
        
        client = XianWalletClientSync("Test DApp")
        client.session_token = "test_token_123"
        
        result = client.get_wallet_info()
        
        assert result["address"] == "test_address_123"
        mock_get.assert_called_once_with(
            "http://localhost:8545/api/v1/wallet/info",
            headers={"Authorization": "Bearer test_token_123"},
            timeout=10.0
        )
    
    @pytest.mark.unit
    @patch('httpx.get')
    def test_get_balance(self, mock_get):
        """Test balance request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"balance": 1000.0}
        mock_get.return_value = mock_response
        
        client = XianWalletClientSync("Test DApp")
        client.session_token = "test_token_123"
        
        result = client.get_balance("TAU")
        
        assert result == 1000.0
        mock_get.assert_called_once_with(
            "http://localhost:8545/api/v1/wallet/balance/TAU",
            headers={"Authorization": "Bearer test_token_123"},
            timeout=10.0
        )
    
    @pytest.mark.unit
    def test_connect_flow(self):
        """Test complete connection flow."""
        client = XianWalletClientSync("Test DApp")
        
        with patch.object(client, 'check_wallet_available', return_value=True), \
             patch.object(client, 'request_authorization', return_value={
                 "request_id": "test_request_123",
                 "status": "pending"
             }), \
             patch.object(client, 'wait_for_authorization', return_value={
                 "status": "approved",
                 "session_token": "test_token_123"
             }):
            
            result = client.connect([Permission.WALLET_INFO])
            
            assert result is True
            assert client.session_token == "test_token_123"


class TestAsyncClient:
    """Test asynchronous client functionality."""
    
    @pytest.mark.unit
    def test_async_client_creation(self):
        """Test basic async client creation."""
        client = XianWalletClient("Test DApp")
        
        assert client.app_name == "Test DApp"
        assert client.server_url == "http://127.0.0.1:8545"
        assert client.session_token is None
    
    @pytest.mark.unit
    async def test_async_check_wallet_available(self):
        """Test async wallet availability check."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"available": True}
            mock_client.get.return_value = mock_response
            
            client = XianWalletClient("Test DApp")
            result = await client.check_wallet_available()
            
            assert result is True
    
    @pytest.mark.unit
    async def test_async_request_authorization(self):
        """Test async authorization request."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "request_id": "test_request_123",
                "status": "pending"
            }
            mock_client.post.return_value = mock_response
            
            client = XianWalletClient("Test DApp")
            result = await client.request_authorization([Permission.WALLET_INFO])
            
            assert result["request_id"] == "test_request_123"
    
    @pytest.mark.unit
    async def test_async_get_wallet_info(self):
        """Test async wallet info request."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "address": "test_address_123",
                "network": "https://testnet.xian.org"
            }
            mock_client.get.return_value = mock_response
            
            client = XianWalletClient("Test DApp")
            client.session_token = "test_token_123"
            
            result = await client.get_wallet_info()
            
            assert result["address"] == "test_address_123"
    
    @pytest.mark.unit
    async def test_async_connect_flow(self):
        """Test complete async connection flow."""
        client = XianWalletClient("Test DApp")
        
        with patch.object(client, 'check_wallet_available', return_value=True), \
             patch.object(client, 'request_authorization', return_value={
                 "request_id": "test_request_123",
                 "status": "pending"
             }), \
             patch.object(client, 'wait_for_authorization', return_value={
                 "status": "approved",
                 "session_token": "test_token_123"
             }):
            
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
    @patch('httpx.post')
    def test_authorization_denied(self, mock_post):
        """Test handling of authorization denial."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "request_id": "test_request_123",
            "status": "denied"
        }
        mock_post.return_value = mock_response
        
        client = XianWalletClientSync("Test DApp")
        
        with patch.object(client, 'wait_for_authorization', return_value={
            "status": "denied"
        }):
            result = client.connect([Permission.WALLET_INFO])
            assert result is False
    
    @pytest.mark.unit
    def test_invalid_permissions(self):
        """Test handling of invalid permissions."""
        client = XianWalletClientSync("Test DApp")
        
        with pytest.raises(ValueError):
            client.connect([])  # Empty permissions should be invalid
    
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
    def test_custom_timeout(self):
        """Test client with custom timeout."""
        client = XianWalletClientSync("Test DApp", timeout=30.0)
        
        assert client.timeout == 30.0
    
    @pytest.mark.unit
    def test_custom_headers(self):
        """Test client with custom headers."""
        custom_headers = {"User-Agent": "Test DApp/1.0"}
        client = XianWalletClientSync("Test DApp", headers=custom_headers)
        
        assert client.headers["User-Agent"] == "Test DApp/1.0"
    
    @pytest.mark.unit
    def test_client_with_all_options(self):
        """Test client creation with all options."""
        client = XianWalletClientSync(
            app_name="Test DApp",
            app_url="https://testdapp.com",
            wallet_url="http://localhost:8546",
            timeout=30.0,
            headers={"Custom-Header": "value"}
        )
        
        assert client.app_name == "Test DApp"
        assert client.app_url == "https://testdapp.com"
        assert client.base_url == "http://localhost:8546"
        assert client.timeout == 30.0
        assert client.headers["Custom-Header"] == "value"


class TestClientUtilities:
    """Test client utility functions."""
    
    @pytest.mark.unit
    def test_format_permissions(self):
        """Test permission formatting."""
        client = XianWalletClientSync("Test DApp")
        permissions = [Permission.WALLET_INFO, Permission.BALANCE]
        
        formatted = client._format_permissions(permissions)
        
        assert "wallet_info" in formatted
        assert "balance" in formatted
    
    @pytest.mark.unit
    def test_build_headers(self):
        """Test header building."""
        client = XianWalletClientSync("Test DApp")
        client.session_token = "test_token_123"
        
        headers = client._build_headers()
        
        assert headers["Authorization"] == "Bearer test_token_123"
        assert "Content-Type" in headers
    
    @pytest.mark.unit
    def test_build_headers_no_token(self):
        """Test header building without token."""
        client = XianWalletClientSync("Test DApp")
        # Don't set session_token
        
        headers = client._build_headers()
        
        assert "Authorization" not in headers
        assert "Content-Type" in headers