#!/usr/bin/env python3
"""
Demonstration of robust server startup functionality

This example shows how the Xian Universal Wallet Protocol handles:
- Port conflicts from killed processes
- Unresponsive servers on the same port
- Automatic cleanup and retry
- Both sync and async startup modes
"""

import asyncio
import time
from xian_uwp import create_server, WalletType


def demo_basic_robust_startup():
    """Demonstrate basic robust startup"""
    print("🚀 Basic Robust Startup Demo")
    print("-" * 40)
    
    server = create_server(wallet_type=WalletType.DESKTOP)
    
    print("Starting server with robust startup...")
    print("This will:")
    print("  1. Check if port 8545 is available")
    print("  2. If in use, check if existing server is responsive")
    print("  3. If unresponsive, clean up and start new server")
    print("  4. Retry up to 3 times if needed")
    
    try:
        # This method handles all the robustness automatically
        server.run_robust(host="127.0.0.1", port=8545, max_retries=3)
    except KeyboardInterrupt:
        print("\n✅ Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")


async def demo_async_robust_startup():
    """Demonstrate async robust startup"""
    print("\n🚀 Async Robust Startup Demo")
    print("-" * 40)
    
    server = create_server(wallet_type=WalletType.DESKTOP)
    
    print("Starting server with async robust startup...")
    
    try:
        # Start server with robust startup
        await server.start_async_robust(host="127.0.0.1", port=8546, max_retries=3)
        
        print("✅ Server started successfully!")
        print("Server is running in background...")
        
        # Keep running for a few seconds
        await asyncio.sleep(3)
        
        # Stop server
        await server.stop_async()
        print("✅ Server stopped cleanly")
        
    except Exception as e:
        print(f"❌ Async server failed: {e}")


def demo_manual_conflict_handling():
    """Demonstrate manual conflict handling"""
    print("\n🛠️ Manual Conflict Handling Demo")
    print("-" * 40)
    
    server = create_server(wallet_type=WalletType.DESKTOP)
    
    print("This shows the individual steps of robust startup:")
    
    # You can also handle conflicts manually if needed
    try:
        # First attempt - normal startup
        print("1. Attempting normal startup...")
        server.run(host="127.0.0.1", port=8547)
        
    except Exception as e:
        print(f"   Normal startup failed: {e}")
        
        try:
            # Second attempt - with force cleanup
            print("2. Attempting startup with force cleanup...")
            server.run(host="127.0.0.1", port=8547, force_cleanup=True)
            
        except KeyboardInterrupt:
            print("\n✅ Server stopped by user")
        except Exception as e:
            print(f"   Force cleanup startup failed: {e}")


def main():
    """Main demo function"""
    print("🛡️ Xian Universal Wallet Protocol - Robust Startup Demo")
    print("=" * 60)
    print()
    print("This demo shows how the protocol handles server startup")
    print("robustly, even when processes are killed or ports are")
    print("already in use.")
    print()
    
    choice = input("Choose demo:\n"
                  "1. Basic robust startup (sync)\n"
                  "2. Async robust startup\n"
                  "3. Manual conflict handling\n"
                  "4. All demos\n"
                  "Enter choice (1-4): ").strip()
    
    if choice == "1":
        demo_basic_robust_startup()
    elif choice == "2":
        asyncio.run(demo_async_robust_startup())
    elif choice == "3":
        demo_manual_conflict_handling()
    elif choice == "4":
        print("\n🎬 Running all demos...")
        demo_basic_robust_startup()
        asyncio.run(demo_async_robust_startup())
        demo_manual_conflict_handling()
    else:
        print("Invalid choice. Running basic demo...")
        demo_basic_robust_startup()
    
    print("\n" + "=" * 60)
    print("🎉 Demo completed!")
    print()
    print("Key benefits of robust startup:")
    print("✅ Handles killed wallet processes automatically")
    print("✅ Cleans up stale servers on the same port")
    print("✅ Retries with increasing force if needed")
    print("✅ Works with both sync and async modes")
    print("✅ No manual intervention required")
    print()
    print("Your wallet will now start reliably even after crashes!")


if __name__ == "__main__":
    main()