"""
Unit tests for Xian UWP data models and enums.

Tests cover validation, serialization, and business logic
for all Pydantic models and enums.
"""

import pytest
from pydantic import ValidationError

from xian_uwp.models import (
    WalletType, Permission, AuthStatus,
    CORSConfig, AuthorizationRequest, AuthorizationResponse,
    WalletInfo, TransactionRequest, TransactionResult
)


class TestEnums:
    """Test enum definitions and values."""
    
    @pytest.mark.unit
    def test_wallet_type_enum(self):
        """Test WalletType enum values."""
        assert WalletType.DESKTOP == "desktop"
        assert WalletType.CLI == "cli"
        assert WalletType.WEB == "web"
        
        # Test all values are unique
        values = [wt.value for wt in WalletType]
        assert len(values) == len(set(values))
    
    @pytest.mark.unit
    def test_permission_enum(self):
        """Test Permission enum values."""
        assert Permission.WALLET_INFO == "wallet_info"
        assert Permission.BALANCE == "balance"
        assert Permission.TRANSACTIONS == "transactions"
        assert Permission.SIGN_MESSAGE == "sign_message"
        
        # Test all values are unique
        values = [p.value for p in Permission]
        assert len(values) == len(set(values))
    
    @pytest.mark.unit
    def test_auth_status_enum(self):
        """Test AuthStatus enum values."""
        assert AuthStatus.PENDING == "pending"
        assert AuthStatus.APPROVED == "approved"
        assert AuthStatus.DENIED == "denied"
        assert AuthStatus.EXPIRED == "expired"


class TestCORSConfig:
    """Test CORS configuration model."""
    
    @pytest.mark.unit
    def test_cors_config_creation(self):
        """Test basic CORS config creation."""
        config = CORSConfig(
            allow_origins=["https://mydapp.com"],
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization"],
            max_age=3600
        )
        
        assert config.allow_origins == ["https://mydapp.com"]
        assert config.allow_credentials is True
        assert config.allow_methods == ["GET", "POST"]
        assert config.allow_headers == ["Authorization"]
        assert config.max_age == 3600
    
    @pytest.mark.unit
    def test_cors_config_defaults(self):
        """Test CORS config default values."""
        config = CORSConfig(allow_origins=["*"])
        
        assert config.allow_origins == ["*"]
        assert config.allow_credentials is True
        assert config.allow_methods == ["*"]
        assert config.allow_headers == ["*"]
        assert config.max_age == 600
    
    @pytest.mark.unit
    def test_cors_config_development_preset(self):
        """Test development CORS preset."""
        config = CORSConfig.development()
        
        assert config.allow_origins == ["*"]
        assert config.allow_credentials is True
    
    @pytest.mark.unit
    def test_cors_config_production_preset(self):
        """Test production CORS preset."""
        origins = ["https://mydapp.com", "https://app.mydapp.com"]
        config = CORSConfig.production(origins)
        
        assert config.allow_origins == origins
        assert config.allow_credentials is True
        assert "GET" in config.allow_methods
        assert "POST" in config.allow_methods
    
    @pytest.mark.unit
    def test_cors_config_localhost_dev_preset(self):
        """Test localhost development CORS preset."""
        config = CORSConfig.localhost_dev()
        
        # Should include common development ports
        assert "http://localhost:3000" in config.allow_origins
        assert "http://localhost:5173" in config.allow_origins
        assert "http://localhost:8080" in config.allow_origins
        assert "http://127.0.0.1:3000" in config.allow_origins
        
        assert config.allow_credentials is True
    
    @pytest.mark.unit
    def test_cors_config_validation(self):
        """Test CORS config validation."""
        # Empty origins should be allowed
        config = CORSConfig(allow_origins=[])
        assert config.allow_origins == []
        
        # Negative max_age should be allowed (no validation)
        config = CORSConfig(allow_origins=["*"], max_age=-1)
        assert config.max_age == -1


class TestAuthorizationRequest:
    """Test authentication request model."""
    
    @pytest.mark.unit
    def test_auth_request_creation(self):
        """Test basic auth request creation."""
        request = AuthorizationRequest(
            app_name="Test DApp",
            app_url="https://testdapp.com",
            permissions=[Permission.WALLET_INFO, Permission.BALANCE]
        )
        
        assert request.app_name == "Test DApp"
        assert request.app_url == "https://testdapp.com"
        assert Permission.WALLET_INFO in request.permissions
        assert Permission.BALANCE in request.permissions
    
    @pytest.mark.unit
    def test_auth_request_validation(self):
        """Test auth request validation."""
        # Empty app_name should be invalid (min_length=1)
        with pytest.raises(ValidationError):
            AuthorizationRequest(
                app_name="",
                app_url="https://testdapp.com",
                permissions=[Permission.WALLET_INFO]
            )
        
        # Valid URL formats should work
        request = AuthorizationRequest(
            app_name="Test DApp",
            app_url="not-a-url",  # URL validation is not strict in the model
            permissions=[Permission.WALLET_INFO]
        )
        assert request.app_url == "not-a-url"
        
        # Empty permissions should be allowed
        request = AuthorizationRequest(
            app_name="Test DApp",
            app_url="https://testdapp.com",
            permissions=[]
        )
        assert request.permissions == []
    
    @pytest.mark.unit
    def test_auth_request_optional_fields(self):
        """Test auth request optional fields."""
        request = AuthorizationRequest(
            app_name="Test DApp",
            app_url="https://testdapp.com",
            permissions=[Permission.WALLET_INFO],
            description="Test description"
        )
        
        assert request.description == "Test description"


