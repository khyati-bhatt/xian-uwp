"""
Shared test configuration and fixtures for Xian UWP test suite.

This module provides common fixtures, utilities, and configuration
for all tests in the suite.
"""

import asyncio
import pytest
import threading
import time
from typing import AsyncGenerator, Generator
from unittest.mock import Mock

import httpx
import uvicorn
from fastapi.testclient import TestClient

from xian_uwp import create_server, CORSConfig
from xian_uwp.models import WalletType, Permission, AuthorizationRequest
from xian_uwp.server import WalletProtocolServer


class MockWallet:
    """Mock wallet implementation for testing."""
    
    def __init__(self):
        self.locked = False
        self.balance = {"currency": 1000.0}
        self.address = "test_address_123"
        self.network = "https://testnet.xian.org"
        self.chain_id = "xian-testnet"
    
    def is_locked(self) -> bool:
        return self.locked
    
    def unlock(self, password: str) -> bool:
        if password == "correct_password":
            self.locked = False
            return True
        return False
    
    def lock(self):
        self.locked = True
    
    def get_address(self) -> str:
        return self.address
    
    def get_balance(self, currency: str) -> float:
        return self.balance.get(currency, 0.0)
    
    def sign_transaction(self, tx_data: dict) -> dict:
        return {
            "signature": "mock_signature_123",
            "transaction": tx_data
        }


class TestServer:
    """Managed test server for integration tests."""
    
    def __init__(self, cors_config: CORSConfig = None, port: int = 0):
        self.cors_config = cors_config or CORSConfig.development()
        self.port = port
        self.server = None
        self.server_thread = None
        self.base_url = None
        self.wallet = MockWallet()
    
    async def start(self) -> str:
        """Start the test server and return base URL."""
        # Find available port if not specified
        if self.port == 0:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', 0))
                self.port = s.getsockname()[1]
        
        # Create server
        self.server = create_server(
            wallet_type=WalletType.DESKTOP,
            cors_config=self.cors_config
        )
        self.server.wallet = self.wallet
        
        # Start server in thread
        def run_server():
            uvicorn.run(
                self.server.app,
                host="127.0.0.1",
                port=self.port,
                log_level="error"  # Reduce noise in tests
            )
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # Wait for server to start
        self.base_url = f"http://127.0.0.1:{self.port}"
        await self._wait_for_server()
        
        return self.base_url
    
    async def stop(self):
        """Stop the test server."""
        if self.server_thread:
            # Server will stop when thread ends (daemon thread)
            pass
    
    async def _wait_for_server(self, timeout: float = 5.0):
        """Wait for server to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.base_url}/api/v1/wallet/status")
                    if response.status_code == 200:
                        return
            except:
                pass
            await asyncio.sleep(0.1)
        
        raise RuntimeError(f"Test server failed to start within {timeout}s")
    
    async def get(self, path: str, **kwargs) -> httpx.Response:
        """Make GET request to test server."""
        async with httpx.AsyncClient() as client:
            return await client.get(f"{self.base_url}{path}", **kwargs)
    
    async def post(self, path: str, **kwargs) -> httpx.Response:
        """Make POST request to test server."""
        async with httpx.AsyncClient() as client:
            return await client.post(f"{self.base_url}{path}", **kwargs)
    
    async def options(self, path: str, **kwargs) -> httpx.Response:
        """Make OPTIONS request to test server."""
        async with httpx.AsyncClient() as client:
            return await client.options(f"{self.base_url}{path}", **kwargs)


@pytest.fixture
def mock_wallet() -> MockWallet:
    """Provide a mock wallet for testing."""
    return MockWallet()


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """Provide a FastAPI test client."""
    server = create_server(
        wallet_type=WalletType.DESKTOP,
        cors_config=CORSConfig.development()
    )
    server.wallet = MockWallet()
    
    with TestClient(server.app) as client:
        yield client


@pytest.fixture
async def test_server() -> AsyncGenerator[TestServer, None]:
    """Provide a managed test server for integration tests."""
    server = TestServer()
    await server.start()
    yield server
    await server.stop()


@pytest.fixture
async def cors_test_server() -> AsyncGenerator[TestServer, None]:
    """Provide a test server with production CORS configuration."""
    cors_config = CORSConfig.production([
        "https://mydapp.com",
        "https://app.mydapp.com",
        "http://localhost:3000"
    ])
    server = TestServer(cors_config=cors_config)
    await server.start()
    yield server
    await server.stop()


@pytest.fixture
def sample_auth_request() -> AuthorizationRequest:
    """Provide a sample authentication request."""
    return AuthorizationRequest(
        app_name="Test DApp",
        app_url="https://testdapp.com",
        permissions=[Permission.WALLET_INFO, Permission.BALANCE]
    )


@pytest.fixture
def cors_origins() -> list[str]:
    """Provide sample CORS origins for testing."""
    return [
        "https://mydapp.com",
        "https://app.mydapp.com",
        "http://localhost:3000",
        "http://localhost:5173"
    ]


# Test utilities
def assert_cors_headers(response: httpx.Response, expected_origin: str):
    """Assert that response has correct CORS headers."""
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == expected_origin
    assert response.headers.get("access-control-allow-credentials") == "true"


def assert_json_response(response: httpx.Response, expected_status: int = 200):
    """Assert that response is valid JSON with expected status."""
    assert response.status_code == expected_status
    assert response.headers["content-type"].startswith("application/json")
    return response.json()


# Async test utilities
async def wait_for_condition(condition_func, timeout: float = 5.0, interval: float = 0.1):
    """Wait for a condition to become true."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        await asyncio.sleep(interval)
    return False


# Mock factories
def create_mock_server() -> Mock:
    """Create a mock server for unit tests."""
    mock_server = Mock(spec=WalletProtocolServer)
    mock_server.wallet = MockWallet()
    mock_server.cors_config = CORSConfig.development()
    return mock_server


def create_mock_client() -> Mock:
    """Create a mock client for unit tests."""
    mock_client = Mock()
    mock_client.connect.return_value = True
    mock_client.get_wallet_info.return_value = {
        "address": "test_address_123",
        "network": "https://testnet.xian.org"
    }
    return mock_client