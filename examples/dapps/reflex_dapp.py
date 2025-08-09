# examples/dapps/reflex_dapp.py
"""
Reflex DApp Example - Xian Universal Protocol
Example DApp built with Reflex that connects to any Xian wallet type
"""

import reflex as rx
from typing import Optional

# Import the universal protocol client
from protocol.client import XianWalletClientSync, WalletProtocolError
from protocol.models import WalletInfo, TransactionResult, WalletType


class WalletState(rx.State):
    """The wallet DApp state."""

    # Connection state
    is_connected: bool = False
    connection_status: str = "Not Connected"
    status_color: str = "red"

    # Wallet info
    wallet_address: str = "No wallet connected"
    wallet_type: str = "Unknown"
    wallet_balance: str = "0"

    # Transaction form
    recipient_address: str = ""
    send_amount: str = ""

    # Message signing
    message_to_sign: str = ""
    signature_result: str = ""

    # Activity log
    activity_log: list[str] = []

    # Loading states
    connecting: bool = False
    sending_transaction: bool = False
    signing_message: bool = False
    refreshing_balance: bool = False

    # Internal client (not a state var since it's not serializable)
    _client: Optional[XianWalletClientSync] = None

    def log_activity(self, message: str, level: str = "info"):
        """Add message to activity log"""
        timestamp = rx.moment().format("HH:mm:ss")

        if level == "error":
            icon = "❌"
        elif level == "success":
            icon = "✅"
        elif level == "warning":
            icon = "⚠️"
        else:
            icon = "ℹ️"

        log_entry = f"[{timestamp}] {icon} {message}"
        self.activity_log = [log_entry] + self.activity_log[:19]  # Keep last 20 entries

    async def connect_wallet(self):
        """Connect to any available Xian wallet"""
        self.connecting = True
        yield

        try:
            self.log_activity("Connecting to any available Xian wallet...", "info")

            # Create universal client
            self._client = XianWalletClientSync(
                app_name="Reflex DApp Example",
                app_url="http://localhost:3000"
            )

            # Connect to any wallet type
            success = self._client.connect(auto_approve=False)

            if success:
                # Get wallet info
                wallet_info = self._client.get_wallet_info()

                # Update state
                self.is_connected = True
                self.connection_status = "Connected"
                self.status_color = "green"
                self.wallet_address = wallet_info.truncated_address
                self.wallet_type = f"{wallet_info.wallet_type.value.title()} Wallet"

                # Get initial balance
                await self.refresh_balance_internal()

                self.log_activity(f"Connected to {wallet_info.wallet_type.value} wallet!", "success")
                self.log_activity(f"Address: {wallet_info.address}", "info")

            else:
                self.log_activity("Failed to connect to wallet", "error")
                self.log_activity("Make sure a Xian wallet is running on port 8545", "warning")

        except WalletProtocolError as e:
            self.log_activity(f"Connection failed: {str(e)}", "error")
            if "not available" in str(e):
                self.log_activity("Start a Xian wallet (desktop, web, or CLI)", "warning")

            self.connection_status = "Failed"
            self.status_color = "red"

        except Exception as e:
            self.log_activity(f"Unexpected error: {str(e)}", "error")

        finally:
            self.connecting = False
            yield

    async def disconnect_wallet(self):
        """Disconnect from wallet"""
        try:
            if self._client:
                self._client.disconnect()
                self._client = None

            # Reset state
            self.is_connected = False
            self.connection_status = "Not Connected"
            self.status_color = "red"
            self.wallet_address = "No wallet connected"
            self.wallet_type = "Unknown"
            self.wallet_balance = "0"

            self.log_activity("Disconnected from wallet", "warning")

        except Exception as e:
            self.log_activity(f"Disconnect error: {str(e)}", "error")

    async def refresh_balance(self):
        """Refresh wallet balance"""
        self.refreshing_balance = True
        yield

        await self.refresh_balance_internal()

        self.refreshing_balance = False
        yield

    async def refresh_balance_internal(self):
        """Internal balance refresh method"""
        try:
            if not self._client:
                self.log_activity("No wallet connected", "error")
                return

            self.log_activity("Refreshing balance...", "info")
            balance = self._client.get_balance("currency")
            self.wallet_balance = str(balance)
            self.log_activity(f"Balance: {balance} XIAN", "success")

        except Exception as e:
            self.log_activity(f"Failed to get balance: {str(e)}", "error")

    async def send_transaction(self):
        """Send transaction through connected wallet"""
        if not self.recipient_address or not self.send_amount:
            return rx.window_alert("Please enter recipient and amount")

        self.sending_transaction = True
        yield

        try:
            if not self._client:
                self.log_activity("No wallet connected", "error")
                return

            try:
                amount = float(self.send_amount)
            except ValueError:
                self.log_activity("Invalid amount format", "error")
                return

            self.log_activity(f"Sending {amount} XIAN to {self.recipient_address[:8]}...", "info")
            self.log_activity(f"Using {self.wallet_type.lower()}", "info")

            result = self._client.send_transaction(
                contract="currency",
                function="transfer",
                kwargs={
                    "to": self.recipient_address,
                    "amount": amount
                }
            )

            if result.success:
                self.log_activity("Transaction sent successfully!", "success")
                if result.transaction_hash:
                    self.log_activity(f"TX Hash: {result.transaction_hash}", "info")

                # Clear form and refresh balance
                self.recipient_address = ""
                self.send_amount = ""
                await self.refresh_balance_internal()
            else:
                errors = ', '.join(result.errors or ['Unknown error'])
                self.log_activity(f"Transaction failed: {errors}", "error")

        except Exception as e:
            self.log_activity(f"Transaction error: {str(e)}", "error")

        finally:
            self.sending_transaction = False
            yield

    async def sign_message(self):
        """Sign message with connected wallet"""
        if not self.message_to_sign:
            return rx.window_alert("Please enter a message to sign")

        self.signing_message = True
        yield

        try:
            if not self._client:
                self.log_activity("No wallet connected", "error")
                return

            self.log_activity("Signing message...", "info")
            self.log_activity(f"Using {self.wallet_type.lower()}", "info")

            signature = self._client.sign_message(self.message_to_sign)

            self.signature_result = signature
            self.log_activity("Message signed successfully!", "success")
            self.log_activity(f"Signature: {signature[:32]}...", "info")

        except Exception as e:
            self.log_activity(f"Failed to sign message: {str(e)}", "error")

        finally:
            self.signing_message = False
            yield


