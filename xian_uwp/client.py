"""
Xian Wallet Protocol Client
Universal client library for connecting to any Xian wallet
"""

import asyncio
import time
import logging
import httpx
import websockets

from typing import Dict, Any, Optional, List, Union

from .models import (
    ConnectionStatus, Permission, ProtocolConfig, Endpoints, ErrorCodes,
    AuthorizationRequest, TransactionRequest, SignMessageRequest, AddTokenRequest,
    WalletInfo, BalanceResponse, TransactionResult, SignatureResponse,
    AuthorizationResponse, StatusResponse
)


logger = logging.getLogger(__name__)


class WalletProtocolError(Exception):
    """Base exception for wallet protocol errors"""
    
    def __init__(self, message: str, code: str = None):
        super().__init__(message)
        self.code = code


class XianWalletClient:
    """
    Universal Xian Wallet Client
    Connects to any wallet type via the standard protocol
    """
    
    def __init__(
        self,
        app_name: str,
        app_url: str = "https://localhost",
        server_url: str = f"http://{ProtocolConfig.DEFAULT_HOST}:{ProtocolConfig.DEFAULT_PORT}",
        permissions: Optional[List[Permission]] = None,
        wallet_url: str = None  # Alias for server_url for backwards compatibility
    ):
        self.app_name = app_name
        self.app_url = app_url
        # Use wallet_url if provided, otherwise use server_url
        self.server_url = (wallet_url or server_url).rstrip('/')
        self.permissions = permissions or [
            Permission.WALLET_INFO,
            Permission.BALANCE,
            Permission.TRANSACTIONS,
            Permission.SIGN_MESSAGE
        ]
        
        # Connection state
        self.session_token: Optional[str] = None
        self.status = ConnectionStatus.DISCONNECTED
        self.wallet_info: Optional[WalletInfo] = None
        
        # HTTP client with connection pooling
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        
        # WebSocket connection
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        
        # Cache with TTL
        self._cache: Dict[str, tuple] = {}  # (data, timestamp)
        
        # Retry configuration
        self._max_retries = 3
        self._retry_delay = 1.0
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
    
    async def connect(self) -> bool:
        """
        Connect to wallet
            
        Returns:
            True if connected successfully
        """
        try:
            self.status = ConnectionStatus.CONNECTING
            
            # Check if wallet is available
            if not await self._check_wallet_available():
                raise WalletProtocolError("Wallet server not available", ErrorCodes.WALLET_NOT_FOUND)
            
            # Request authorization
            session_token = await self._request_authorization()
            
            if session_token:
                self.session_token = session_token
                self.status = ConnectionStatus.CONNECTED
                
                # Get initial wallet info
                self.wallet_info = await self.get_wallet_info()
                
                logger.info(f"✅ Connected to {self.wallet_info.wallet_type} wallet: {self.wallet_info.truncated_address}")
                return True
            
            return False
            
        except Exception as e:
            self.status = ConnectionStatus.ERROR
            raise WalletProtocolError(f"Connection failed: {str(e)}")
    
    async def disconnect(self):
        """Disconnect from wallet"""
        try:
            if self.websocket:
                await self.websocket.close()
            
            await self.http_client.aclose()
            
            self.session_token = None
            self.status = ConnectionStatus.DISCONNECTED
            self.wallet_info = None
            self._cache.clear()
            
            logger.info("🔌 Disconnected from wallet")
            
        except Exception as e:
            logger.warning(f"Error during disconnect: {e}")
    
    async def get_wallet_info(self) -> WalletInfo:
        """Get wallet information"""
        await self._ensure_connected()
        
        cache_key = "wallet_info"
        cached = self._get_cached(cache_key, ttl_seconds=60)
        if cached:
            return cached
        
        response = await self._make_request("GET", Endpoints.WALLET_INFO)
        wallet_info = WalletInfo(**response)
        
        self._set_cache(cache_key, wallet_info)
        self.wallet_info = wallet_info
        return wallet_info
    
    async def get_balance(self, contract: str = "currency") -> Union[float, int]:
        """Get token balance"""
        await self._ensure_connected()
        
        cache_key = f"balance_{contract}"
        cached = self._get_cached(cache_key, ttl_seconds=10)
        if cached:
            return cached.balance
        
        endpoint = Endpoints.BALANCE.replace("{contract}", contract)
        response = await self._make_request("GET", endpoint)
        balance_response = BalanceResponse(**response)
        
        self._set_cache(cache_key, balance_response)
        return balance_response.balance
    
    async def get_approved_balance(self, contract: str, spender: str) -> Union[float, int]:
        """Get approved balance for spender"""
        await self._ensure_connected()
        
        cache_key = f"approved_{contract}_{spender}"
        cached = self._get_cached(cache_key, ttl_seconds=30)
        if cached:
            return cached
        
        endpoint = Endpoints.APPROVED_BALANCE.replace("{contract}", contract).replace("{spender}", spender)
        response = await self._make_request("GET", endpoint)
        balance = response.get("approved_amount", 0)
        
        self._set_cache(cache_key, balance)
        return balance
    
    async def send_transaction(
        self,
        contract: str,
        function: str,
        kwargs: Dict[str, Any],
        stamps_supplied: Optional[int] = None
    ) -> TransactionResult:
        """Send transaction"""
        await self._ensure_connected()
        
        request = TransactionRequest(
            contract=contract,
            function=function,
            kwargs=kwargs,
            stamps_supplied=stamps_supplied
        )
        
        response = await self._make_request("POST", Endpoints.TRANSACTION, json=request.model_dump())
        result = TransactionResult(**response)
        
        # Clear balance cache after transaction
        self._clear_cache_pattern("balance_")
        
        return result
    
    async def sign_message(self, message: str) -> str:
        """Sign message"""
        await self._ensure_connected()
        
        request = SignMessageRequest(message=message)
        response = await self._make_request("POST", Endpoints.SIGN_MESSAGE, json=request.model_dump())
        signature_response = SignatureResponse(**response)
        
        return signature_response.signature
    
    async def add_token(self, contract_address: str, token_name: str = None, token_symbol: str = None, decimals: int = None) -> bool:
        """Add token to wallet"""
        await self._ensure_connected()
        
        request = AddTokenRequest(
            contract_address=contract_address,
            token_name=token_name,
            token_symbol=token_symbol,
            decimals=decimals
        )
        
        response = await self._make_request("POST", Endpoints.ADD_TOKEN, json=request.model_dump())
        return response.get("accepted", False)
    
    # Public API methods
    async def check_wallet_available(self) -> bool:
        """Check if wallet server is available"""
        return await self._check_wallet_available()
    
    async def request_authorization(self, permissions: Optional[List[Permission]] = None) -> dict:
        """Request authorization from wallet"""
        if permissions:
            # Temporarily override permissions for this request
            original_permissions = self.permissions
            self.permissions = permissions
            try:
                session_token = await self._request_authorization()
                return {"session_token": session_token, "status": "approved" if session_token else "denied"}
            finally:
                self.permissions = original_permissions
        else:
            session_token = await self._request_authorization()
            return {"session_token": session_token, "status": "approved" if session_token else "denied"}
    
    async def wait_for_authorization(self, request_id: str, timeout: int = 300) -> dict:
        """
        Wait for authorization to be approved/denied
        
        Args:
            request_id: The authorization request ID to wait for
            timeout: Maximum time to wait in seconds (default: 5 minutes)
            
        Returns:
            Dictionary with status and session_token if approved
        """
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                # Check authorization status
                status_endpoint = Endpoints.AUTH_STATUS.replace("{request_id}", request_id)
                response = await self.http_client.get(f"{self.server_url}{status_endpoint}")
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status")
                    
                    if status == "approved":
                        return {
                            "status": "approved", 
                            "session_token": result.get("session_token")
                        }
                    elif status == "denied":
                        return {"status": "denied", "session_token": None}
                    # If status is "pending", continue polling
                
                # Wait before next poll
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error checking authorization status: {e}")
                await asyncio.sleep(2)
        
        # Timeout reached
        return {"status": "timeout", "session_token": None}
    
    # Private methods
    async def _check_wallet_available(self) -> bool:
        """Check if wallet server is available"""
        try:
            response = await self.http_client.get(f"{self.server_url}{Endpoints.WALLET_STATUS}")
            if response.status_code == 200:
                status = StatusResponse(**response.json())
                return status.available
            return False
        except:
            return False
    
    async def _request_authorization(self) -> Optional[str]:
        """Request authorization from wallet and wait for user approval"""
        auth_request = AuthorizationRequest(
            app_name=self.app_name,
            app_url=self.app_url,
            permissions=self.permissions,
            description=f"Authorization request from {self.app_name}"
        )
        
        # Request authorization
        response = await self.http_client.post(
            f"{self.server_url}{Endpoints.AUTH_REQUEST}",
            json=auth_request.model_dump()
        )
        
        if response.status_code != 200:
            raise WalletProtocolError("Authorization request failed")
        
        result = response.json()
        request_id = result["request_id"]
        
        logger.info(f"⏳ Waiting for authorization approval for {self.app_name} (request: {request_id})")
        
        # Wait for user approval using the proper polling method
        auth_result = await self.wait_for_authorization(request_id, timeout=300)
        
        if auth_result["status"] == "approved":
            return auth_result["session_token"]
        elif auth_result["status"] == "denied":
            raise WalletProtocolError("Authorization denied by user")
        elif auth_result["status"] == "timeout":
            raise WalletProtocolError("Authorization request timed out")
        
        return None
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated HTTP request with retry logic"""
        for attempt in range(self._max_retries):
            try:
                headers = kwargs.get("headers", {})
                if self.session_token:
                    headers["Authorization"] = f"Bearer {self.session_token}"
                kwargs["headers"] = headers
                
                response = await getattr(self.http_client, method.lower())(
                    f"{self.server_url}{endpoint}",
                    **kwargs
                )
                
                if response.status_code == 401 and attempt < self._max_retries - 1:
                    # Try to reconnect
                    await self._auto_reconnect()
                    continue
                
                if response.status_code == 423:
                    raise WalletProtocolError("Wallet is locked", ErrorCodes.WALLET_LOCKED)
                
                if not response.is_success:
                    error_detail = response.json().get("detail", "Request failed")
                    raise WalletProtocolError(error_detail)
                
                return response.json()
                
            except httpx.RequestError as e:
                if attempt == self._max_retries - 1:
                    raise WalletProtocolError(f"Network error: {str(e)}", ErrorCodes.NETWORK_ERROR)
                
                await asyncio.sleep(self._retry_delay * (attempt + 1))
    
    async def _auto_reconnect(self):
        """Automatically reconnect if session is lost"""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            raise WalletProtocolError("Max reconnection attempts exceeded")
        
        try:
            self._reconnect_attempts += 1
            await self.connect(auto_approve=True)
            self._reconnect_attempts = 0
        except Exception:
            pass
    
    async def _ensure_connected(self):
        """Ensure client is connected"""
        if not self.session_token:
            raise WalletProtocolError("Not connected to wallet", ErrorCodes.UNAUTHORIZED)
    
    # Cache management
    def _get_cached(self, key: str, ttl_seconds: int) -> Optional[Any]:
        """Get cached data if still valid"""
        if key not in self._cache:
            return None
        
        data, timestamp = self._cache[key]
        if time.time() - timestamp > ttl_seconds:
            del self._cache[key]
            return None
        
        return data
    
    def _set_cache(self, key: str, data: Any):
        """Set cache data"""
        self._cache[key] = (data, time.time())
    
    def _clear_cache_pattern(self, pattern: str):
        """Clear cache entries matching pattern"""
        keys_to_delete = [k for k in self._cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self._cache[key]


class XianWalletClientSync:
    """Synchronous wrapper for XianWalletClient"""
    
    def __init__(self, app_name: str, app_url: str = "http://localhost", **kwargs):
        self.client = XianWalletClient(app_name, app_url, **kwargs)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    # Property accessors for client attributes
    @property
    def app_name(self) -> str:
        return self.client.app_name
    
    @property
    def app_url(self) -> str:
        return self.client.app_url
    
    @property
    def base_url(self) -> str:
        return self.client.server_url
    
    @property
    def session_token(self) -> Optional[str]:
        return self.client.session_token
    
    @session_token.setter
    def session_token(self, value: Optional[str]):
        self.client.session_token = value
    
    def _run_async(self, coro):
        """Run async coroutine in sync context"""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop.run_until_complete(coro)
    
    def check_wallet_available(self) -> bool:
        """Check if wallet server is available"""
        return self._run_async(self.client.check_wallet_available())
    
    def request_authorization(self, permissions: Optional[List[Permission]] = None) -> dict:
        """Request authorization from wallet"""
        return self._run_async(self.client.request_authorization(permissions))
    
    def wait_for_authorization(self, request_id: str = None) -> dict:
        """Wait for authorization to be approved/denied"""
        return self._run_async(self.client.wait_for_authorization(request_id))
    
    def connect(self) -> bool:
        """Connect to wallet"""
        return self._run_async(self.client.connect())
    
    def disconnect(self):
        """Disconnect from wallet"""
        return self._run_async(self.client.disconnect())
    
    def get_wallet_info(self) -> WalletInfo:
        """Get wallet information"""
        return self._run_async(self.client.get_wallet_info())
    
    def get_balance(self, contract: str = "currency") -> Union[float, int]:
        """Get token balance"""
        return self._run_async(self.client.get_balance(contract))
    
    def get_approved_balance(self, contract: str, spender: str) -> Union[float, int]:
        """Get approved balance"""
        return self._run_async(self.client.get_approved_balance(contract, spender))
    
    def send_transaction(self, contract: str, function: str, kwargs: Dict[str, Any], stamps_supplied: Optional[int] = None) -> TransactionResult:
        """Send transaction"""
        return self._run_async(self.client.send_transaction(contract, function, kwargs, stamps_supplied))
    
    def sign_message(self, message: str) -> str:
        """Sign message"""
        return self._run_async(self.client.sign_message(message))
    
    def add_token(self, contract_address: str, token_name: str = None, token_symbol: str = None) -> bool:
        """Add token to wallet"""
        return self._run_async(self.client.add_token(contract_address, token_name, token_symbol))


# Convenience factory functions
def create_client(
    app_name: str,
    app_url: str = "http://localhost",
    async_mode: bool = False,
    **kwargs
) -> Union[XianWalletClient, XianWalletClientSync]:
    """Create a wallet client instance"""
    if async_mode:
        return XianWalletClient(app_name, app_url, **kwargs)
    else:
        return XianWalletClientSync(app_name, app_url, **kwargs)


# Legacy compatibility (matches original dapp-utils interface)
class XianWalletUtils:
    """Legacy compatibility class matching JavaScript dapp-utils API"""
    
    def __init__(self):
        self.client: Optional[XianWalletClientSync] = None
    
    def init(self, _: str = None):
        """Initialize (legacy compatibility)"""
        self.client = XianWalletClientSync("Legacy DApp")
        return self.client.connect(auto_approve=True)
    
    def requestWalletInfo(self) -> dict:
        """Request wallet info (legacy compatibility)"""
        if not self.client:
            raise WalletProtocolError("Not initialized")
        info = self.client.get_wallet_info()
        return {
            "address": info.address,
            "truncatedAddress": info.truncated_address,
            "locked": info.locked,
            "chainId": info.chain_id
        }
    
    def getBalance(self, contract: str = "currency") -> Union[float, int]:
        """Get balance (legacy compatibility)"""
        if not self.client:
            raise WalletProtocolError("Not initialized")
        return self.client.get_balance(contract)
    
    def getApprovedBalance(self, contract: str, spender: str) -> Union[float, int]:
        """Get approved balance (legacy compatibility)"""
        if not self.client:
            raise WalletProtocolError("Not initialized")
        return self.client.get_approved_balance(contract, spender)
    
    def sendTransaction(self, contract: str, function: str, kwargs: dict, stamps_supplied: int = None) -> dict:
        """Send transaction (legacy compatibility)"""
        if not self.client:
            raise WalletProtocolError("Not initialized")
        result = self.client.send_transaction(contract, function, kwargs, stamps_supplied)
        return {
            "result": result.result,
            "errors": result.errors,
            "hash": result.transaction_hash
        }
    
    def signMessage(self, message: str) -> dict:
        """Sign message (legacy compatibility)"""
        if not self.client:
            raise WalletProtocolError("Not initialized")
        signature = self.client.sign_message(message)
        return {"signature": signature}
    
    def addToken(self, contract_address: str) -> dict:
        """Add token (legacy compatibility)"""
        if not self.client:
            raise WalletProtocolError("Not initialized")
        accepted = self.client.add_token(contract_address)
        return {"accepted": accepted}
