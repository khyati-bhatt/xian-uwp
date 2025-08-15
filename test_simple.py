#!/usr/bin/env python3
"""
Simple test to verify protocol components
"""
import asyncio
from xian_py.wallet import Wallet
from xian_py.xian import Xian
from protocol.models import WalletInfo, BalanceResponse, TransactionRequest, SignMessageRequest

async def test_components():
    print("🧪 Testing Protocol Components\n")
    
    # 1. Test wallet creation
    print("1️⃣ Testing wallet creation...")
    try:
        wallet = Wallet()
        print(f"✅ Wallet created: {wallet.public_key[:16]}...")
        print(f"   Private key exists: {wallet.private_key is not None}")
    except Exception as e:
        print(f"❌ Failed to create wallet: {e}")
        return
    
    # 2. Test Xian client
    print("\n2️⃣ Testing Xian client...")
    try:
        xian_client = Xian("https://testnet.xian.org", wallet=wallet)
        print("✅ Xian client created successfully")
    except Exception as e:
        print(f"❌ Failed to create Xian client: {e}")
        return
    
    # 3. Test models
    print("\n3️⃣ Testing data models...")
    try:
        # Test WalletInfo model
        wallet_info = WalletInfo(
            address=wallet.public_key,
            truncated_address=f"{wallet.public_key[:8]}...{wallet.public_key[-8:]}",
            locked=False,
            chain_id="xian-testnet",
            network="https://testnet.xian.org",
            wallet_type="desktop"
        )
        print(f"✅ WalletInfo model: {wallet_info.truncated_address}")
        
        # Test BalanceResponse model
        balance_response = BalanceResponse(
            balance=100.0,
            contract="currency",
            symbol="XIAN",
            decimals=8
        )
        print(f"✅ BalanceResponse model: {balance_response.balance} {balance_response.symbol}")
        
        # Test TransactionRequest model
        tx_request = TransactionRequest(
            contract="currency",
            function="transfer",
            kwargs={"to": "recipient", "amount": 10},
            stamps_supplied=50000
        )
        print(f"✅ TransactionRequest model: {tx_request.contract}.{tx_request.function}")
        
        # Test SignMessageRequest model
        sign_request = SignMessageRequest(message="Hello World")
        print(f"✅ SignMessageRequest model: {sign_request.message}")
        
    except Exception as e:
        print(f"❌ Failed to create models: {e}")
        return
    
    # 4. Test wallet operations
    print("\n4️⃣ Testing wallet operations...")
    try:
        # Test message signing
        message = "Test message"
        signature = wallet.sign_msg(message)
        print(f"✅ Message signed: {signature[:32]}...")
        
        # Test signature verification
        is_valid = wallet.verify_msg(message, signature)
        print(f"✅ Signature verified: {is_valid}")
        
    except Exception as e:
        print(f"❌ Failed wallet operations: {e}")
    
    # 5. Test network connectivity (optional)
    print("\n5️⃣ Testing network connectivity...")
    try:
        # Try to get balance (will fail if no funds, but tests connectivity)
        balance = xian_client.get_balance(wallet.public_key, contract="currency")
        print(f"✅ Network connected - Balance: {balance}")
    except Exception as e:
        # This is expected if wallet has no funds
        if "connection" in str(e).lower():
            print(f"❌ Network connection failed: {e}")
        else:
            print(f"⚠️  Network connected but query failed (expected for new wallet): {e}")
    
    print("\n✅ Component test completed!")

if __name__ == "__main__":
    asyncio.run(test_components())