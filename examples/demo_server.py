#!/usr/bin/env python3
"""
Demo Server Example
Shows how to properly initialize a production-ready wallet server
"""

import asyncio
import hashlib
from xian_py.wallet import Wallet
from xian_uwp.server import WalletProtocolServer
from xian_uwp.models import WalletType, CORSConfig


async def create_demo_server():
    """Create a demo server with proper wallet initialization"""
    
    # Create a demo wallet
    wallet = Wallet()
    print(f"📍 Demo wallet created: {wallet.public_key}")
    
    # Create password hash for demo
    demo_password = "demo_password"
    password_hash = hashlib.sha256(demo_password.encode()).hexdigest()
    
    # Create server with wallet
    server = WalletProtocolServer(
        wallet_type=WalletType.DESKTOP,
        cors_config=CORSConfig.development(),
        network_url="https://testnet.xian.org",
        chain_id="xian-testnet-1",
        wallet=wallet
    )
    
    # Set wallet and password
    server.set_wallet(wallet, password_hash)
    
    # Unlock wallet for demo
    server.unlock_wallet(demo_password)
    
    print("🚀 Demo server ready!")
    print(f"   Wallet: {wallet.public_key}")
    print(f"   Network: https://testnet.xian.org")
    print(f"   Password: {demo_password}")
    print("   Server will run on http://localhost:8545")
    
    return server


def main():
    """Run the demo server"""
    async def run_server():
        server = await create_demo_server()
        server.run()
    
    asyncio.run(run_server())


if __name__ == "__main__":
    main()