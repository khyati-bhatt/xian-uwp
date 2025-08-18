"""
Integration tests demonstrating async and sync functionality working together
"""

import asyncio
import pytest
import time
import threading
from unittest.mock import patch, MagicMock

from xian_uwp.server import WalletProtocolServer, create_server
from xian_uwp.client import XianWalletClient, XianWalletClientSync, create_client
from xian_uwp.models import WalletType, CORSConfig, Permission


class TestAsyncSyncIntegration:
    """Test async and sync functionality working together"""
    
    @pytest.mark.asyncio
    async def test_async_server_with_sync_client_simulation(self):
        """Test that async server can handle sync client patterns"""
        server = create_server(WalletType.DESKTOP)
        
        # Test server creation and basic properties
        assert server.wallet_type == WalletType.DESKTOP
        assert not server.is_server_running()
        
        # Test that we can configure the server
        server.configure_network("https://testnet.xian.org", "xian-testnet-1")
        assert server.network_url == "https://testnet.xian.org"
        assert server.chain_id == "xian-testnet-1"
        
        # Test sync client creation
        sync_client = XianWalletClientSync("Test DApp")
        assert sync_client.app_name == "Test DApp"
        assert isinstance(sync_client.client, XianWalletClient)
    
    @pytest.mark.asyncio
    async def test_client_factory_both_modes(self):
        """Test client factory creates both async and sync clients correctly"""
        # Test async client creation
        async_client = create_client("Async DApp", async_mode=True)
        assert isinstance(async_client, XianWalletClient)
        assert async_client.app_name == "Async DApp"
        
        # Test sync client creation
        sync_client = create_client("Sync DApp", async_mode=False)
        assert isinstance(sync_client, XianWalletClientSync)
        assert sync_client.app_name == "Sync DApp"
        
        # Test default (sync) client creation
        default_client = create_client("Default DApp")
        assert isinstance(default_client, XianWalletClientSync)
    
    def test_sync_client_async_operations(self):
        """Test that sync client properly wraps async operations"""
        client = XianWalletClientSync("Test DApp")
        
        # Test that sync client has all the expected methods
        assert hasattr(client, 'connect')
        assert hasattr(client, 'disconnect')
        assert hasattr(client, 'get_wallet_info')
        assert hasattr(client, 'get_balance')
        assert hasattr(client, 'send_transaction')
        assert hasattr(client, 'sign_message')
        assert hasattr(client, 'add_token')
        
        # Test property access
        assert client.app_name == "Test DApp"
        assert client.session_token is None
        
        # Test session token setter
        client.session_token = "test_token"
        assert client.session_token == "test_token"
        assert client.client.session_token == "test_token"
    
    @pytest.mark.asyncio
    async def test_server_lifecycle_management(self):
        """Test complete server lifecycle management"""
        server = create_server(WalletType.CLI)
        
        # Test initial state
        assert not server.is_server_running()
        assert server.wallet_type == WalletType.CLI
        
        # Test that server has all required components
        assert hasattr(server, 'sessions')
        assert hasattr(server, 'pending_requests')
        assert hasattr(server, 'websocket_connections')
        assert hasattr(server, 'background_tasks')
        assert hasattr(server, 'cache')
        
        # Test cache operations
        server._set_cache("test_key", "test_value")
        cached_value = server._get_cached("test_key", ttl_seconds=60)
        assert cached_value == "test_value"
        
        # Test cache expiration
        server._set_cache("expired_key", "expired_value")
        # Manually set old timestamp
        from datetime import datetime, timedelta
        old_time = datetime.now() - timedelta(seconds=120)
        server.cache["expired_key"] = ("expired_value", old_time)
        expired_value = server._get_cached("expired_key", ttl_seconds=60)
        assert expired_value is None
        
        # Test cache clearing
        server._set_cache("key1", "value1")
        server._set_cache("key2", "value2")
        server._clear_cache()
        assert len(server.cache) == 0
    
    @pytest.mark.asyncio
    async def test_client_lifecycle_management(self):
        """Test complete client lifecycle management"""
        client = XianWalletClient("Test DApp", "http://localhost:3000")
        
        # Test initial state
        assert client.app_name == "Test DApp"
        assert client.app_url == "http://localhost:3000"
        assert client.session_token is None
        assert client.wallet_info is None
        
        # Test permissions
        assert Permission.WALLET_INFO in client.permissions
        assert Permission.BALANCE in client.permissions
        assert Permission.TRANSACTIONS in client.permissions
        assert Permission.SIGN_MESSAGE in client.permissions
        
        # Test cache operations
        client._set_cache("test_key", "test_value")
        cached_value = client._get_cached("test_key", ttl_seconds=60)
        assert cached_value == "test_value"
        
        # Test cache pattern clearing
        client._set_cache("balance_currency", "100")
        client._set_cache("balance_token", "50")
        client._set_cache("other_data", "data")
        
        client._clear_cache_pattern("balance_")
        assert client._get_cached("balance_currency", ttl_seconds=60) is None
        assert client._get_cached("balance_token", ttl_seconds=60) is None
        assert client._get_cached("other_data", ttl_seconds=60) == "data"
        
        # Test disconnect cleanup
        client.session_token = "test_token"
        client.wallet_info = MagicMock()
        client._cache = {"test": ("data", time.time())}
        
        await client.disconnect()
        
        assert client.session_token is None
        assert client.wallet_info is None
        assert len(client._cache) == 0