def connection_section() -> rx.Component:
    """Wallet connection section"""
    return rx.card(
        rx.vstack(
            rx.heading("Universal Wallet Connection", size="6"),
            rx.text(
                "This DApp works with ANY Xian wallet type: Desktop, Web, or CLI",
                color="gray",
                size="2"
            ),
            rx.divider(),

            # Status info
            rx.hstack(
                rx.text("Status:", weight="bold"),
                rx.badge(
                    WalletState.connection_status,
                    color_scheme=rx.cond(
                        WalletState.status_color == "green",
                        "green",
                        rx.cond(
                            WalletState.status_color == "red",
                            "red",
                            "yellow"
                        )
                    )
                ),
                align="center",
                spacing="2"
            ),

            rx.hstack(
                rx.text("Wallet Type:", weight="bold"),
                rx.text(WalletState.wallet_type),
                align="center",
                spacing="2"
            ),

            rx.hstack(
                rx.text("Address:", weight="bold"),
                rx.text(WalletState.wallet_address),
                align="center",
                spacing="2"
            ),

            rx.hstack(
                rx.text("Balance:", weight="bold"),
                rx.text(WalletState.wallet_balance),
                rx.text("XIAN"),
                align="center",
                spacing="2"
            ),

            # Action buttons
            rx.hstack(
                rx.button(
                    "Connect Any Wallet",
                    on_click=WalletState.connect_wallet,
                    color_scheme="blue",
                    size="2",
                    disabled=WalletState.connecting,
                    loading=WalletState.connecting
                ),
                rx.button(
                    "Disconnect",
                    on_click=WalletState.disconnect_wallet,
                    color_scheme="red",
                    variant="outline",
                    size="2",
                    disabled=~WalletState.is_connected
                ),
                rx.button(
                    "Refresh Balance",
                    on_click=WalletState.refresh_balance,
                    color_scheme="green",
                    variant="outline",
                    size="2",
                    disabled=~WalletState.is_connected,
                    loading=WalletState.refreshing_balance
                ),
                spacing="3"
            ),

            spacing="4",
            align="stretch"
        ),
        width="100%"
    )


def transaction_section() -> rx.Component:
    """Transaction section"""
    return rx.card(
        rx.vstack(
            rx.heading("Universal Transaction", size="6"),
            rx.text(
                "Send transactions through any connected wallet type",
                color="gray",
                size="2"
            ),
            rx.divider(),

            rx.hstack(
                rx.input(
                    placeholder="Recipient address...",
                    value=WalletState.recipient_address,
                    on_change=WalletState.set_recipient_address,
                    width="100%"
                ),
                rx.input(
                    placeholder="Amount...",
                    value=WalletState.send_amount,
                    on_change=WalletState.set_send_amount,
                    type="number",
                    width="200px"
                ),
                spacing="3",
                width="100%"
            ),

            rx.button(
                "Send XIAN",
                on_click=WalletState.send_transaction,
                color_scheme="green",
                size="2",
                disabled=~WalletState.is_connected,
                loading=WalletState.sending_transaction,
                width="100%"
            ),

            spacing="4",
            align="stretch"
        ),
        width="100%"
    )


