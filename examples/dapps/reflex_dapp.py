# examples/dapps/reflex_dapp.py
# Requires: pip install reflex>=0.8.6

import reflex as rx
from typing import Optional
from protocol.client import XianWalletClientSync


# State is now a simple Python class (not Pydantic)
class WalletState(rx.State):
    """DApp state for wallet integration"""

    # Connection state
    is_connected: bool = False
    wallet_address: str = "No wallet connected"
    truncated_address: str = ""
    wallet_type: str = ""

    # Transaction state
    recipient: str = ""
    amount: str = ""
    transaction_result: str = ""

    # Balance
    balance: float = 0.0

    # Loading states
    connecting: bool = False
    sending: bool = False

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
                permissions=["wallet_info", "balance", "transactions"]
            )

            success = self._client.connect()
            if success:
                info = self._client.get_wallet_info()
                self.is_connected = True
                self.wallet_address = info.address
                self.truncated_address = info.truncated_address
                self.wallet_type = info.wallet_type

                # Get balance
                balance_info = self._client.get_balance("currency")
                self.balance = balance_info.balance

                self.transaction_result = "✅ Wallet connected successfully"
            else:
                self.transaction_result = "❌ Failed to connect to wallet"
        except Exception as e:
            self.transaction_result = f"❌ Connection error: {str(e)}"
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
        self.transaction_result = "Wallet disconnected"

    def send_transaction(self):
        """Send a transaction"""
        if not self.is_connected or not self._client:
            self.transaction_result = "❌ Wallet not connected"
            return

        if not self.recipient or not self.amount:
            self.transaction_result = "❌ Please fill in recipient and amount"
            return

        self.sending = True
        yield  # Update UI to show loading

        try:
            amount_val = float(self.amount)
            result = self._client.send_transaction(
                contract="currency",
                function="transfer",
                kwargs={"to": self.recipient, "amount": amount_val},
                stamps_supplied=50000
            )

            if result.success:
                self.transaction_result = f"✅ Transaction successful: {result.transaction_hash}"
                # Update balance
                balance_info = self._client.get_balance("currency")
                self.balance = balance_info.balance
                # Clear form
                self.recipient = ""
                self.amount = ""
            else:
                self.transaction_result = f"❌ Transaction failed: {result.errors}"
        except ValueError:
            self.transaction_result = "❌ Invalid amount"
        except Exception as e:
            self.transaction_result = f"❌ Transaction error: {str(e)}"
        finally:
            self.sending = False

    def set_recipient(self, value: str):
        self.recipient = value

    def set_amount(self, value: str):
        self.amount = value


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


def transaction_card() -> rx.Component:
    """Transaction form card"""
    return rx.card(
        rx.vstack(
            rx.heading("Send Transaction", size="4"),
            rx.cond(
                WalletState.is_connected,
                rx.vstack(
                    rx.input(
                        placeholder="Recipient address",
                        value=WalletState.recipient,
                        on_change=WalletState.set_recipient,
                        width="100%"
                    ),
                    rx.input(
                        placeholder="Amount",
                        value=WalletState.amount,
                        on_change=WalletState.set_amount,
                        width="100%"
                    ),
                    rx.button(
                        "Send Transaction",
                        on_click=WalletState.send_transaction,
                        loading=WalletState.sending,
                        color_scheme="green",
                        size="3",
                        width="100%"
                    ),
                    spacing="3"
                ),
                rx.text("Connect wallet to send transactions", color="gray")
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
                WalletState.transaction_result != "",
                rx.text(WalletState.transaction_result),
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
                "This DApp works with Desktop, CLI, and Web wallets",
                text_align="center",
                color="gray",
                margin_bottom="2rem"
            ),
            rx.hstack(
                wallet_connection_card(),
                transaction_card(),
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
    ),
    disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"]
)

# Add the page
app.add_page(index, route="/")

# For Reflex, you typically run with: reflex run
# But for this example to work with python -m, we'll use a simple approach
if __name__ == "__main__":
    print("Reflex DApp configured. To run properly, use: reflex run")
    print("Or use the universal_dapp.py example instead.")
