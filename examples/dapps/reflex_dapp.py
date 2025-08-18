# examples/dapps/reflex_dapp.py
# Requires: pip install reflex>=0.8.6

import reflex as rx

from typing import Optional
from xian_uwp.client import XianWalletClientSync


# State is now a simple Python class (not Pydantic)
class WalletState(rx.State):
    """DApp state for wallet integration"""

    # Connection state
    is_connected: bool = False
    wallet_address: str = "No wallet connected"
    truncated_address: str = ""
    wallet_type: str = ""

    # Balance
    balance: float = 0.0
    
    # Status message
    status_message: str = "Ready to connect..."

    # Loading states
    connecting: bool = False

    def __init__(self):
        super().__init__()
        self._client: Optional[XianWalletClientSync] = None

    def connect_wallet(self):
        """Connect to any available wallet"""
        self.connecting = True
        yield  # Update UI to show loading

        try:
            self._client = XianWalletClientSync(
                app_name="Reflex DApp Example",
                app_url="http://localhost:3000",
                permissions=["wallet_info", "balance"]
            )

            success = self._client.connect(auto_approve=True)  # Auto-approve for demo purposes
            if success:
                info = self._client.get_wallet_info()
                self.is_connected = True
                self.wallet_address = info.address
                self.truncated_address = info.truncated_address
                self.wallet_type = info.wallet_type

                # Get balance
                self.balance = self._client.get_balance("currency")

                self.status_message = "✅ Wallet connected successfully"
            else:
                self.status_message = "❌ Failed to connect to wallet"
        except Exception as e:
            self.status_message = f"❌ Connection error: {str(e)}"
        finally:
            self.connecting = False

    def disconnect_wallet(self):
        """Disconnect from wallet"""
        self.is_connected = False
        self.wallet_address = "No wallet connected"
        self.truncated_address = ""
        self.wallet_type = ""
        self.balance = 0.0
        self._client = None
        self.status_message = "Wallet disconnected"

    def refresh_balance(self):
        """Refresh balance from wallet"""
        if self.is_connected and self._client:
            try:
                self.balance = self._client.get_balance("currency")
            except Exception as e:
                print(f"Error refreshing balance: {e}")


def wallet_connection_card() -> rx.Component:
    """Wallet connection status card"""
    return rx.card(
        rx.vstack(
            rx.heading("Wallet Connection", size="4"),
            rx.cond(
                WalletState.is_connected,
                rx.vstack(
                    rx.text(f"Address: {WalletState.truncated_address}", weight="bold"),
                    rx.text(f"Type: {WalletState.wallet_type}"),
                    rx.text(f"Balance: {WalletState.balance} XIAN", color="green"),
                    rx.button(
                        "Disconnect",
                        on_click=WalletState.disconnect_wallet,
                        color_scheme="red",
                        size="2"
                    ),
                    spacing="2"
                ),
                rx.vstack(
                    rx.text("No wallet connected"),
                    rx.button(
                        "Connect Wallet",
                        on_click=WalletState.connect_wallet,
                        loading=WalletState.connecting,
                        color_scheme="blue",
                        size="3"
                    ),
                    spacing="2"
                )
            ),
            spacing="3"
        ),
        width="100%",
        max_width="400px"
    )


def balance_card() -> rx.Component:
    """Balance display and refresh card"""
    return rx.card(
        rx.vstack(
            rx.heading("Wallet Balance", size="4"),
            rx.cond(
                WalletState.is_connected,
                rx.vstack(
                    rx.text(
                        f"{WalletState.balance} XIAN",
                        size="6",
                        weight="bold",
                        color="green"
                    ),
                    rx.button(
                        "Refresh Balance",
                        on_click=WalletState.refresh_balance,
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
        width="100%",
        max_width="400px"
    )


def status_card() -> rx.Component:
    """Status and results card"""
    return rx.card(
        rx.vstack(
            rx.heading("Status", size="4"),
            rx.cond(
                WalletState.status_message != "",
                rx.text(WalletState.status_message),
                rx.text("Ready", color="gray")
            ),
            spacing="2"
        ),
        width="100%",
        max_width="400px"
    )


def index() -> rx.Component:
    """Main page"""
    return rx.container(
        rx.vstack(
            rx.heading(
                "Universal Xian DApp",
                size="6",
                text_align="center",
                margin_bottom="2rem"
            ),
            rx.text(
                "Connect to any Xian wallet and view your address & balance",
                text_align="center",
                color="gray",
                margin_bottom="2rem"
            ),
            rx.hstack(
                wallet_connection_card(),
                balance_card(),
                spacing="4",
                wrap="wrap",
                justify="center"
            ),
            rx.container(height="2rem"),
            status_card(),
            spacing="4",
            align="center"
        ),
        padding="2rem",
        max_width="1200px",
        margin="0 auto"
    )


# Create the app (updated for Reflex 0.8.6)
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        scaling="100%"
    )
)

# Add the page
app.add_page(index, route="/")

# For Reflex, you typically run with: reflex run
# But for this example to work with python -m, we'll use a simple approach
if __name__ == "__main__":
    print("Reflex DApp configured. To run properly, use: reflex run")
    print("Or use the universal_dapp.py example instead.")
