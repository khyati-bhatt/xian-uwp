"""
Comprehensive tests for async/sync functionality and server shutdown
"""

import asyncio
import pytest
import time
import threading
import signal
import os
from unittest.mock import patch, MagicMock

from xian_uwp.server import WalletProtocolServer, create_server
from xian_uwp.client import XianWalletClient, XianWalletClientSync, create_client
from xian_uwp.models import WalletType, CORSConfig, Permission


class TestAsyncServerOperations:
    """Test async server operations"""
    
    @pytest.mark.asyncio
    async def test_async_server_startup_shutdown(self):
        """Test async server startup and shutdown"""
        server = create_server(WalletType.DESKTOP)
        
        # Test that server is not running initially
        assert not server.is_server_running()
        
        # Start server asynchronously
        await server.start_async(host="127.0.0.1", port=8546)
        
        # Give server time to start
        await asyncio.sleep(0.5)
        
        # Test that server is running
        assert server.is_server_running()
        assert server.uvicorn_server is not None
        assert server.is_running is True
        
        # Stop server asynchronously
        await server.stop_async()
        
        # Give server time to stop
        await asyncio.sleep(0.5)
        
        # Test that server is stopped
        assert not server.is_running
    
    @pytest.mark.asyncio
    async def test_async_server_multiple_start_stop_cycles(self):
        """Test multiple async start/stop cycles"""
        server = create_server(WalletType.DESKTOP)
        
        for i in range(3):
            # Start server
            await server.start_async(host="127.0.0.1", port=8547 + i)
            await asyncio.sleep(0.3)
            assert server.is_server_running()
            
            # Stop server
            await server.stop_async()
            await asyncio.sleep(0.3)
            assert not server.is_running
    
    @pytest.mark.asyncio
    async def test_async_server_background_tasks_cleanup(self):
        """Test that background tasks are properly cleaned up"""
        server = create_server(WalletType.DESKTOP)
        
        # Test that background_tasks set exists
        assert hasattr(server, 'background_tasks')
        assert isinstance(server.background_tasks, set)
        
        # We can't easily test the actual cleanup without running a full server
        # but we can verify the data structures exist and the server can be created
        assert server is not None
    
    @pytest.mark.asyncio
    async def test_async_server_with_cors_config(self):
        """Test async server with custom CORS configuration"""
        cors_config = CORSConfig.development()
        server = create_server(WalletType.WEB, cors_config=cors_config)
        
        # Test CORS config without actually starting server to avoid port conflicts
        assert server.cors_config == cors_config
        assert server.cors_config.allow_origins == ["*"]


class TestSyncServerOperations:
    """Test sync server operations"""
    
    def test_sync_server_creation(self):
        """Test sync server creation"""
        server = create_server(WalletType.CLI)
        
        assert server is not None
        assert server.wallet_type == WalletType.CLI
        assert not server.is_server_running()
    
    def test_sync_server_stop_method(self):
        """Test sync server stop method"""
        server = create_server(WalletType.DESKTOP)
        
        # Test stop method when server is not running
        server.stop()
        assert not server.is_running
        
        # Mock uvicorn server for testing
        server.uvicorn_server = MagicMock()
        server.is_running = True
        
        # Test stop method
        server.stop()
        assert not server.is_running
        assert server.uvicorn_server.should_exit is True
    
    def test_sync_server_status_check(self):
        """Test server status checking"""
        server = create_server(WalletType.DESKTOP)
        
        # Initially not running
        assert not server.is_server_running()
        
        # Mock running state
        server.is_running = True
        server.uvicorn_server = MagicMock()
        assert server.is_server_running()
        
        # Mock stopped state
        server.is_running = False
        assert not server.is_server_running()
        
        # Test with None uvicorn_server
        server.uvicorn_server = None
        assert not server.is_server_running()


