# examples/wallets/desktop.py
# Requires: pip install flet>=0.28.3

import threading

import flet as ft

from xian_uwp.server import WalletProtocolServer
from xian_uwp.models import WalletType


class DesktopWallet:
    def __init__(self):
        self.server = None
        self.wallet_address = "Not initialized"
        self.is_locked = True
        self.balance = 0.0

    def start_server(self):
        """Start the protocol server in background thread"""
        try:
            self.server = WalletProtocolServer(wallet_type=WalletType.DESKTOP)
            self.server.is_locked = self.is_locked

            # Run server in background thread
            def run_server():
                self.server.run(host="127.0.0.1", port=8545)

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            # Wait a moment for server to initialize, then update UI with real wallet data
            import time
            time.sleep(1)  # Give server time to initialize
            self.update_wallet_info()
        except Exception as e:
            print(f"Failed to start server: {e}")
            # Set some demo data so the wallet still works
            self.wallet_address = "demo_wallet_address_12345678901234567890123456789012"
            self.balance = 100.0

    def update_wallet_info(self):
        """Update wallet info from the server's wallet instance"""
        if self.server and self.server.wallet:
            self.wallet_address = self.server.wallet.public_key
            # Set a demo balance for consistency (no real blockchain needed)
            self.balance = 100.0 if not self.is_locked else 0.0
        
    def get_truncated_address(self):
        """Get truncated address for display"""
        if len(self.wallet_address) > 16:
            return f"{self.wallet_address[:8]}...{self.wallet_address[-8:]}"
        return self.wallet_address


def main(page: ft.Page):
    page.title = "Xian Desktop Wallet"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 800
    page.window.height = 600
    page.window.center()
    page.padding = 0

    wallet = DesktopWallet()

    # UI State
    password_field = ft.TextField(
        label="Password (demo_password)",
        password=True,
        width=300,
        on_submit=lambda _: unlock_wallet()
    )

    address_text = ft.Text(
        value=f"Address: {wallet.get_truncated_address()}",
        size=16,
        weight=ft.FontWeight.BOLD
    )

    balance_text = ft.Text(
        value=f"Balance: {wallet.balance} XIAN",
        size=18,
        color=ft.Colors.GREEN_700
    )

    status_text = ft.Text(
        value="Wallet Locked",
        size=14,
        color=ft.Colors.RED_700
    )

    server_status = ft.Text(
        value="Server: Stopped",
        size=12,
        color=ft.Colors.GREY_700
    )

    def unlock_wallet():
        if password_field.value == "demo_password":  # Demo password (matches server)
            wallet.is_locked = False
            if wallet.server:
                wallet.server.is_locked = False

            # Update wallet info with real data
            wallet.update_wallet_info()
            
            # Update UI with real wallet data
            address_text.value = f"Address: {wallet.get_truncated_address()}"
            balance_text.value = f"Balance: {wallet.balance} XIAN"
            status_text.value = "Wallet Unlocked"
            status_text.color = ft.Colors.GREEN_700
            password_field.visible = False
            unlock_btn.visible = False
            lock_btn.visible = True
            page.update()
        else:
            show_error("Invalid password")

    def lock_wallet():
        wallet.is_locked = True
        if wallet.server:
            wallet.server.is_locked = True

        status_text.value = "Wallet Locked"
        status_text.color = ft.Colors.RED_700
        password_field.visible = True
        password_field.value = ""
        unlock_btn.visible = True
        lock_btn.visible = False
        page.update()

    def start_server():
        try:
            wallet.start_server()
            
            # Update UI with real wallet address (but keep balance as 0 since wallet is locked)
            address_text.value = f"Address: {wallet.get_truncated_address()}"
            
            server_status.value = "Server: Running on localhost:8545"
            server_status.color = ft.Colors.GREEN_700
            start_server_btn.visible = False
            stop_server_btn.visible = True
            page.update()
        except Exception as e:
            show_error(f"Failed to start server: {str(e)}")

    def stop_server():
        # In real implementation, you'd stop the server here
        server_status.value = "Server: Stopped"
        server_status.color = ft.Colors.RED_700
        start_server_btn.visible = True
        stop_server_btn.visible = False
        page.update()

    def show_error(message):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_400
        )
        page.snack_bar.open = True
        page.update()

    # Buttons
    unlock_btn = ft.ElevatedButton(
        "Unlock Wallet",
        on_click=lambda _: unlock_wallet(),
        bgcolor=ft.Colors.BLUE_400,
        color=ft.Colors.WHITE
    )

    lock_btn = ft.ElevatedButton(
        "Lock Wallet",
        on_click=lambda _: lock_wallet(),
        bgcolor=ft.Colors.RED_400,
        color=ft.Colors.WHITE,
        visible=False
    )

    start_server_btn = ft.ElevatedButton(
        "Start Protocol Server",
        on_click=lambda _: start_server(),
        bgcolor=ft.Colors.GREEN_400,
        color=ft.Colors.WHITE
    )

    stop_server_btn = ft.ElevatedButton(
        "Stop Protocol Server",
        on_click=lambda _: stop_server(),
        bgcolor=ft.Colors.ORANGE_400,
        color=ft.Colors.WHITE,
        visible=False
    )

    # Layout
    page.add(
        ft.Column([
            # Header
            ft.Container(
                content=ft.Text(
                    "Xian Desktop Wallet",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER
                ),
                bgcolor=ft.Colors.BLUE_600,
                padding=20,
                width=float("inf")
            ),

            # Main content
            ft.Container(
                content=ft.Column([
                    address_text,
                    balance_text,
                    status_text,
                    ft.Container(height=20),
                    password_field,
                    ft.Row([unlock_btn, lock_btn], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=30),
                    server_status,
                    ft.Row([start_server_btn, stop_server_btn], alignment=ft.MainAxisAlignment.CENTER),
                ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10),
                padding=30,
                alignment=ft.alignment.center
            )
        ])
    )


# Compatible with older Flet versions: Use ft.app instead of ft.run
if __name__ == "__main__":
    ft.app(target=main)
