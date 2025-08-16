#!/usr/bin/env python3
"""
Test server that starts unlocked
"""
import asyncio
from xian_uwp.server import WalletProtocolServer
from xian_uwp.models import WalletType
from xian_py.wallet import Wallet
from xian_py.xian import Xian
import hashlib

# Create server
server = WalletProtocolServer(wallet_type=WalletType.DESKTOP)

# Initialize wallet manually before starting
async def init_wallet():
    server.wallet = Wallet()
    server.xian_client = Xian(server.network_url, wallet=server.wallet)
    server.password_hash = hashlib.sha256("demo_password".encode()).hexdigest()
    server.is_locked = False  # Unlock for testing
    print(f"Test wallet initialized: {server.wallet.public_key}")

# Run initialization
asyncio.run(init_wallet())

# Run server
server.run(port=54542)