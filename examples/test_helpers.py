#!/usr/bin/env python3
"""
Test Helpers for Examples
Provides testing utilities like auto-approval for development/testing
"""

import asyncio
import httpx
from xian_uwp.models import Endpoints


class TestWalletHelper:
    """Helper class for testing wallet interactions"""
    
    def __init__(self, server_url: str = "http://localhost:8545"):
        self.server_url = server_url
    
    async def auto_approve_pending_requests(self):
        """Auto-approve all pending authorization requests (for testing only)"""
        async with httpx.AsyncClient() as client:
            try:
                # Get pending requests (this would need to be implemented in server)
                response = await client.get(f"{self.server_url}/api/v1/auth/pending")
                if response.status_code == 200:
                    pending = response.json()
                    
                    for request in pending.get("requests", []):
                        request_id = request["request_id"]
                        approve_endpoint = Endpoints.AUTH_APPROVE.replace("{request_id}", request_id)
                        
                        await client.post(f"{self.server_url}{approve_endpoint}")
                        print(f"✅ Auto-approved request: {request_id}")
                        
            except Exception as e:
                print(f"⚠️  Auto-approval failed: {e}")
    
    async def start_auto_approval_loop(self, interval: float = 1.0):
        """Start a background loop that auto-approves requests (for testing only)"""
        print("🤖 Starting auto-approval loop for testing...")
        
        while True:
            await self.auto_approve_pending_requests()
            await asyncio.sleep(interval)


async def create_test_client_with_auto_approval(app_name: str, permissions: list):
    """Create a client and start auto-approval for testing"""
    from xian_uwp.client import WalletProtocolClient
    
    # Start auto-approval in background
    helper = TestWalletHelper()
    auto_approval_task = asyncio.create_task(helper.start_auto_approval_loop())
    
    # Create client
    client = WalletProtocolClient(
        app_name=app_name,
        permissions=permissions
    )
    
    try:
        # Connect (will be auto-approved)
        success = await client.connect()
        return client, auto_approval_task
    except Exception as e:
        auto_approval_task.cancel()
        raise e


# Example usage
async def demo_with_auto_approval():
    """Demo showing how to use auto-approval for testing"""
    client, auto_task = await create_test_client_with_auto_approval(
        "Test DApp", 
        ["wallet_info", "balance"]
    )
    
    try:
        # Use client normally
        info = await client.get_wallet_info()
        print(f"Connected to: {info.public_key}")
        
    finally:
        auto_task.cancel()
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(demo_with_auto_approval())