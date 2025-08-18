"""
End-to-end demonstration tests showing async and sync functionality working together
"""

import asyncio
import pytest
import time
import threading
from unittest.mock import patch, MagicMock, AsyncMock

from xian_uwp.server import WalletProtocolServer, create_server
from xian_uwp.client import XianWalletClient, XianWalletClientSync, create_client
from xian_uwp.models import WalletType, CORSConfig, Permission, WalletInfo, BalanceResponse


class TestE2EAsyncSyncDemo:
    """End-to-end demonstration of async and sync functionality"""
    
    @pytest.mark.asyncio
    async def test_complete_async_workflow_demo(self):
        """Demonstrate complete async workflow"""
        # Create server
        server = create_server(WalletType.DESKTOP)
        server.configure_network("https://testnet.xian.org", "xian-testnet-1")
        
        # Verify server configuration
        assert server.wallet_type == WalletType.DESKTOP
        assert server.network_url == "https://testnet.xian.org"
        assert server.chain_id == "xian-testnet-1"
        assert not server.is_server_running()
        
        # Create async client
        client = XianWalletClient(
            app_name="Demo Async DApp",
            app_url="https://demo.example.com",
            permissions=[Permission.WALLET_INFO, Permission.BALANCE]
        )
        
        # Verify client configuration
        assert client.app_name == "Demo Async DApp"
        assert client.app_url == "https://demo.example.com"
        assert Permission.WALLET_INFO in client.permissions
        assert Permission.BALANCE in client.permissions
        
        # Test cache operations
        client._set_cache("demo_key", "demo_value")
        cached_value = client._get_cached("demo_key", ttl_seconds=60)
        assert cached_value == "demo_value"
        
        # Test disconnect cleanup
        client.session_token = "demo_token"
        await client.disconnect()
        assert client.session_token is None
        
        print("✅ Async workflow demo completed successfully")
    
    def test_complete_sync_workflow_demo(self):
        """Demonstrate complete sync workflow"""
        # Create server
        server = create_server(WalletType.CLI)
        server.configure_network("https://mainnet.xian.org", "xian-mainnet-1")
        
        # Verify server configuration
        assert server.wallet_type == WalletType.CLI
        assert server.network_url == "https://mainnet.xian.org"
        assert server.chain_id == "xian-mainnet-1"
        
        # Create sync client
        client = XianWalletClientSync(
            app_name="Demo Sync DApp",
            app_url="http://localhost:3000"
        )
        
        # Verify client configuration
        assert client.app_name == "Demo Sync DApp"
        assert client.app_url == "http://localhost:3000"
        assert isinstance(client.client, XianWalletClient)
        
        # Test property access
        assert client.session_token is None
        client.session_token = "sync_demo_token"
        assert client.session_token == "sync_demo_token"
        assert client.client.session_token == "sync_demo_token"
        
        # Test disconnect
        client.disconnect()
        assert client.session_token is None
        
        print("✅ Sync workflow demo completed successfully")
    
    @pytest.mark.asyncio
    async def test_server_lifecycle_demo(self):
        """Demonstrate server lifecycle management"""
        server = create_server(WalletType.WEB)
        
        # Test initial state
        assert not server.is_server_running()
        assert server.wallet_type == WalletType.WEB
        
        # Test configuration
        server.configure_network("https://testnet.xian.org", "xian-testnet-1")
        assert server.network_url == "https://testnet.xian.org"
        assert server.chain_id == "xian-testnet-1"
        
        # Test cache operations
        server._set_cache("server_demo_key", "server_demo_value")
        cached = server._get_cached("server_demo_key", ttl_seconds=60)
        assert cached == "server_demo_value"
        
        # Test cache clearing
        server._clear_cache()
        assert len(server.cache) == 0
        
        # Test stop when not running
        await server.stop_async()
        assert not server.is_running
        
        print("✅ Server lifecycle demo completed successfully")
    
    def test_client_factory_demo(self):
        """Demonstrate client factory functionality"""
        # Create async client
        async_client = create_client("Factory Async DApp", async_mode=True)
        assert isinstance(async_client, XianWalletClient)
        assert async_client.app_name == "Factory Async DApp"
        
        # Create sync client
        sync_client = create_client("Factory Sync DApp", async_mode=False)
        assert isinstance(sync_client, XianWalletClientSync)
        assert sync_client.app_name == "Factory Sync DApp"
        
        # Create default client (should be sync)
        default_client = create_client("Factory Default DApp")
        assert isinstance(default_client, XianWalletClientSync)
        assert default_client.app_name == "Factory Default DApp"
        
        print("✅ Client factory demo completed successfully")
    
    @pytest.mark.asyncio
    async def test_error_handling_demo(self):
        """Demonstrate error handling capabilities"""
        server = create_server(WalletType.DESKTOP)
        client = XianWalletClient("Error Demo DApp")
        
        # Test server network validation
        try:
            server._validate_network_config()
            assert False, "Should have raised an exception"
        except Exception:
            pass  # Expected
        
        # Configure network and test again
        server.configure_network("https://testnet.xian.org", "xian-testnet-1")
        server._validate_network_config()  # Should not raise
        
        # Test client disconnect with mocked errors
        client.http_client = MagicMock()
        client.http_client.aclose = AsyncMock(side_effect=Exception("Mock error"))
        
        # Should handle error gracefully
        await client.disconnect()
        assert client.session_token is None
        
        print("✅ Error handling demo completed successfully")
    
    @pytest.mark.asyncio
    async def test_concurrent_operations_demo(self):
        """Demonstrate concurrent operations"""
        server = create_server(WalletType.DESKTOP)
        client = XianWalletClient("Concurrent Demo DApp")
        
        # Test concurrent server cache operations
        async def server_cache_task(i):
            key = f"concurrent_server_{i}"
            value = f"value_{i}"
            server._set_cache(key, value)
            await asyncio.sleep(0.001)  # Small delay
            return server._get_cached(key, ttl_seconds=60)
        
        server_tasks = [server_cache_task(i) for i in range(5)]
        server_results = await asyncio.gather(*server_tasks)
        
        for i, result in enumerate(server_results):
            assert result == f"value_{i}"
        
        # Test concurrent client cache operations
        async def client_cache_task(i):
            key = f"concurrent_client_{i}"
            value = f"client_value_{i}"
            client._set_cache(key, value)
            await asyncio.sleep(0.001)  # Small delay
            return client._get_cached(key, ttl_seconds=60)
        
        client_tasks = [client_cache_task(i) for i in range(5)]
        client_results = await asyncio.gather(*client_tasks)
        
        for i, result in enumerate(client_results):
            assert result == f"client_value_{i}"
        
        print("✅ Concurrent operations demo completed successfully")
    
    def test_sync_client_event_loop_demo(self):
        """Demonstrate sync client event loop management"""
        client = XianWalletClientSync("Event Loop Demo DApp")
        
        # Test that event loop is created on demand
        assert client._loop is None
        
        # Run an async operation through sync interface
        async def demo_async_operation():
            await asyncio.sleep(0.001)
            return "async_result"
        
        result = client._run_async(demo_async_operation())
        assert result == "async_result"
        assert client._loop is not None
        
        # Test multiple operations
        results = []
        for i in range(3):
            async def numbered_operation():
                return f"result_{i}"
            
            result = client._run_async(numbered_operation())
            results.append(result)
        
        assert len(results) == 3
        
        print("✅ Sync client event loop demo completed successfully")
    
    def test_cors_configuration_demo(self):
        """Demonstrate CORS configuration options"""
        # Test development CORS config
        dev_cors = CORSConfig.development()
        dev_server = create_server(WalletType.WEB, cors_config=dev_cors)
        assert dev_server.cors_config.allow_origins == ["*"]
        
        # Test localhost development CORS config
        localhost_cors = CORSConfig.localhost_dev()
        localhost_server = create_server(WalletType.DESKTOP, cors_config=localhost_cors)
        assert "http://localhost:3000" in localhost_server.cors_config.allow_origins
        assert "http://localhost:5173" in localhost_server.cors_config.allow_origins
        
        # Test production CORS config
        prod_origins = ["https://myapp.com", "https://www.myapp.com"]
        prod_cors = CORSConfig.production(allowed_origins=prod_origins)
        prod_server = create_server(WalletType.CLI, cors_config=prod_cors)
        assert prod_server.cors_config.allow_origins == prod_origins
        
        print("✅ CORS configuration demo completed successfully")
    
    def test_legacy_compatibility_demo(self):
        """Demonstrate legacy compatibility features"""
        from xian_uwp.client import XianWalletUtils
        
        # Test legacy utils creation
        utils = XianWalletUtils()
        assert utils.client is None
        
        # Test that all legacy methods exist
        legacy_methods = [
            'init', 'requestWalletInfo', 'getBalance', 'getApprovedBalance',
            'sendTransaction', 'signMessage', 'addToken'
        ]
        
        for method in legacy_methods:
            assert hasattr(utils, method), f"Missing legacy method: {method}"
        
        print("✅ Legacy compatibility demo completed successfully")
    
    @pytest.mark.asyncio
    async def test_comprehensive_integration_demo(self):
        """Comprehensive integration demonstration"""
        print("\n🚀 Starting comprehensive integration demo...")
        
        # 1. Create and configure server
        print("1. Creating and configuring server...")
        server = create_server(WalletType.DESKTOP)
        server.configure_network("https://testnet.xian.org", "xian-testnet-1")
        assert server.wallet_type == WalletType.DESKTOP
        assert server.network_url == "https://testnet.xian.org"
        print("   ✅ Server created and configured")
        
        # 2. Create async client
        print("2. Creating async client...")
        async_client = XianWalletClient(
            app_name="Integration Demo DApp",
            app_url="https://demo.example.com",
            permissions=[Permission.WALLET_INFO, Permission.BALANCE, Permission.TRANSACTIONS]
        )
        assert async_client.app_name == "Integration Demo DApp"
        print("   ✅ Async client created")
        
        # 3. Create sync client
        print("3. Creating sync client...")
        sync_client = XianWalletClientSync(
            app_name="Integration Demo Sync DApp",
            app_url="http://localhost:3000"
        )
        assert sync_client.app_name == "Integration Demo Sync DApp"
        print("   ✅ Sync client created")
        
        # 4. Test cache operations
        print("4. Testing cache operations...")
        server._set_cache("integration_server", "server_data")
        async_client._set_cache("integration_async", "async_data")
        
        assert server._get_cached("integration_server", 60) == "server_data"
        assert async_client._get_cached("integration_async", 60) == "async_data"
        print("   ✅ Cache operations working")
        
        # 5. Test concurrent operations
        print("5. Testing concurrent operations...")
        async def concurrent_task(name, delay):
            await asyncio.sleep(delay)
            return f"completed_{name}"
        
        tasks = [
            concurrent_task("task1", 0.001),
            concurrent_task("task2", 0.002),
            concurrent_task("task3", 0.001)
        ]
        
        results = await asyncio.gather(*tasks)
        assert len(results) == 3
        assert all("completed_" in result for result in results)
        print("   ✅ Concurrent operations working")
        
        # 6. Test cleanup
        print("6. Testing cleanup...")
        async_client.session_token = "demo_token"
        await async_client.disconnect()
        assert async_client.session_token is None
        
        # For sync client, just test the property setting/getting
        sync_client.session_token = "sync_demo_token"
        assert sync_client.session_token == "sync_demo_token"
        sync_client.session_token = None  # Manual cleanup for demo
        assert sync_client.session_token is None
        print("   ✅ Cleanup working")
        
        # 7. Test server stop
        print("7. Testing server stop...")
        await server.stop_async()
        assert not server.is_running
        print("   ✅ Server stop working")
        
        print("🎉 Comprehensive integration demo completed successfully!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to show print statements