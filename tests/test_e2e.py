#!/usr/bin/env python3
"""
End-to-end test for Xian Universal Wallet Protocol
"""
import asyncio
import httpx
import time
import json
from typing import Dict, Any

# Test configuration
SERVER_URL = "http://localhost:58905"
API_BASE = f"{SERVER_URL}/api/v1"

async def test_protocol_e2e():
    """Test the protocol end-to-end"""
    print("🧪 Xian Universal Wallet Protocol - End-to-End Test\n")
    
    # HTTP client
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # 1. Check wallet status
        print("1️⃣ Checking wallet status...")
        response = await client.get(f"{API_BASE}/wallet/status")
        assert response.status_code == 200
        status = response.json()
        print(f"✅ Wallet Status:")
        print(f"   - Available: {status['available']}")
        print(f"   - Locked: {status['locked']}")
        print(f"   - Type: {status['wallet_type']}")
        print(f"   - Network: {status['network']}")
        print(f"   - Version: {status['version']}\n")
        
        # 2. Request authorization
        print("2️⃣ Requesting authorization...")
        auth_request = {
            "app_name": "E2E Test DApp",
            "app_url": "http://localhost:8080",
            "permissions": ["wallet_info", "balance", "transactions", "sign_message"]
        }
        response = await client.post(f"{API_BASE}/auth/request", json=auth_request)
        assert response.status_code == 200
        auth_response = response.json()
        request_id = auth_response["request_id"]
        print(f"✅ Authorization requested: {request_id}\n")
        
        # 3. Approve authorization (simulating wallet approval)
        print("3️⃣ Approving authorization...")
        response = await client.post(f"{API_BASE}/auth/approve/{request_id}")
        assert response.status_code == 200
        approval = response.json()
        session_token = approval["session_token"]
        print(f"✅ Authorization approved:")
        print(f"   - Token: {session_token[:16]}...")
        print(f"   - Expires: {approval['expires_at']}")
        print(f"   - Permissions: {approval['permissions']}\n")
        
        # Set auth header for subsequent requests
        headers = {"Authorization": f"Bearer {session_token}"}
        
        # 4. Unlock wallet (if needed)
        if status['locked']:
            print("4️⃣ Unlocking wallet...")
            unlock_request = {"password": "demo_password"}
            response = await client.post(f"{API_BASE}/wallet/unlock", json=unlock_request)
            if response.status_code == 200:
                print("✅ Wallet unlocked\n")
            else:
                print(f"⚠️  Failed to unlock: {response.text}\n")
        
        # 5. Get wallet info
        print("5️⃣ Getting wallet info...")
        response = await client.get(f"{API_BASE}/wallet/info", headers=headers)
        if response.status_code == 200:
            wallet_info = response.json()
            print(f"✅ Wallet Info:")
            print(f"   - Address: {wallet_info['truncated_address']}")
            print(f"   - Chain ID: {wallet_info['chain_id']}")
            print(f"   - Network: {wallet_info['network']}")
            print(f"   - Type: {wallet_info['wallet_type']}\n")
        else:
            print(f"❌ Failed to get wallet info: {response.status_code} - {response.text}\n")
        
        # 6. Get balance
        print("6️⃣ Getting balance...")
        response = await client.get(f"{API_BASE}/balance/currency", headers=headers)
        if response.status_code == 200:
            balance_info = response.json()
            print(f"✅ Balance: {balance_info['balance']} {balance_info.get('symbol', 'XIAN')}\n")
        else:
            print(f"❌ Failed to get balance: {response.status_code} - {response.text}\n")
        
        # 7. Sign message
        print("7️⃣ Signing message...")
        sign_request = {"message": "Hello from E2E Test!"}
        response = await client.post(f"{API_BASE}/sign", json=sign_request, headers=headers)
        if response.status_code == 200:
            signature_info = response.json()
            print(f"✅ Message signed:")
            print(f"   - Message: {signature_info['message']}")
            print(f"   - Signature: {signature_info['signature'][:32]}...\n")
        else:
            print(f"❌ Failed to sign message: {response.status_code} - {response.text}\n")
        
        # 8. Test transaction (expected to fail without funds)
        print("8️⃣ Testing transaction...")
        tx_request = {
            "contract": "currency",
            "function": "transfer",
            "kwargs": {"to": "test_recipient", "amount": 1},
            "stamps_supplied": 50000
        }
        response = await client.post(f"{API_BASE}/transaction", json=tx_request, headers=headers)
        if response.status_code == 200:
            tx_result = response.json()
            if tx_result['success']:
                print(f"✅ Transaction sent: {tx_result['transaction_hash']}")
            else:
                print(f"⚠️  Transaction failed (expected): {tx_result.get('errors', 'Unknown error')}")
        else:
            print(f"⚠️  Transaction request failed: {response.status_code} - {response.text}\n")
        
        # 9. Add token
        print("9️⃣ Adding custom token...")
        token_request = {
            "contract_address": "test_token",
            "token_name": "Test Token",
            "token_symbol": "TEST"
        }
        response = await client.post(f"{API_BASE}/tokens/add", json=token_request, headers=headers)
        if response.status_code == 200:
            token_result = response.json()
            print(f"✅ Token added: {token_result['accepted']}\n")
        else:
            print(f"❌ Failed to add token: {response.status_code} - {response.text}\n")
        
        # 10. Test WebSocket connection
        print("🔟 Testing WebSocket...")
        try:
            import websockets
            ws_url = f"ws://localhost:58905/ws/v1"
            async with websockets.connect(ws_url) as websocket:
                # Send ping
                await websocket.send('{"type":"ping"}')
                response = await websocket.recv()
                if "pong" in response:
                    print("✅ WebSocket connection successful\n")
                else:
                    print(f"⚠️  Unexpected WebSocket response: {response}\n")
        except Exception as e:
            print(f"❌ WebSocket test failed: {e}\n")
    
    print("🎉 End-to-end test completed!")

async def start_test_server():
    """Start a test server in the background"""
    from xian_uwp.server import WalletProtocolServer
    from xian_uwp.models import WalletType
    from xian_py.wallet import Wallet
    from xian_py.xian import Xian
    import hashlib
    
    # Create and configure server
    server = WalletProtocolServer(wallet_type=WalletType.DESKTOP)
    
    # Initialize wallet before starting server
    server.wallet = Wallet()
    server.xian_client = Xian(server.network_url, wallet=server.wallet)
    server.password_hash = hashlib.sha256("demo_password".encode()).hexdigest()
    server.is_locked = False  # Start unlocked for testing
    print(f"Test wallet initialized: {server.wallet.public_key}")
    
    # Run server in background
    import uvicorn
    config = uvicorn.Config(server.app, host="127.0.0.1", port=58905, log_level="error")
    server_instance = uvicorn.Server(config)
    
    # Start server in background task
    asyncio.create_task(server_instance.serve())
    await asyncio.sleep(2)  # Wait for server to start
    
    return server_instance

async def main():
    """Main test runner"""
    # Start server
    print("Starting test server...\n")
    server = await start_test_server()
    
    try:
        # Run tests
        await test_protocol_e2e()
    finally:
        # Cleanup
        server.should_exit = True
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())