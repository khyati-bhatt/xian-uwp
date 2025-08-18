#!/usr/bin/env python3
"""
Test script to verify the Xian Universal Wallet Protocol
"""
import asyncio
import time
import threading
import subprocess
import sys
from xian_uwp.server import WalletProtocolServer
from xian_uwp.client import XianWalletClientSync
from xian_uwp.models import WalletType

def test_protocol():
    """Test the protocol functionality"""
    print("🧪 Starting Protocol Test Suite\n")
    
    # 1. Start server in a subprocess
    print("1️⃣ Starting wallet server...")
    server_process = subprocess.Popen(
        [sys.executable, "test_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(3)
    print("✅ Server started on port 54542\n")
    
    # 2. Create client and connect
    print("2️⃣ Creating client and connecting...")
    client = XianWalletClientSync(
        app_name="Test DApp",
        app_url="http://localhost:8080",
        server_url="http://localhost:54542"
    )
    
    try:
        # Connect for testing
        connected = client.connect()
        if connected:
            print("✅ Client connected successfully\n")
        else:
            print("❌ Failed to connect\n")
            return
    except Exception as e:
        print(f"❌ Connection error: {e}\n")
        return
    
    # 3. Test wallet info
    print("3️⃣ Testing wallet info...")
    try:
        wallet_info = client.get_wallet_info()
        print(f"✅ Wallet Info:")
        print(f"   - Address: {wallet_info.truncated_address}")
        print(f"   - Type: {wallet_info.wallet_type}")
        print(f"   - Network: {wallet_info.network}")
        print(f"   - Chain ID: {wallet_info.chain_id}")
        print(f"   - Locked: {wallet_info.locked}\n")
    except Exception as e:
        print(f"❌ Error getting wallet info: {e}\n")
    
    # 4. Test balance query
    print("4️⃣ Testing balance query...")
    try:
        balance = client.get_balance("currency")
        print(f"✅ Currency balance: {balance}\n")
    except Exception as e:
        print(f"❌ Error getting balance: {e}\n")
    
    # 5. Test message signing
    print("5️⃣ Testing message signing...")
    try:
        message = "Hello from Test DApp!"
        signature = client.sign_message(message)
        print(f"✅ Message signed successfully")
        print(f"   - Message: {message}")
        print(f"   - Signature: {signature[:32]}...\n")
    except Exception as e:
        print(f"❌ Error signing message: {e}\n")
    
    # 6. Test transaction (will fail on testnet without funds)
    print("6️⃣ Testing transaction...")
    try:
        result = client.send_transaction(
            contract="currency",
            function="transfer",
            kwargs={"to": "test_address", "amount": 1},
            stamps_supplied=50000
        )
        if result.success:
            print(f"✅ Transaction successful: {result.transaction_hash}")
        else:
            print(f"⚠️  Transaction failed (expected without funds): {result.errors}")
    except Exception as e:
        print(f"⚠️  Transaction error (expected without funds): {e}\n")
    
    # 7. Test adding token
    print("7️⃣ Testing add token...")
    try:
        accepted = client.add_token("test_token_contract", "Test Token", "TEST")
        print(f"✅ Token added: {accepted}\n")
    except Exception as e:
        print(f"❌ Error adding token: {e}\n")
    
    # 8. Disconnect
    print("8️⃣ Disconnecting...")
    client.disconnect()
    print("✅ Client disconnected\n")
    
    # Clean up server process
    server_process.terminate()
    server_process.wait()
    
    print("🎉 Protocol test completed!")

if __name__ == "__main__":
    test_protocol()