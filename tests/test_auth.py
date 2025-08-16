"""
Integration tests for authentication and authorization functionality.

Tests cover the complete auth flow from request to approval/denial,
session management, and permission validation.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from xian_uwp import create_server, CORSConfig
from xian_uwp.models import WalletType, Permission, AuthStatus


class TestAuthenticationFlow:
    """Test authentication request and approval flow."""
    
    @pytest.mark.integration
    def test_auth_request_creation(self, test_client):
        """Test creating an authentication request."""
        auth_data = {
            "app_name": "Test DApp",
            "app_url": "https://testdapp.com",
            "permissions": ["wallet_info", "balance"]
        }
        
        response = test_client.post("/api/v1/auth/request", json=auth_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert data["status"] == "pending"
    
    @pytest.mark.integration
    def test_auth_request_with_description(self, test_client):
        """Test auth request with optional description."""
        auth_data = {
            "app_name": "Test DApp",
            "app_url": "https://testdapp.com",
            "permissions": ["wallet_info"],
            "description": "This is a test DApp for demonstration purposes."
        }
        
        response = test_client.post("/api/v1/auth/request", json=auth_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert data["status"] == "pending"
    
    @pytest.mark.integration
    def test_auth_request_with_icon(self, test_client):
        """Test auth request with optional icon URL."""
        auth_data = {
            "app_name": "Test DApp",
            "app_url": "https://testdapp.com",
            "permissions": ["wallet_info"],
            "icon_url": "https://testdapp.com/icon.png"
        }
        
        response = test_client.post("/api/v1/auth/request", json=auth_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert data["status"] == "pending"
    
    @pytest.mark.integration
    def test_auth_request_all_permissions(self, test_client):
        """Test auth request with all available permissions."""
        auth_data = {
            "app_name": "Full Access DApp",
            "app_url": "https://fulldapp.com",
            "permissions": ["wallet_info", "balance", "transactions", "sign_message"]
        }
        
        response = test_client.post("/api/v1/auth/request", json=auth_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert data["status"] == "pending"


class TestAuthenticationValidation:
    """Test authentication request validation."""
    
    @pytest.mark.integration
    def test_auth_request_empty_app_name(self, test_client):
        """Test auth request with empty app name."""
        auth_data = {
            "app_name": "",
            "app_url": "https://testdapp.com",
            "permissions": ["wallet_info"]
        }
        
        response = test_client.post("/api/v1/auth/request", json=auth_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.integration
    def test_auth_request_invalid_url(self, test_client):
        """Test auth request with invalid URL."""
        auth_data = {
            "app_name": "Test DApp",
            "app_url": "not-a-valid-url",
            "permissions": ["wallet_info"]
        }
        
        response = test_client.post("/api/v1/auth/request", json=auth_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.integration
    def test_auth_request_empty_permissions(self, test_client):
        """Test auth request with empty permissions."""
        auth_data = {
            "app_name": "Test DApp",
            "app_url": "https://testdapp.com",
            "permissions": []
        }
        
        response = test_client.post("/api/v1/auth/request", json=auth_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.integration
    def test_auth_request_invalid_permission(self, test_client):
        """Test auth request with invalid permission."""
        auth_data = {
            "app_name": "Test DApp",
            "app_url": "https://testdapp.com",
            "permissions": ["invalid_permission"]
        }
        
        response = test_client.post("/api/v1/auth/request", json=auth_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.integration
    def test_auth_request_duplicate_permissions(self, test_client):
        """Test auth request with duplicate permissions."""
        auth_data = {
            "app_name": "Test DApp",
            "app_url": "https://testdapp.com",
            "permissions": ["wallet_info", "wallet_info", "balance"]
        }
        
        response = test_client.post("/api/v1/auth/request", json=auth_data)
        
        # Should succeed but deduplicate permissions
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert data["status"] == "pending"
        
        # Check the status endpoint to verify deduplication
        request_id = data["request_id"]
        status_response = test_client.get(f"/api/v1/auth/status/{request_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        # Should have unique permissions only
        assert len(status_data["permissions"]) == 2
        assert "wallet_info" in status_data["permissions"]
        assert "balance" in status_data["permissions"]


class TestAuthorizationManagement:
    """Test authorization approval and denial."""
    
    @pytest.mark.integration
    def test_auth_status_check(self, test_client):
        """Test checking authorization status."""
        # First create an auth request
        auth_data = {
            "app_name": "Test DApp",
            "app_url": "https://testdapp.com",
            "permissions": ["wallet_info"]
        }
        
        response = test_client.post("/api/v1/auth/request", json=auth_data)
        assert response.status_code == 200
        request_id = response.json()["request_id"]
        
        # Check status
        response = test_client.get(f"/api/v1/auth/status/{request_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["request_id"] == request_id
        assert data["status"] == "pending"
    
    @pytest.mark.integration
    def test_auth_status_nonexistent(self, test_client):
        """Test checking status of non-existent auth request."""
        response = test_client.get("/api/v1/auth/status/nonexistent_id")
        
        assert response.status_code == 404
    
    @pytest.mark.integration
    def test_list_pending_requests(self, test_client):
        """Test listing pending authorization requests."""
        # Create a few auth requests
        for i in range(3):
            auth_data = {
                "app_name": f"Test DApp {i}",
                "app_url": f"https://testdapp{i}.com",
                "permissions": ["wallet_info"]
            }
            response = test_client.post("/api/v1/auth/request", json=auth_data)
            assert response.status_code == 200
        
        # List pending requests
        response = test_client.get("/api/v1/auth/pending")
        assert response.status_code == 200
        
        data = response.json()
        assert "pending_requests" in data
        assert len(data["pending_requests"]) >= 3  # At least the 3 we created


class TestSessionManagement:
    """Test session token management."""
    
    @pytest.mark.integration
    def test_session_validation(self, test_client):
        """Test session token validation."""
        # Try to access protected endpoint without token
        response = test_client.get("/api/v1/wallet/info")
        
        assert response.status_code in [401, 403]  # Unauthorized
    
    @pytest.mark.integration
    def test_session_with_invalid_token(self, test_client):
        """Test access with invalid session token."""
        headers = {"Authorization": "Bearer invalid_token_123"}
        response = test_client.get("/api/v1/wallet/info", headers=headers)
        
        assert response.status_code in [401, 403]  # Unauthorized
    
    @pytest.mark.integration
    def test_session_token_format(self, test_client):
        """Test session token format validation."""
        # Test various invalid token formats
        invalid_tokens = [
            "invalid_token",  # No Bearer prefix
            "Bearer",  # No token
            "Basic dGVzdA==",  # Wrong auth type
            "",  # Empty
        ]
        
        for token in invalid_tokens:
            headers = {"Authorization": token}
            response = test_client.get("/api/v1/wallet/info", headers=headers)
            assert response.status_code in [401, 403]


class TestPermissionValidation:
    """Test permission-based access control."""
    
    @pytest.mark.integration
    def test_wallet_info_permission(self, test_client):
        """Test wallet_info permission requirement."""
        # This would require a valid session with wallet_info permission
        # For now, just test that it requires authorization
        response = test_client.get("/api/v1/wallet/info")
        
        assert response.status_code in [401, 403]
    
    @pytest.mark.integration
    def test_balance_permission(self, test_client):
        """Test balance permission requirement."""
        response = test_client.get("/api/v1/balance/TAU")
        
        assert response.status_code in [401, 403]
    
    @pytest.mark.integration
    def test_transaction_permission(self, test_client):
        """Test transaction permission requirement."""
        tx_data = {
            "to": "recipient_address",
            "amount": 100.0,
            "currency": "TAU",
            "function": "transfer"
        }
        
        response = test_client.post("/api/v1/transaction", json=tx_data)
        
        assert response.status_code in [401, 403]
    
    @pytest.mark.integration
    def test_signing_permission(self, test_client):
        """Test signing permission requirement."""
        sign_data = {"message": "Test message"}
        
        response = test_client.post("/api/v1/sign", json=sign_data)
        
        assert response.status_code in [401, 403]


class TestAuthenticationIntegration:
    """Test complete authentication integration scenarios."""
    
    @pytest.mark.integration
    def test_complete_auth_flow_simulation(self, test_client):
        """Test complete authentication flow (simulated)."""
        # 1. DApp requests authorization
        auth_data = {
            "app_name": "Integration Test DApp",
            "app_url": "https://integrationtest.com",
            "permissions": ["wallet_info", "balance"],
            "description": "Integration test for complete auth flow"
        }
        
        response = test_client.post("/api/v1/auth/request", json=auth_data)
        assert response.status_code == 200
        
        auth_response = response.json()
        request_id = auth_response["request_id"]
        
        # 2. Check that request is pending
        response = test_client.get(f"/api/v1/auth/status/{request_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "pending"
        
        # 3. Verify request appears in pending list
        response = test_client.get("/api/v1/auth/pending")
        assert response.status_code == 200
        
        pending_requests = response.json()["pending_requests"]
        request_ids = [req["request_id"] for req in pending_requests]
        assert request_id in request_ids
        
        # Note: Actual approval/denial would require wallet interaction
        # which is beyond the scope of this test
    
    @pytest.mark.integration
    def test_multiple_app_requests(self, test_client):
        """Test multiple apps requesting authorization."""
        apps = [
            {"name": "DApp A", "url": "https://dappa.com", "permissions": ["wallet_info"]},
            {"name": "DApp B", "url": "https://dappb.com", "permissions": ["balance"]},
            {"name": "DApp C", "url": "https://dappc.com", "permissions": ["wallet_info", "balance"]},
        ]
        
        request_ids = []
        
        # Create requests for all apps
        for app in apps:
            auth_data = {
                "app_name": app["name"],
                "app_url": app["url"],
                "permissions": app["permissions"]
            }
            
            response = test_client.post("/api/v1/auth/request", json=auth_data)
            assert response.status_code == 200
            
            request_ids.append(response.json()["request_id"])
        
        # Verify all requests are pending
        response = test_client.get("/api/v1/auth/pending")
        assert response.status_code == 200
        
        pending_requests = response.json()["pending_requests"]
        pending_ids = [req["request_id"] for req in pending_requests]
        
        for request_id in request_ids:
            assert request_id in pending_ids
    
    @pytest.mark.integration
    def test_auth_request_with_cors(self, mock_wallet):
        """Test auth request with CORS headers."""
        cors_config = CORSConfig.production(["https://testdapp.com"])
        server = create_server(
            wallet_type=WalletType.DESKTOP,
            cors_config=cors_config
        )
        server.wallet = mock_wallet
        
        client = TestClient(server.app)
        
        auth_data = {
            "app_name": "CORS Test DApp",
            "app_url": "https://testdapp.com",
            "permissions": ["wallet_info"]
        }
        
        response = client.post(
            "/api/v1/auth/request",
            json=auth_data,
            headers={"Origin": "https://testdapp.com"}
        )
        
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "https://testdapp.com"
        
        data = response.json()
        assert "request_id" in data
        assert data["status"] == "pending"