class TestAuthorizationResponse:
    """Test authentication response model."""
    
    @pytest.mark.unit
    def test_auth_response_creation(self):
        """Test basic auth response creation."""
        from datetime import datetime, timedelta
        expires_at = datetime.now() + timedelta(hours=1)
        
        response = AuthorizationResponse(
            session_token="test_token_123",
            expires_at=expires_at,
            permissions=[Permission.WALLET_INFO],
            status="pending"
        )
        
        assert response.session_token == "test_token_123"
        assert response.expires_at == expires_at
        assert response.status == "pending"
    
    @pytest.mark.unit
    def test_auth_response_with_session(self):
        """Test auth response with session token."""
        from datetime import datetime, timedelta
        expires_at = datetime.now() + timedelta(hours=1)
        
        response = AuthorizationResponse(
            session_token="session_token_123",
            expires_at=expires_at,
            permissions=[Permission.WALLET_INFO],
            status="approved"
        )
        
        assert response.session_token == "session_token_123"
        assert response.status == "approved"


class TestWalletInfo:
    """Test wallet info model."""
    
    @pytest.mark.unit
    def test_wallet_info_creation(self):
        """Test basic wallet info creation."""
        info = WalletInfo(
            address="test_address_123",
            truncated_address="test_addr...123",
            locked=False,
            network="https://testnet.xian.org",
            chain_id="xian-testnet",
            wallet_type=WalletType.DESKTOP
        )
        
        assert info.address == "test_address_123"
        assert info.truncated_address == "test_addr...123"
        assert info.locked is False
        assert info.network == "https://testnet.xian.org"
        assert info.chain_id == "xian-testnet"
        assert info.wallet_type == WalletType.DESKTOP
    
    @pytest.mark.unit
    def test_wallet_info_validation(self):
        """Test wallet info validation."""
        # Empty address should be allowed (no validation)
        info = WalletInfo(
            address="",
            truncated_address="",
            locked=True,
            network="https://testnet.xian.org",
            chain_id="xian-testnet",
            wallet_type=WalletType.DESKTOP
        )
        assert info.address == ""
        
        # Any network format should be allowed
        info = WalletInfo(
            address="test_address_123",
            truncated_address="test_addr...123",
            locked=False,
            network="not-a-url",
            chain_id="xian-testnet",
            wallet_type=WalletType.DESKTOP
        )
        assert info.network == "not-a-url"


class TestTransactionModels:
    """Test transaction request and response models."""
    
    @pytest.mark.unit
    def test_transaction_request_creation(self):
        """Test basic transaction request creation."""
        request = TransactionRequest(
            contract="currency",
            function="transfer",
            kwargs={
                "to": "recipient_address",
                "amount": 100.0
            }
        )
        
        assert request.contract == "currency"
        assert request.function == "transfer"
        assert request.kwargs["to"] == "recipient_address"
        assert request.kwargs["amount"] == 100.0
    
    @pytest.mark.unit
    def test_transaction_request_with_kwargs(self):
        """Test transaction request with additional kwargs."""
        request = TransactionRequest(
            contract="currency",
            function="transfer",
            kwargs={
                "to": "recipient_address",
                "amount": 100.0,
                "memo": "Test payment"
            }
        )
        
        assert request.kwargs["memo"] == "Test payment"
    
    @pytest.mark.unit
    def test_transaction_request_validation(self):
        """Test transaction request validation."""
        # Empty contract should be invalid
        with pytest.raises(ValidationError):
            TransactionRequest(
                contract="",
                function="transfer",
                kwargs={"to": "recipient", "amount": 100.0}
            )
        
        # Empty function should be invalid
        with pytest.raises(ValidationError):
            TransactionRequest(
                contract="currency",
                function="",
                kwargs={"to": "recipient", "amount": 100.0}
            )
    
    @pytest.mark.unit
    def test_transaction_response_creation(self):
        """Test basic transaction response creation."""
        response = TransactionResult(
            success=True,
            transaction_hash="tx_123",
            result={"status": "success"},
            gas_used=1000
        )
        
        assert response.success is True
        assert response.transaction_hash == "tx_123"
        assert response.result == {"status": "success"}
        assert response.gas_used == 1000


class TestModelSerialization:
    """Test model serialization and deserialization."""
    
    @pytest.mark.unit
    def test_cors_config_serialization(self):
        """Test CORS config JSON serialization."""
        config = CORSConfig.production(["https://mydapp.com"])
        
        # Test to dict
        data = config.model_dump()
        assert data["allow_origins"] == ["https://mydapp.com"]
        assert data["allow_credentials"] is True
        
        # Test from dict
        new_config = CORSConfig(**data)
        assert new_config.allow_origins == config.allow_origins
        assert new_config.allow_credentials == config.allow_credentials
    
    @pytest.mark.unit
    def test_auth_request_serialization(self):
        """Test auth request JSON serialization."""
        request = AuthorizationRequest(
            app_name="Test DApp",
            app_url="https://testdapp.com",
            permissions=[Permission.WALLET_INFO, Permission.BALANCE]
        )
        
        # Test to dict
        data = request.model_dump()
        assert data["app_name"] == "Test DApp"
        assert data["permissions"] == ["wallet_info", "balance"]
        
        # Test from dict
        new_request = AuthorizationRequest(**data)
        assert new_request.app_name == request.app_name
        assert new_request.permissions == request.permissions
    
    @pytest.mark.unit
    def test_wallet_info_serialization(self):
        """Test wallet info JSON serialization."""
        info = WalletInfo(
            address="test_address_123",
            truncated_address="test_addr...123",
            locked=False,
            network="https://testnet.xian.org",
            chain_id="xian-testnet",
            wallet_type=WalletType.DESKTOP
        )
        
        # Test to dict
        data = info.model_dump()
        assert data["wallet_type"] == "desktop"
        
        # Test from dict
        new_info = WalletInfo(**data)
        assert new_info.wallet_type == WalletType.DESKTOP