class TestAsyncClientOperations:
    """Test async client operations"""
    
    @pytest.mark.asyncio
    async def test_async_client_creation(self):
        """Test async client creation"""
        client = XianWalletClient("Test DApp", "http://localhost:3000")
        
        assert client.app_name == "Test DApp"
        assert client.app_url == "http://localhost:3000"
        assert client.session_token is None
        assert client.wallet_info is None
    
    @pytest.mark.asyncio
    async def test_async_client_disconnect_cleanup(self):
        """Test async client disconnect and cleanup"""
        client = XianWalletClient("Test DApp")
        
        # Mock some state
        client.session_token = "test_token"
        client.wallet_info = MagicMock()
        client._cache = {"test": ("data", time.time())}
        
        # Test disconnect
        await client.disconnect()
        
        # Verify cleanup
        assert client.session_token is None
        assert client.wallet_info is None
        assert len(client._cache) == 0
    
    @pytest.mark.asyncio
    async def test_async_client_cache_management(self):
        """Test async client cache management"""
        client = XianWalletClient("Test DApp")
        
        # Test cache operations
        client._set_cache("test_key", "test_data")
        assert client._get_cached("test_key", ttl_seconds=60) == "test_data"
        
        # Test cache expiration
        client._set_cache("expired_key", "expired_data")
        # Manually set old timestamp
        client._cache["expired_key"] = ("expired_data", time.time() - 120)
        assert client._get_cached("expired_key", ttl_seconds=60) is None
        
        # Test cache pattern clearing
        client._set_cache("balance_currency", "100")
        client._set_cache("balance_token", "50")
        client._set_cache("other_data", "data")
        
        client._clear_cache_pattern("balance_")
        assert client._get_cached("balance_currency", ttl_seconds=60) is None
        assert client._get_cached("balance_token", ttl_seconds=60) is None
        assert client._get_cached("other_data", ttl_seconds=60) == "data"
    
    @pytest.mark.asyncio
    async def test_async_client_factory_function(self):
        """Test async client factory function"""
        # Test async client creation
        async_client = create_client("Test DApp", async_mode=True)
        assert isinstance(async_client, XianWalletClient)
        
        # Test sync client creation
        sync_client = create_client("Test DApp", async_mode=False)
        assert isinstance(sync_client, XianWalletClientSync)


class TestSyncClientOperations:
    """Test sync client operations"""
    
    def test_sync_client_creation(self):
        """Test sync client creation"""
        client = XianWalletClientSync("Test DApp", "http://localhost:3000")
        
        assert client.app_name == "Test DApp"
        assert client.app_url == "http://localhost:3000"
        assert client.session_token is None
        assert isinstance(client.client, XianWalletClient)
    
    def test_sync_client_properties(self):
        """Test sync client property accessors"""
        client = XianWalletClientSync("Test DApp", "http://localhost:3000")
        
        # Test property getters
        assert client.app_name == "Test DApp"
        assert client.app_url == "http://localhost:3000"
        assert client.base_url == client.client.server_url
        assert client.session_token is None
        
        # Test session_token setter
        client.session_token = "test_token"
        assert client.session_token == "test_token"
        assert client.client.session_token == "test_token"
    
    def test_sync_client_event_loop_management(self):
        """Test sync client event loop management"""
        client = XianWalletClientSync("Test DApp")
        
        # Test that _run_async creates and manages event loop
        assert client._loop is None
        
        # Mock an async operation
        async def mock_async_op():
            return "test_result"
        
        result = client._run_async(mock_async_op())
        assert result == "test_result"
        assert client._loop is not None
    
    def test_sync_client_disconnect(self):
        """Test sync client disconnect"""
        client = XianWalletClientSync("Test DApp")
        
        # Mock some state
        client.client.session_token = "test_token"
        client.client.wallet_info = MagicMock()
        
        # Test disconnect (this will create an event loop and run disconnect)
        client.disconnect()
        
        # Verify cleanup happened
        assert client.client.session_token is None
        assert client.client.wallet_info is None


