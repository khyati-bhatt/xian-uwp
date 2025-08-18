#!/usr/bin/env python3
"""
Web DApp Example with CORS Support
Demonstrates how to create a web-based DApp that connects to a local wallet
"""
import logging

import reflex as rx

from typing import Optional
from xian_uwp.client import XianWalletClientSync, WalletProtocolError
from xian_uwp.models import Permission

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebDAppState(rx.State):
    """Web DApp state with CORS-enabled wallet connection"""
    
    # Connection state
    is_connected: bool = False
    wallet_address: str = "No wallet connected"
    truncated_address: str = ""
    wallet_type: str = ""
    connection_status: str = "Disconnected"
    
    # Balance
    balance: float = 0.0
    
    # Loading states
    connecting: bool = False
    refreshing: bool = False
    
    # Error handling
    error_message: str = ""
    
    def __init__(self):
        super().__init__()
        self._client: Optional[XianWalletClientSync] = None
    
    def connect_wallet(self):
        """Connect to local wallet with CORS support"""
        self.connecting = True
        self.error_message = ""
        yield
        
        try:
            # Create client that will connect to local wallet
            # The wallet server should be configured with appropriate CORS settings
            self._client = XianWalletClientSync(
                app_name="Web CORS DApp Example",
                app_url=f"http://localhost:{self.router.page.host.split(':')[-1] if ':' in str(self.router.page.host) else '3000'}",
                server_url="http://localhost:8545",  # Local wallet server
                permissions=[
                    Permission.WALLET_INFO,
                    Permission.BALANCE
                ]
            )
            
            # Attempt connection
            success = self._client.connect()
            
            if success:
                # Get wallet info
                info = self._client.get_wallet_info()
                self.is_connected = True
                self.wallet_address = info.address
                self.truncated_address = info.truncated_address
                self.wallet_type = info.wallet_type.value
                self.connection_status = "Connected"
                
                # Get initial balance
                self.refresh_balance()
                
                logger.info(f"Connected to {self.wallet_type} wallet: {self.truncated_address}")
            else:
                self.error_message = "Failed to connect to wallet. Please ensure wallet is running and unlocked."
                self.connection_status = "Connection Failed"
                
        except WalletProtocolError as e:
            self.error_message = f"Wallet error: {str(e)}"
            self.connection_status = "Error"
            logger.error(f"Wallet connection error: {e}")
        except Exception as e:
            self.error_message = f"Connection error: {str(e)}"
            self.connection_status = "Error"
            logger.error(f"Unexpected error: {e}")
        finally:
            self.connecting = False
            yield
    
    def disconnect_wallet(self):
        """Disconnect from wallet"""
        if self._client:
            try:
                self._client.disconnect()
            except:
                pass
            self._client = None
        
        self.is_connected = False
        self.wallet_address = "No wallet connected"
        self.truncated_address = ""
        self.wallet_type = ""
        self.connection_status = "Disconnected"
        self.balance = 0.0
        self.error_message = ""
    
    def refresh_balance(self):
        """Refresh wallet balance"""
        if not self.is_connected or not self._client:
            return
        
        self.refreshing = True
        yield
        
        try:
            self.balance = self._client.get_balance("currency")
        except Exception as e:
            self.error_message = f"Failed to get balance: {str(e)}"
        finally:
            self.refreshing = False
            yield
    
    def manual_refresh_balance(self):
        """Manually refresh balance from wallet"""
        if not self.is_connected or not self._client:
            self.error_message = "Wallet not connected"
            return
            
        self.refreshing = True
        self.error_message = ""
        yield
        
        try:
            self.refresh_balance()
        except Exception as e:
            self.error_message = f"Failed to refresh balance: {str(e)}"
        finally:
            self.refreshing = False
            yield
    
    def clear_error(self):
        """Clear error message"""
        self.error_message = ""
    



