# examples/wallets/web.py
# Requires: pip install flet>=0.28.3

import flet as ft
import threading
from protocol.server import WalletProtocolServer
from protocol.models import WalletType


class WebWallet:
    def __init__(self):
        self.server = None
        self.wallet_address = "xian5678...efgh"
        self.is_locked = True
        self.balance = 2500.0
        self.network = "https://testnet.xian.org"

    def start_server(self):
        """Start the protocol server in background thread"""
        self.server = WalletProtocolServer(wallet_type=WalletType.WEB)
        self.server.wallet = self
        self.server.is_locked = self.is_locked

        def run_server():
            self.server.run(host="127.0.0.1", port=8545)

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()


def main(page: ft.Page):
    page.title = "Xian Web Wallet"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO

    wallet = WebWallet()

    # Navigation state
    current_tab = ft.Text("wallet")

    # Password field
    password_field = ft.TextField(
        label="Enter Password",
        password=True,
        width=300,
        border_color=ft.Colors.BLUE_400
    )

    # Transaction fields
    recipient_field = ft.TextField(
        label="Recipient Address",
        width=400,
        border_color=ft.Colors.GREEN_400
    )

    amount_field = ft.TextField(
        label="Amount",
        width=200,
        border_color=ft.Colors.GREEN_400
    )

    # Status displays
    wallet_status = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.LOCK, color=ft.Colors.RED_400, size=40),
            ft.Text("Wallet Locked", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=20,
        border_radius=10,
        bgcolor=ft.Colors.RED_50,
        border=ft.border.all(2, ft.Colors.RED_200)
    )

    server_status = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.WIFI_OFF, color=ft.Colors.GREY_400, size=30),
            ft.Text("Server Stopped", size=14, color=ft.Colors.GREY_700)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=15,
        border_radius=8,
        bgcolor=ft.Colors.GREY_100,
        border=ft.border.all(1, ft.Colors.GREY_300)
    )

    def show_notification(message, error=False):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_400 if error else ft.Colors.GREEN_400
        )
        page.snack_bar.open = True
        page.update()

    def unlock_wallet():
        if password_field.value == "webwallet123":
            wallet.is_locked = False
            if wallet.server:
                wallet.server.is_locked = False

            wallet_status.content = ft.Column([
                ft.Icon(ft.Icons.LOCK_OPEN, color=ft.Colors.GREEN_400, size=40),
                ft.Text("Wallet Unlocked", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            wallet_status.bgcolor = ft.Colors.GREEN_50
            wallet_status.border = ft.border.all(2, ft.Colors.GREEN_200)

            password_field.value = ""
            show_notification("Wallet unlocked successfully!")
            page.update()
        else:
            show_notification("Invalid password", error=True)

    def lock_wallet():
        wallet.is_locked = True
        if wallet.server:
            wallet.server.is_locked = True

        wallet_status.content = ft.Column([
            ft.Icon(ft.Icons.LOCK, color=ft.Colors.RED_400, size=40),
            ft.Text("Wallet Locked", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        wallet_status.bgcolor = ft.Colors.RED_50
        wallet_status.border = ft.border.all(2, ft.Colors.RED_200)

        show_notification("Wallet locked")
        page.update()

    def start_server():
        try:
            wallet.start_server()
            server_status.content = ft.Column([
                ft.Icon(ft.Icons.WIFI, color=ft.Colors.GREEN_400, size=30),
                ft.Text("Server Running", size=14, color=ft.Colors.GREEN_700),
                ft.Text("localhost:8545", size=12, color=ft.Colors.GREEN_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            server_status.bgcolor = ft.Colors.GREEN_50
            server_status.border = ft.border.all(1, ft.Colors.GREEN_300)

            show_notification("Protocol server started on port 8545")
            page.update()
        except Exception as e:
            show_notification(f"Failed to start server: {str(e)}", error=True)

    def send_transaction():
        if wallet.is_locked:
            show_notification("Unlock wallet first", error=True)
            return

        if not recipient_field.value or not amount_field.value:
            show_notification("Fill in recipient and amount", error=True)
            return

        try:
            amount = float(amount_field.value)
            if amount > wallet.balance:
                show_notification("Insufficient balance", error=True)
                return

            # Simulate transaction
            wallet.balance -= amount
            recipient_field.value = ""
            amount_field.value = ""
            show_notification(f"Transaction sent: {amount} XIAN")
            page.update()
        except ValueError:
            show_notification("Invalid amount", error=True)

    def switch_tab(tab_name):
        current_tab.value = tab_name
        update_content()

    def update_content():
        content_area.content = get_tab_content(current_tab.value)
        page.update()

    def get_tab_content(tab):
        if tab == "wallet":
            return ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Address: {wallet.wallet_address}", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Balance: {wallet.balance} XIAN", size=20, color=ft.Colors.GREEN_700),
                        ft.Text(f"Network: {wallet.network}", size=14, color=ft.Colors.GREY_600),
                    ]),
                    padding=20,
                    border_radius=10,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.GREY_300)
                ),
                wallet_status,
                ft.Container(
                    content=ft.Column([
                        password_field,
                        ft.Row([
                            ft.ElevatedButton("Unlock", on_click=lambda _: unlock_wallet(),
                                              bgcolor=ft.Colors.BLUE_400, color=ft.Colors.WHITE),
                            ft.ElevatedButton("Lock", on_click=lambda _: lock_wallet(),
                                              bgcolor=ft.Colors.RED_400, color=ft.Colors.WHITE)
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ]),
                    padding=20
                )
            ], spacing=20)

        elif tab == "send":
            return ft.Column([
                ft.Text("Send Transaction", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column([
                        recipient_field,
                        amount_field,
                        ft.ElevatedButton(
                            "Send Transaction",
                            on_click=lambda _: send_transaction(),
                            bgcolor=ft.Colors.GREEN_400,
                            color=ft.Colors.WHITE,
                            width=200
                        )
                    ], spacing=15),
                    padding=20,
                    border_radius=10,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.GREY_300)
                )
            ], spacing=20)

        elif tab == "settings":
            return ft.Column([
                ft.Text("Settings", size=24, weight=ft.FontWeight.BOLD),
                server_status,
                ft.ElevatedButton(
                    "Start Protocol Server",
                    on_click=lambda _: start_server(),
                    bgcolor=ft.Colors.BLUE_400,
                    color=ft.Colors.WHITE
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Protocol Information", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("• Supports Universal Wallet Protocol"),
                        ft.Text("• Compatible with all DApp types"),
                        ft.Text("• Runs on localhost:8545"),
                        ft.Text("• Secure session-based authentication"),
                    ]),
                    padding=20,
                    border_radius=10,
                    bgcolor=ft.Colors.BLUE_50,
                    border=ft.border.all(1, ft.Colors.BLUE_200)
                )
            ], spacing=20)

    # Navigation
    nav_rail = ft.NavigationRail(
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.ACCOUNT_BALANCE_WALLET, label="Wallet"),
            ft.NavigationRailDestination(icon=ft.Icons.SEND, label="Send"),
            ft.NavigationRailDestination(icon=ft.Icons.SETTINGS, label="Settings")
        ],
        on_change=lambda e: switch_tab(["wallet", "send", "settings"][e.control.selected_index])
    )

    # Content area
    content_area = ft.Container(
        content=get_tab_content("wallet"),
        padding=30,
        expand=True
    )

    # Main layout
    page.add(
        ft.Column([
            ft.Container(
                content=ft.Text("Xian Web Wallet", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.BLUE_600,
                padding=20,
                width=float("inf"),
                alignment=ft.alignment.center
            ),
            ft.Row([
                nav_rail,
                ft.VerticalDivider(width=1),
                content_area
            ], expand=True)
        ], expand=True)
    )


# Updated for Flet 0.28.3: Use ft.run with web view
if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8080)