def signing_section() -> rx.Component:
    """Message signing section"""
    return rx.card(
        rx.vstack(
            rx.heading("Universal Message Signing", size="6"),
            rx.text(
                "Sign messages with any wallet type using the same interface",
                color="gray",
                size="2"
            ),
            rx.divider(),

            rx.text_area(
                placeholder="Enter message to sign...",
                value=WalletState.message_to_sign,
                on_change=WalletState.set_message_to_sign,
                width="100%",
                height="100px"
            ),

            rx.button(
                "Sign Message",
                on_click=WalletState.sign_message,
                color_scheme="purple",
                size="2",
                disabled=~WalletState.is_connected,
                loading=WalletState.signing_message,
                width="100%"
            ),

            rx.cond(
                WalletState.signature_result,
                rx.vstack(
                    rx.text("Signature:", weight="bold"),
                    rx.text_area(
                        value=WalletState.signature_result,
                        read_only=True,
                        width="100%",
                        height="80px"
                    ),
                    spacing="2",
                    align="stretch"
                )
            ),

            spacing="4",
            align="stretch"
        ),
        width="100%"
    )


def compatibility_section() -> rx.Component:
    """Wallet compatibility info"""
    return rx.card(
        rx.vstack(
            rx.heading("Wallet Compatibility", size="6"),
            rx.text("This DApp is compatible with:", weight="bold", color="gray"),

            rx.vstack(
                rx.hstack(
                    rx.icon("monitor", color="blue"),
                    rx.text("Desktop Wallets (Flet-based GUI)"),
                    align="center",
                    spacing="2"
                ),
                rx.hstack(
                    rx.icon("globe", color="green"),
                    rx.text("Web Wallets (Browser-based Flet apps)"),
                    align="center",
                    spacing="2"
                ),
                rx.hstack(
                    rx.icon("terminal", color="orange"),
                    rx.text("CLI Wallets (Command-line daemon)"),
                    align="center",
                    spacing="2"
                ),
                rx.hstack(
                    rx.icon("cpu", color="purple"),
                    rx.text("Hardware Wallets (via protocol adapters)"),
                    align="center",
                    spacing="2"
                ),
                spacing="3",
                align="start"
            ),

            rx.divider(),
            rx.text(
                "All wallet types expose the same API on localhost:8545",
                size="1",
                color="gray",
                style={"font-style": "italic"}
            ),

            spacing="4",
            align="stretch"
        ),
        width="100%"
    )


def activity_log_section() -> rx.Component:
    """Activity log section"""
    return rx.card(
        rx.vstack(
            rx.heading("Activity Log", size="6"),
            rx.divider(),

            rx.scroll_area(
                rx.vstack(
                    rx.foreach(
                        WalletState.activity_log,
                        lambda log_entry: rx.text(
                            log_entry,
                            font_family="mono",
                            size="1",
                            white_space="pre-wrap"
                        )
                    ),
                    spacing="1",
                    align="start"
                ),
                height="300px",
                width="100%"
            ),

            spacing="4",
            align="stretch"
        ),
        width="100%"
    )


def index() -> rx.Component:
    """Main page of the Reflex DApp"""
    return rx.container(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon("link", size=32, color="purple"),
                rx.heading("Universal Xian DApp", size="8"),
                rx.spacer(),
                rx.badge("Reflex Example", color_scheme="purple", variant="outline"),
                align="center",
                spacing="3",
                width="100%"
            ),

            rx.text(
                "Built with Reflex - Works with ANY Xian wallet type",
                color="gray",
                size="3",
                text_align="center"
            ),

            rx.divider(),

            # Main content in responsive grid
            rx.grid(
                # Left column
                rx.vstack(
                    connection_section(),
                    transaction_section(),
                    signing_section(),
                    spacing="6",
                    align="stretch"
                ),

                # Right column
                rx.vstack(
                    compatibility_section(),
                    activity_log_section(),
                    spacing="6",
                    align="stretch"
                ),

                columns="2",
                spacing="6",
                width="100%"
            ),

            # Footer
            rx.divider(),
            rx.hstack(
                rx.text("Powered by", color="gray", size="1"),
                rx.link(
                    "Xian Universal Protocol",
                    href="#",
                    color="purple",
                    size="1"
                ),
                rx.text("•", color="gray", size="1"),
                rx.link(
                    "Built with Reflex",
                    href="https://reflex.dev",
                    color="purple",
                    size="1"
                ),
                align="center",
                spacing="2",
                justify="center"
            ),

            spacing="8",
            align="stretch",
            width="100%",
            padding="4"
        ),
        max_width="1200px",
        margin="0 auto"
    )


# Create the app
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        accent_color="purple"
    )
)

# Add the page
app.add_page(
    index,
    title="Universal Xian DApp - Reflex Example",
    description="Example DApp built with Reflex that works with any Xian wallet type"
)

if __name__ == "__main__":
    # This runs the dev server
    print("🚀 Starting Reflex DApp Example...")
    print("🔗 This DApp works with ANY Xian wallet type:")
    print("   📱 Desktop wallets (GUI applications)")
    print("   🌐 Web wallets (browser-based Flet apps)")
    print("   💻 CLI wallets (command-line daemons)")
    print("   🔧 Hardware wallets (via adapters)")
    print()
    print("💡 Make sure a Xian wallet is running on port 8545")
    print("🌐 DApp will be available at http://localhost:3000")
    print("⚡ Run with: reflex run")