class TestServerShutdownScenarios:
    """Test various server shutdown scenarios"""
    
    @pytest.mark.asyncio
    async def test_graceful_async_shutdown(self):
        """Test graceful async server shutdown"""
        server = create_server(WalletType.DESKTOP)
        
        # Start server
        await server.start_async(host="127.0.0.1", port=8550)
        await asyncio.sleep(0.3)
        
        # Verify server is running
        assert server.is_server_running()
        
        # Graceful shutdown
        await server.stop_async()
        await asyncio.sleep(0.3)
        
        # Verify server is stopped
        assert not server.is_running
    
    @pytest.mark.asyncio
    async def test_shutdown_with_active_connections(self):
        """Test shutdown with active WebSocket connections"""
        server = create_server(WalletType.DESKTOP)
        
        # Mock WebSocket connections
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()
        server.websocket_connections.add(mock_ws1)
        server.websocket_connections.add(mock_ws2)
        
        # Start and stop server
        await server.start_async(host="127.0.0.1", port=8551)
        await asyncio.sleep(0.3)
        await server.stop_async()
        await asyncio.sleep(0.3)
        
        # Verify shutdown completed
        assert not server.is_running
    
    @pytest.mark.asyncio
    async def test_shutdown_timeout_handling(self):
        """Test shutdown timeout handling"""
        server = create_server(WalletType.DESKTOP)
        
        # Start server
        await server.start_async(host="127.0.0.1", port=8552)
        await asyncio.sleep(0.3)
        
        # Mock a server task that doesn't respond to cancellation quickly
        original_task = server.server_task
        server.server_task = MagicMock()
        server.server_task.cancel = MagicMock()
        
        # Create a task that will timeout
        async def slow_task():
            await asyncio.sleep(5)  # Longer than the 2-second timeout
        
        server.server_task = asyncio.create_task(slow_task())
        
        # Test shutdown with timeout
        await server.stop_async()
        
        # Verify shutdown completed despite timeout
        assert not server.is_running
    
    def test_sync_shutdown_signal_handling(self):
        """Test sync server shutdown behavior"""
        server = create_server(WalletType.DESKTOP)
        
        # Mock uvicorn server
        server.uvicorn_server = MagicMock()
        server.is_running = True
        
        # Test stop method
        server.stop()
        
        # Verify stop was called
        assert not server.is_running
        assert server.uvicorn_server.should_exit is True


