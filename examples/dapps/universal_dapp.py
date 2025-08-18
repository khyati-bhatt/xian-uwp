# examples/dapps/universal_dapp.py
# Requires: pip install flet>=0.28.3
#
# IMPORTANT: This example requires the latest development version of xian-uwp.
# Run with: PYTHONPATH=. python examples/dapps/universal_dapp.py
# Or install development version: pip install -e .

import flet as ft

from xian_uwp.client import XianWalletClientSync


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
                permissions=["wallet_info", "balance"]
            )

            success = self.client.connect()  # Will wait for user approval
            if success:
                self.wallet_info = self.client.get_wallet_info()
                self.balance = self.client.get_balance("currency")
                self.is_connected = True
                return True
            else:
                print("❌ Failed to connect to wallet - make sure a wallet is running on localhost:8545")
                return False
        except ConnectionError as e:
            print(f"❌ Connection error: No wallet found on localhost:8545")
            print("   Make sure to start a wallet (desktop, CLI, or web) first!")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

    def disconnect_wallet(self):
        """Disconnect from wallet"""
        self.client = None
        self.is_connected = False
        self.wallet_info = None
        self.balance = 0.0

    def refresh_balance(self):
        """Refresh balance from wallet"""
        if self.is_connected and self.client:
            try:
                # Refresh wallet info first to get current lock status
                self.wallet_info = self.client.get_wallet_info()
                # Then try to get balance (will fail if wallet is locked)
                self.balance = self.client.get_balance("currency")
                return True
            except Exception as e:
                print(f"Error refreshing balance: {e}")
                # Still update wallet info even if balance fails (e.g., if locked)
                try:
                    self.wallet_info = self.client.get_wallet_info()
                except:
                    pass
                return False
        return False


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
                ft.Text(f"Locked: {'Yes' if dapp.wallet_info.locked else 'No'}", size=14),
                ft.ElevatedButton(
                    "Refresh Balance",
                    on_click=lambda _: refresh_balance_click(),
                    bgcolor=ft.Colors.BLUE_400,
                    color=ft.Colors.WHITE,
                    width=150
                )
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

    def refresh_balance_click():
        """Refresh balance from wallet"""
        if dapp.refresh_balance():
            # Update both balance and lock status display
            if wallet_details.visible and wallet_details.content:
                wallet_details.content.controls[4].value = f"Balance: {dapp.balance} XIAN"
                wallet_details.content.controls[5].value = f"Locked: {'Yes' if dapp.wallet_info.locked else 'No'}"
            results_text.value = f"✅ Balance refreshed: {dapp.balance} XIAN"
            results_text.color = ft.Colors.GREEN_700
            show_notification("Balance refreshed!")
        else:
            # Update lock status even if balance refresh failed
            if wallet_details.visible and wallet_details.content and dapp.wallet_info:
                wallet_details.content.controls[5].value = f"Locked: {'Yes' if dapp.wallet_info.locked else 'No'}"
            results_text.value = "❌ Failed to refresh balance (wallet may be locked)"
            results_text.color = ft.Colors.RED_700
            show_notification("Failed to refresh balance - check if wallet is unlocked", error=True)
        
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
                        ft.Text("Connect to any Xian wallet and view your address & balance", size=14, color=ft.Colors.WHITE70)
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

                # Results section
                ft.Container(
                    content=ft.Column([
                        ft.Text("Status", size=18, weight=ft.FontWeight.BOLD),
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
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080)
