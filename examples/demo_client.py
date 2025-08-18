#!/usr/bin/env python3
"""
Demo Client Example
Shows how to properly connect to a wallet server and wait for authorization
"""

import asyncio
from xian_uwp.client import WalletProtocolClient
from xian_uwp.models import Permission


async def demo_client():
    """Demo client that properly waits for authorization"""
    
    # Create client
    client = WalletProtocolClient(
        app_name="Demo DApp",
        app_url="https://demo-dapp.com",
        permissions=[Permission.WALLET_INFO, Permission.TRANSACTIONS, Permission.SIGN_MESSAGE]
    )
    
    print("🔗 Connecting to wallet...")
    print("   This will wait for user approval in the wallet interface")
    print("   (In a real wallet, the user would see a popup/notification)")
    
    try:
        # Connect (this will wait for user approval)
        success = await client.connect()
        
        if success:
            print("✅ Connected successfully!")
            
            # Get wallet info
            wallet_info = await client.get_wallet_info()
            print(f"   Wallet: {wallet_info.public_key}")
            print(f"   Type: {wallet_info.wallet_type}")
            
            # Get balance
            balance = await client.get_balance()
            print(f"   Balance: {balance.balance} XIAN")
            
        else:
            print("❌ Connection failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await client.disconnect()
        print("🔌 Disconnected")


def main():
    """Run the demo client"""
    asyncio.run(demo_client())


if __name__ == "__main__":
    main()