"""
Simple test for MAX_SESSIONS enforcement without async complications
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from xian_uwp.models import ProtocolConfig, ErrorCodes, AuthorizationRequest
from xian_uwp.server import WalletProtocolServer


def test_max_sessions_enforcement_simple():
    """Test that MAX_SESSIONS limit is enforced"""
    # Create a simple app for testing
    app = FastAPI()
    
    # Track pending requests
    pending_requests = {}
    
    @app.post("/api/v1/auth/request")
    async def auth_request(request: AuthorizationRequest):
        # Check MAX_SESSIONS limit
        if len(pending_requests) >= ProtocolConfig.MAX_SESSIONS:
            raise HTTPException(
                status_code=429,
                detail=ErrorCodes.MAX_SESSIONS_EXCEEDED
            )
        
        # Add request
        request_id = f"req_{len(pending_requests)}"
        pending_requests[request_id] = request
        
        return {
            "request_id": request_id,
            "status": "pending",
            "app_name": request.app_name
        }
    
    # Create test client
    client = TestClient(app)
    
    # Fill up to MAX_SESSIONS
    for i in range(ProtocolConfig.MAX_SESSIONS):
        response = client.post(
            "/api/v1/auth/request",
            json={
                "app_name": f"App {i}",
                "app_url": f"http://app{i}.com",
                "permissions": ["wallet_info"]
            }
        )
        assert response.status_code == 200
        assert response.json()["status"] == "pending"
    
    # Verify we have MAX_SESSIONS
    assert len(pending_requests) == ProtocolConfig.MAX_SESSIONS
    
    # Try one more - should fail
    response = client.post(
        "/api/v1/auth/request",
        json={
            "app_name": "Overflow App",
            "app_url": "http://overflow.com",
            "permissions": ["wallet_info"]
        }
    )
    
    assert response.status_code == 429
    assert response.json()["detail"] == ErrorCodes.MAX_SESSIONS_EXCEEDED


def test_max_sessions_with_actual_server():
    """Test MAX_SESSIONS with the actual server implementation"""
    # Create server
    server = WalletProtocolServer()
    
    # Mock the problematic parts
    server._broadcast_to_wallet = AsyncMock()
    
    # Patch asyncio.create_task to prevent background tasks
    with patch('xian_uwp.server.asyncio.create_task') as mock_create_task:
        mock_create_task.return_value = MagicMock()
        
        # Get the app
        app = server.app
        
        # Create test client
        client = TestClient(app)
        
        # Fill up to MAX_SESSIONS
        for i in range(ProtocolConfig.MAX_SESSIONS):
            response = client.post(
                "/api/v1/auth/request",
                json={
                    "app_name": f"App {i}",
                    "app_url": f"http://app{i}.com",
                    "permissions": ["wallet_info"]
                }
            )
            assert response.status_code == 200
        
        # Try one more - should fail
        response = client.post(
            "/api/v1/auth/request",
            json={
                "app_name": "Overflow App",
                "app_url": "http://overflow.com",
                "permissions": ["wallet_info"]
            }
        )
        
        assert response.status_code == 429
        assert response.json()["detail"] == ErrorCodes.MAX_SESSIONS_EXCEEDED


if __name__ == "__main__":
    test_max_sessions_enforcement_simple()
    print("Simple test passed!")
    
    test_max_sessions_with_actual_server()
    print("Server test passed!")