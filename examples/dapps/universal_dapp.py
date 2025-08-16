# examples/dapps/universal_dapp.py
# Requires: pip install flet>=0.28.3

import flet as ft
from protocol.client import XianWalletClientSync


class UniversalDApp:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.wallet_info = None
        self.balance = 0.0

    def connect_wallet(self):
        """Connect to any available wallet"""
        try:
            self.client = XianWalletClientSync(
                app_name="Universal DApp Demo",
                app_url="http://localhost:8080",
                permissions=["wallet_info", "balance", "transactions", "sign_message"]
            )

            success = self.client.connect()
            if success:
                self.wallet_info = self.client.get_wallet_info()
                balance_info = self.client.get_balance("currency")
                self.balance = balance_info.balance
                self.is_connected = True
                return True
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def disconnect_wallet(self):
        """Disconnect from wallet"""
        self.client = None
        self.is_connected = False
        self.wallet_info = None
        self.balance = 0.0

    def send_transaction(self, recipient, amount):
        """Send a transaction"""
        if not self.is_connected or not self.client:
            return {"success": False, "error": "Wallet not connected"}

        try:
            result = self.client.send_transaction(
                contract="currency",
                function="transfer",
                kwargs={"to": recipient, "amount": float(amount)},
                stamps_supplied=50000
            )

            if result.success:
                # Update balance after transaction
                balance_info = self.client.get_balance("currency")
                self.balance = balance_info.balance

            return {
                "success": result.success,
                "hash": result.transaction_hash if result.success else None,
                "error": result.errors if not result.success else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def sign_message(self, message):
        """Sign a message"""
        if not self.is_connected or not self.client:
            return {"success": False, "error": "Wallet not connected"}

        try:
            result = self.client.sign_message(message)
            return {
                "success": True,
                "signature": result.signature,
                "signer": result.signer
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


def main(page: ft.Page):
    page.title = "Universal Xian DApp"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 900
    page.window.height = 700
    page.window.center()
    page.scroll = ft.ScrollMode.AUTO

    dapp = UniversalDApp()

    # UI Components
    connection_status = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.WIFI_OFF, color=ft.Colors.RED_400),
            ft.Text("Not Connected", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_600)
        ], alignment=ft.MainAxisAlignment.CENTER),
        padding=15,
        border_radius=10,
        bgcolor=ft.Colors.RED_50,
        border=ft.border.all(2, ft.Colors.RED_200)
    )

    wallet_details = ft.Container(
        content=ft.Text("Connect wallet to view details", color=ft.Colors.GREY_600),
        padding=20,
        border_radius=10,
        bgcolor=ft.Colors.GREY_50,
        visible=False
    )

    # Transaction form
    recipient_field = ft.TextField(
        label="Recipient Address",
        width=400,
        border_color=ft.Colors.BLUE_400
    )

    amount_field = ft.TextField(
        label="Amount (XIAN)",
        width=200,
        border_color=ft.Colors.BLUE_400
    )

    # Message signing
    message_field = ft.TextField(
        label="Message to Sign",
        width=400,
        multiline=True,
        max_lines=3,
        border_color=ft.Colors.PURPLE_400
    )

    # Results area
    results_text = ft.Text(
        "Ready to connect...",
        size=14,
        color=ft.Colors.GREY_700
    )

    def show_notification(message, error=False):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_400 if error else ft.Colors.GREEN_400
        )
        page.snack_bar.open = True
        page.update()

    def connect_wallet_click():
        results_text.value = "Connecting to wallet..."
        page.update()

        success = dapp.connect_wallet()
        if success:
            # Update connection status
            connection_status.content = ft.Row([
                ft.Icon(ft.Icons.WIFI, color=ft.Colors.GREEN_400),
                ft.Text("Connected", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_600)
            ], alignment=ft.MainAxisAlignment.CENTER)
            connection_status.bgcolor = ft.Colors.GREEN_50
            connection_status.border = ft.border.all(2, ft.Colors.GREEN_200)

            # Show wallet details
            wallet_details.content = ft.Column([
                ft.Text("Wallet Information", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(f"Address: {dapp.wallet_info.truncated_address}", size=14),
                ft.Text(f"Full Address: {dapp.wallet_info.address}", size=12, color=ft.Colors.GREY_600),
                ft.Text(f"Type: {dapp.wallet_info.wallet_type.title()}", size=14),
                ft.Text(f"Balance: {dapp.balance} XIAN", size=16, color=ft.Colors.GREEN_700, weight=ft.FontWeight.BOLD),
                ft.Text(f"Network: {dapp.wallet_info.network}", size=12, color=ft.Colors.GREY_600),
            ], spacing=5)
            wallet_details.bgcolor = ft.Colors.BLUE_50
            wallet_details.visible = True

            # Update buttons
            connect_btn.visible = False
            disconnect_btn.visible = True

            results_text.value = "✅ Wallet connected successfully!"
            results_text.color = ft.Colors.GREEN_700
            show_notification("Wallet connected successfully!")
        else:
            results_text.value = "❌ Failed to connect to wallet. Make sure a wallet is running on port 8545."
            results_text.color = ft.Colors.RED_700
            show_notification("Connection failed", error=True)

        page.update()

    def disconnect_wallet_click():
        dapp.disconnect_wallet()

        # Reset UI
        connection_status.content = ft.Row([
            ft.Icon(ft.Icons.WIFI_OFF, color=ft.Colors.RED_400),
            ft.Text("Not Connected", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_600)
        ], alignment=ft.MainAxisAlignment.CENTER)
        connection_status.bgcolor = ft.Colors.RED_50
        connection_status.border = ft.border.all(2, ft.Colors.RED_200)

        wallet_details.visible = False
        connect_btn.visible = True
        disconnect_btn.visible = False

        results_text.value = "Wallet disconnected"
        results_text.color = ft.Colors.GREY_700

        page.update()

    def send_transaction_click():
        if not recipient_field.value or not amount_field.value:
            show_notification("Please fill in recipient and amount", error=True)
            return

        results_text.value = "Sending transaction..."
        page.update()

        result = dapp.send_transaction(recipient_field.value, amount_field.value)

        if result["success"]:
            results_text.value = f"✅ Transaction successful!\nHash: {result['hash']}\nNew Balance: {dapp.balance} XIAN"
            results_text.color = ft.Colors.GREEN_700
            recipient_field.value = ""
            amount_field.value = ""

            # Update balance display
            if wallet_details.visible:
                wallet_details.content.controls[4].value = f"Balance: {dapp.balance} XIAN"

            show_notification("Transaction sent successfully!")
        else:
            results_text.value = f"❌ Transaction failed: {result['error']}"
            results_text.color = ft.Colors.RED_700
            show_notification("Transaction failed", error=True)

        page.update()

    def sign_message_click():
        if not message_field.value:
            show_notification("Please enter a message to sign", error=True)
            return

        results_text.value = "Signing message..."
        page.update()

        result = dapp.sign_message(message_field.value)

        if result["success"]:
            results_text.value = f"✅ Message signed!\nSignature: {result['signature'][:50]}...\nSigner: {result['signer']}"
            results_text.color = ft.Colors.GREEN_700
            show_notification("Message signed successfully!")
        else:
            results_text.value = f"❌ Signing failed: {result['error']}"
            results_text.color = ft.Colors.RED_700
            show_notification("Signing failed", error=True)

        page.update()

    # Buttons
    connect_btn = ft.ElevatedButton(
        "Connect Wallet",
        on_click=lambda _: connect_wallet_click(),
        bgcolor=ft.Colors.BLUE_400,
        color=ft.Colors.WHITE,
        width=200
    )

    disconnect_btn = ft.ElevatedButton(
        "Disconnect",
        on_click=lambda _: disconnect_wallet_click(),
        bgcolor=ft.Colors.RED_400,
        color=ft.Colors.WHITE,
        width=200,
        visible=False
    )

    # Layout
    page.add(
        ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Column([
                        ft.Text("Universal Xian DApp", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text("Works with Desktop, CLI, and Web wallets", size=14, color=ft.Colors.WHITE70)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.BLUE_600,
                    padding=20,
                    border_radius=ft.border_radius.only(top_left=10, top_right=10)
                ),

                # Connection section
                ft.Container(
                    content=ft.Column([
                        ft.Text("Wallet Connection", size=20, weight=ft.FontWeight.BOLD),
                        connection_status,
                        ft.Row([connect_btn, disconnect_btn], alignment=ft.MainAxisAlignment.CENTER),
                        wallet_details
                    ], spacing=15),
                    padding=20
                ),

                ft.Divider(),

                # Transaction section
                ft.Container(
                    content=ft.Column([
                        ft.Text("Send Transaction", size=20, weight=ft.FontWeight.BOLD),
                        ft.Row([recipient_field, amount_field], spacing=20),
                        ft.ElevatedButton(
                            "Send Transaction",
                            on_click=lambda _: send_transaction_click(),
                            bgcolor=ft.Colors.GREEN_400,
                            color=ft.Colors.WHITE,
                            disabled=not dapp.is_connected
                        )
                    ], spacing=15),
                    padding=20
                ),

                ft.Divider(),

                # Message signing section
                ft.Container(
                    content=ft.Column([
                        ft.Text("Sign Message", size=20, weight=ft.FontWeight.BOLD),
                        message_field,
                        ft.ElevatedButton(
                            "Sign Message",
                            on_click=lambda _: sign_message_click(),
                            bgcolor=ft.Colors.PURPLE_400,
                            color=ft.Colors.WHITE,
                            disabled=not dapp.is_connected
                        )
                    ], spacing=15),
                    padding=20
                ),

                ft.Divider(),

                # Results section
                ft.Container(
                    content=ft.Column([
                        ft.Text("Results", size=18, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=results_text,
                            padding=15,
                            border_radius=8,
                            bgcolor=ft.Colors.GREY_100,
                            border=ft.border.all(1, ft.Colors.GREY_300),
                            width=float("inf")
                        )
                    ], spacing=10),
                    padding=20
                )
            ]),
            width=float("inf"),
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300)
        )
    )


# Updated for Flet 0.28.3: Use ft.run
if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8080)
