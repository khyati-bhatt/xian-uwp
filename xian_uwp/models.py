# protocol/models.py
"""
Xian Wallet Protocol - Data Models
Universal data models for all wallet implementations
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import datetime


class WalletType(str, Enum):
    """Supported wallet types"""
    DESKTOP = "desktop"
    WEB = "web" 
    CLI = "cli"
    HARDWARE = "hardware"


class ConnectionStatus(str, Enum):
    """Connection status states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    LOCKED = "locked"


class Permission(str, Enum):
    """Available permissions for DApps"""
    WALLET_INFO = "wallet_info"
    BALANCE = "balance"
    TRANSACTIONS = "transactions"
    SIGN_MESSAGE = "sign_message"
    ADD_TOKEN = "add_token"


# Request Models
class AuthorizationRequest(BaseModel):
    """Authorization request from DApp"""
    app_name: str = Field(..., min_length=1, max_length=100)
    app_url: str = Field(..., min_length=1, max_length=500)
    permissions: List[Permission]
    description: Optional[str] = Field(None, max_length=500)


class TransactionRequest(BaseModel):
    """Transaction request"""
    contract: str = Field(..., min_length=1, max_length=100)
    function: str = Field(..., min_length=1, max_length=100)
    kwargs: Dict[str, Any]
    stamps_supplied: Optional[int] = Field(None, ge=0)


class SignMessageRequest(BaseModel):
    """Message signing request"""
    message: str = Field(..., min_length=1, max_length=10000)


class AddTokenRequest(BaseModel):
    """Add token request"""
    contract_address: str = Field(..., min_length=1, max_length=100)
    token_name: Optional[str] = Field(None, max_length=100)
    token_symbol: Optional[str] = Field(None, max_length=20)
    decimals: Optional[int] = Field(None, ge=0, le=18)


class UnlockRequest(BaseModel):
    """Wallet unlock request"""
    password: str = Field(..., min_length=1)


# Response Models
class WalletInfo(BaseModel):
    """Wallet information response"""
    address: str
    truncated_address: str
    locked: bool
    chain_id: str
    network: str
    wallet_type: WalletType
    version: str = "1.0.0"


class BalanceResponse(BaseModel):
    """Balance query response"""
    balance: Union[float, int]
    contract: str
    symbol: Optional[str] = None
    decimals: Optional[int] = None


class TransactionResult(BaseModel):
    """Transaction result"""
    success: bool
    transaction_hash: Optional[str] = None
    result: Optional[Any] = None
    errors: Optional[List[str]] = None
    gas_used: Optional[int] = None


class SignatureResponse(BaseModel):
    """Message signature response"""
    signature: str
    message: str
    address: str


class AuthorizationResponse(BaseModel):
    """Authorization response"""
    session_token: str
    expires_at: datetime
    permissions: List[Permission]
    status: str = "approved"


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    code: str
    details: Optional[str] = None


class StatusResponse(BaseModel):
    """Wallet status response"""
    available: bool
    locked: bool
    wallet_type: WalletType
    network: str
    chain_id: str
    version: str


# Internal Models
class Session(BaseModel):
    """Internal session model"""
    token: str
    app_name: str
    app_url: str
    permissions: List[Permission]
    created_at: datetime
    expires_at: datetime
    last_activity: datetime


class PendingRequest(BaseModel):
    """Pending authorization request"""
    request_id: str
    app_name: str
    app_url: str
    permissions: List[Permission]
    description: Optional[str]
    created_at: datetime
    status: str = "pending"


# Protocol Constants
class ProtocolConfig:
    """Protocol configuration constants"""
    DEFAULT_PORT = 8545
    DEFAULT_HOST = "127.0.0.1"
    API_VERSION = "v1"
    PROTOCOL_VERSION = "1.0.0"
    SESSION_TIMEOUT_MINUTES = 60
    AUTO_LOCK_MINUTES = 30
    MAX_SESSIONS = 10
    CACHE_TTL_SECONDS = 30


# API Endpoints
class Endpoints:
    """API endpoint constants"""
    # Auth endpoints
    AUTH_REQUEST = "/api/v1/auth/request"
    AUTH_APPROVE = "/api/v1/auth/approve/{request_id}"
    AUTH_DENY = "/api/v1/auth/deny/{request_id}"
    AUTH_REVOKE = "/api/v1/auth/revoke"
    
    # Wallet endpoints
    WALLET_STATUS = "/api/v1/wallet/status"
    WALLET_INFO = "/api/v1/wallet/info"
    WALLET_UNLOCK = "/api/v1/wallet/unlock"
    WALLET_LOCK = "/api/v1/wallet/lock"
    
    # Transaction endpoints
    BALANCE = "/api/v1/balance/{contract}"
    APPROVED_BALANCE = "/api/v1/balance/{contract}/{spender}"
    TRANSACTION = "/api/v1/transaction"
    SIGN_MESSAGE = "/api/v1/sign"
    
    # Token management
    ADD_TOKEN = "/api/v1/tokens/add"
    LIST_TOKENS = "/api/v1/tokens"
    
    # WebSocket
    WEBSOCKET = "/ws/v1"


# Error Codes
class ErrorCodes:
    """Standard error codes"""
    WALLET_LOCKED = "WALLET_LOCKED"
    UNAUTHORIZED = "UNAUTHORIZED"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    INVALID_REQUEST = "INVALID_REQUEST"
    NETWORK_ERROR = "NETWORK_ERROR"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    TRANSACTION_FAILED = "TRANSACTION_FAILED"
    USER_REJECTED = "USER_REJECTED"
    WALLET_NOT_FOUND = "WALLET_NOT_FOUND"
    INVALID_CONTRACT = "INVALID_CONTRACT"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"