def connection_card() -> rx.Component:
    """Wallet connection card"""
    return rx.card(
        rx.vstack(
            rx.heading("Wallet Connection", size="4"),
            rx.text(f"Status: {WebDAppState.connection_status}"),
            rx.cond(
                WebDAppState.is_connected,
                rx.vstack(
                    rx.text(f"Type: {WebDAppState.wallet_type}"),
                    rx.text(f"Address: {WebDAppState.truncated_address}"),
                    rx.text(f"Balance: {WebDAppState.balance} XIAN"),
                    rx.hstack(
                        rx.button(
                            "Refresh Balance",
                            on_click=WebDAppState.refresh_balance,
                            loading=WebDAppState.refreshing,
                            size="2"
                        ),
                        rx.button(
                            "Disconnect",
                            on_click=WebDAppState.disconnect_wallet,
                            color_scheme="red",
                            size="2"
                        ),
                        spacing="2"
                    ),
                    spacing="2"
                ),
                rx.button(
                    "Connect Wallet",
                    on_click=WebDAppState.connect_wallet,
                    loading=WebDAppState.connecting,
                    size="3"
                )
            ),
            spacing="3"
        ),
        width="100%"
    )


def balance_card() -> rx.Component:
    """Balance display and refresh card"""
    return rx.card(
        rx.vstack(
            rx.heading("Wallet Balance", size="4"),
            rx.cond(
                WebDAppState.is_connected,
                rx.vstack(
                    rx.text(
                        f"{WebDAppState.balance} XIAN",
                        size="6",
                        weight="bold",
                        color="green"
                    ),
                    rx.button(
                        "Refresh Balance",
                        on_click=WebDAppState.manual_refresh_balance,
                        loading=WebDAppState.refreshing,
                        disabled=~WebDAppState.is_connected,
                        color_scheme="blue",
                        size="3",
                        width="100%"
                    ),
                    spacing="3"
                ),
                rx.text("Connect wallet to view balance", color="gray")
            ),
            spacing="3"
        ),
        width="100%"
    )


def error_alert() -> rx.Component:
    """Error message alert"""
    return rx.cond(
        WebDAppState.error_message,
        rx.callout(
            WebDAppState.error_message,
            icon="alert-triangle",
            color_scheme="red",
            size="2",
            width="100%"
        )
    )


def info_card() -> rx.Component:
    """Information card about CORS setup"""
    return rx.card(
        rx.vstack(
            rx.heading("CORS Web DApp Example", size="4"),
            rx.text(
                "This example demonstrates how to create a web-based DApp that connects to a local wallet server with proper CORS configuration to view wallet address and balance.",
                size="2"
            ),
            rx.text("Setup Instructions:", weight="bold", size="2"),
            rx.unordered_list(
                rx.list_item("Start a local wallet server on port 8545"),
                rx.list_item("Ensure the wallet server has CORS enabled for this origin"),
                rx.list_item("Unlock the wallet if required"),
                rx.list_item("Click 'Connect Wallet' to establish connection"),
                size="2"
            ),
            rx.text(
                "The wallet server should be configured with CORSConfig.localhost_dev() or similar to allow connections from this web app.",
                size="2",
                color="gray"
            ),
            spacing="3"
        ),
        width="100%"
    )


def index() -> rx.Component:
    """Main page"""
    return rx.container(
        rx.vstack(
            rx.heading("Xian Web DApp with CORS", size="6", text_align="center"),
            error_alert(),
            info_card(),
            connection_card(),
            balance_card(),
            spacing="4",
            width="100%",
            max_width="600px"
        ),
        padding="4",
        center_content=True
    )


# Create the app
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        scaling="100%"
    )
)

app.add_page(index, route="/")


if __name__ == "__main__":
    # Instructions for running
    print("🌐 Starting Web CORS DApp Example")
    print("📋 Setup Instructions:")
    print("1. Start a wallet server: python -m xian_uwp.server")
    print("2. Ensure wallet is unlocked")
    print("3. Open this web app in your browser")
    print("4. Click 'Connect Wallet' to test CORS functionality")
    print()
    
    # Run the app
    app.run(
        host="0.0.0.0",  # Allow external connections
        port=3000,       # Common web dev port
        reload=True      # Enable hot reload for development
    )