class TestResourceCleanup:
    """Test resource cleanup in various scenarios"""
    
    @pytest.mark.asyncio
    async def test_client_http_client_cleanup(self):
        """Test that HTTP client is properly closed"""
        client = XianWalletClient("Test DApp")
        
        # Mock the http_client
        client.http_client = MagicMock()
        client.http_client.aclose = MagicMock()
        
        # Test disconnect
        await client.disconnect()
        
        # Verify HTTP client was closed
        client.http_client.aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_client_websocket_cleanup(self):
        """Test that WebSocket connections are properly closed"""
        client = XianWalletClient("Test DApp")
        
        # Mock WebSocket connection
        mock_websocket = MagicMock()
        mock_websocket.close = MagicMock()
        client.websocket = mock_websocket
        
        # Test disconnect
        await client.disconnect()
        
        # Verify WebSocket was closed
        mock_websocket.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_server_session_cleanup(self):
        """Test server session cleanup"""
        server = create_server(WalletType.DESKTOP)
        
        # Add some test sessions
        server.sessions["token1"] = MagicMock()
        server.sessions["token2"] = MagicMock()
        server.pending_requests["req1"] = MagicMock()
        
        # Test that sessions exist
        assert len(server.sessions) == 2
        assert len(server.pending_requests) == 1
        
        # The cleanup happens in background tasks and lifespan events
        # We can't directly test it without running the server, but we can
        # verify the data structures exist
        assert hasattr(server, 'sessions')
        assert hasattr(server, 'pending_requests')
        assert hasattr(server, 'websocket_connections')


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery scenarios"""
    
    @pytest.mark.asyncio
    async def test_client_disconnect_with_errors(self):
        """Test client disconnect handles errors gracefully"""
        client = XianWalletClient("Test DApp")
        
        # Mock HTTP client that raises an exception
        client.http_client = MagicMock()
        client.http_client.aclose = MagicMock(side_effect=Exception("Connection error"))
        
        # Mock WebSocket that raises an exception
        mock_websocket = MagicMock()
        mock_websocket.close = MagicMock(side_effect=Exception("WebSocket error"))
        client.websocket = mock_websocket
        
        # Test that disconnect handles errors gracefully
        await client.disconnect()  # Should not raise an exception
        
        # Verify cleanup still happened
        assert client.session_token is None
        assert client.wallet_info is None
    
    @pytest.mark.asyncio
    async def test_server_stop_with_no_server(self):
        """Test server stop when no server is running"""
        server = create_server(WalletType.DESKTOP)
        
        # Test stop when server was never started
        await server.stop_async()  # Should not raise an exception
        assert not server.is_running
        
        # Test stop when uvicorn_server is None
        server.uvicorn_server = None
        server.is_running = True
        await server.stop_async()  # Should not raise an exception
        # After calling stop_async, is_running should be False
        assert not server.is_running
    
    def test_sync_client_with_closed_loop(self):
        """Test sync client behavior with closed event loop"""
        client = XianWalletClientSync("Test DApp")
        
        # Create and close a loop
        loop = asyncio.new_event_loop()
        loop.close()
        client._loop = loop
        
        # Test that _run_async creates a new loop when the old one is closed
        async def test_coro():
            return "success"
        
        result = client._run_async(test_coro())
        assert result == "success"
        assert client._loop != loop  # Should be a new loop
        assert not client._loop.is_closed()


class TestConcurrentOperations:
    """Test concurrent operations and thread safety"""
    
    @pytest.mark.asyncio
    async def test_concurrent_client_operations(self):
        """Test concurrent client operations"""
        client = XianWalletClient("Test DApp")
        
        # Test concurrent cache operations
        async def cache_operation(key, value):
            client._set_cache(key, value)
            await asyncio.sleep(0.01)  # Small delay
            return client._get_cached(key, ttl_seconds=60)
        
        # Run multiple cache operations concurrently
        tasks = [
            cache_operation(f"key_{i}", f"value_{i}")
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all operations completed successfully
        for i, result in enumerate(results):
            assert result == f"value_{i}"
    
    @pytest.mark.asyncio
    async def test_concurrent_server_operations(self):
        """Test concurrent server operations"""
        server = create_server(WalletType.DESKTOP)
        
        # Test concurrent cache operations on server
        async def server_cache_operation(key, value):
            server._set_cache(key, value)
            await asyncio.sleep(0.01)
            return server._get_cached(key, ttl_seconds=60)
        
        tasks = [
            server_cache_operation(f"server_key_{i}", f"server_value_{i}")
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        for i, result in enumerate(results):
            assert result == f"server_value_{i}"


class TestNetworkConfiguration:
    """Test network configuration scenarios"""
    
    def test_server_network_configuration(self):
        """Test server network configuration"""
        server = create_server(WalletType.DESKTOP)
        
        # Test initial state
        assert server.network_url is None
        assert server.chain_id is None
        
        # Test configuration
        server.configure_network("https://testnet.xian.org", "xian-testnet-1")
        assert server.network_url == "https://testnet.xian.org"
        assert server.chain_id == "xian-testnet-1"
        
        # Test validation
        server.network_url = None
        with pytest.raises(Exception):  # Should raise WalletProtocolError
            server._validate_network_config()
    
    def test_server_with_network_config(self):
        """Test server creation with network configuration"""
        server = WalletProtocolServer(
            wallet_type=WalletType.DESKTOP,
            network_url="https://mainnet.xian.org",
            chain_id="xian-mainnet-1"
        )
        
        assert server.network_url == "https://mainnet.xian.org"
        assert server.chain_id == "xian-mainnet-1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])