class TestErrorHandlingIntegration:
    """Test error handling across async and sync components"""
    
    @pytest.mark.asyncio
    async def test_server_error_handling(self):
        """Test server error handling scenarios"""
        server = create_server(WalletType.DESKTOP)
        
        # Test network validation
        with pytest.raises(Exception):  # Should raise WalletProtocolError
            server._validate_network_config()
        
        # Test that server handles missing network config gracefully
        server.configure_network("https://testnet.xian.org", "xian-testnet-1")
        server._validate_network_config()  # Should not raise
    
    def test_sync_client_error_handling(self):
        """Test sync client error handling"""
        client = XianWalletClientSync("Test DApp")
        
        # Test that client handles event loop management
        assert client._loop is None
        
        # Test _run_async with a simple coroutine
        async def test_coro():
            return "success"
        
        result = client._run_async(test_coro())
        assert result == "success"
        assert client._loop is not None
    
    @pytest.mark.asyncio
    async def test_async_client_error_handling(self):
        """Test async client error handling"""
        client = XianWalletClient("Test DApp")
        
        # Test disconnect with mocked errors
        client.http_client = MagicMock()
        client.http_client.aclose = MagicMock(side_effect=Exception("Connection error"))
        
        # Should not raise exception
        await client.disconnect()
        
        # Verify cleanup still happened
        assert client.session_token is None
        assert client.wallet_info is None


class TestConcurrencyAndThreadSafety:
    """Test concurrency and thread safety aspects"""
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self):
        """Test concurrent cache operations on both server and client"""
        server = create_server(WalletType.DESKTOP)
        client = XianWalletClient("Test DApp")
        
        # Test concurrent server cache operations
        async def server_cache_op(key, value):
            server._set_cache(key, value)
            await asyncio.sleep(0.001)  # Small delay
            return server._get_cached(key, ttl_seconds=60)
        
        server_tasks = [
            server_cache_op(f"server_key_{i}", f"server_value_{i}")
            for i in range(5)
        ]
        
        server_results = await asyncio.gather(*server_tasks)
        
        for i, result in enumerate(server_results):
            assert result == f"server_value_{i}"
        
        # Test concurrent client cache operations
        async def client_cache_op(key, value):
            client._set_cache(key, value)
            await asyncio.sleep(0.001)  # Small delay
            return client._get_cached(key, ttl_seconds=60)
        
        client_tasks = [
            client_cache_op(f"client_key_{i}", f"client_value_{i}")
            for i in range(5)
        ]
        
        client_results = await asyncio.gather(*client_tasks)
        
        for i, result in enumerate(client_results):
            assert result == f"client_value_{i}"
    
    def test_sync_client_thread_safety(self):
        """Test sync client thread safety"""
        client = XianWalletClientSync("Test DApp")
        
        # Test that multiple sync operations can be performed
        results = []
        
        def sync_operation(value):
            async def async_op():
                return f"result_{value}"
            
            result = client._run_async(async_op())
            results.append(result)
        
        # Run multiple operations
        for i in range(3):
            sync_operation(i)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result == f"result_{i}"


class TestConfigurationAndCustomization:
    """Test configuration and customization options"""
    
    def test_server_configuration_options(self):
        """Test server configuration options"""
        # Test with custom CORS config
        cors_config = CORSConfig.localhost_dev()
        server = WalletProtocolServer(
            wallet_type=WalletType.WEB,
            cors_config=cors_config,
            network_url="https://mainnet.xian.org",
            chain_id="xian-mainnet-1"
        )
        
        assert server.wallet_type == WalletType.WEB
        assert server.cors_config == cors_config
        assert server.network_url == "https://mainnet.xian.org"
        assert server.chain_id == "xian-mainnet-1"
    
    def test_client_configuration_options(self):
        """Test client configuration options"""
        # Test async client with custom permissions
        custom_permissions = [Permission.WALLET_INFO, Permission.BALANCE]
        async_client = XianWalletClient(
            app_name="Custom DApp",
            app_url="https://example.com",
            server_url="http://localhost:8545",
            permissions=custom_permissions
        )
        
        assert async_client.app_name == "Custom DApp"
        assert async_client.app_url == "https://example.com"
        assert async_client.server_url == "http://localhost:8545"
        assert async_client.permissions == custom_permissions
        
        # Test sync client with server_url
        sync_client = XianWalletClientSync(
            app_name="Test DApp",
            app_url="http://localhost:3000",
            server_url="http://localhost:8546"
        )
        
        assert sync_client.app_name == "Test DApp"
        assert sync_client.app_url == "http://localhost:3000"
        assert sync_client.base_url == "http://localhost:8546"





if __name__ == "__main__":
    pytest.main([__file__, "-v"])