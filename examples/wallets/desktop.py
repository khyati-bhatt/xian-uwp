# wallets/desktop.py
"""
Xian Desktop Wallet
Professional desktop wallet with universal protocol server
"""

import threading
import logging
from datetime import datetime
from typing import Optional
import flet as ft

from protocol.server import WalletProtocolServer
from protocol.models import WalletType, PendingRequest
from protocol.client import XianWalletClientSync


logger = logging.getLogger(__name__)


class DesktopWallet:
    """Professional desktop wallet application"""
    
    def __init__(self):
        self.server: Optional[WalletProtocolServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.page: Optional[ft.Page] = None
        
        # UI Components
        self.server_status = ft.Text("Server: Stopped", color=ft.Colors.RED)
        self.wallet_address = ft.Text("No wallet loaded")
        self.wallet_balance = ft.Text("0 XIAN")
        self.pending_requests_list = ft.Column()
        self.log_output = ft.Text("Wallet ready...", expand=True)
        
        # Test client for wallet operations
        self.test_client: Optional[XianWalletClientSync] = None
    
    def setup_ui(self, page: ft.Page):
        """Setup the desktop wallet UI"""
        self.page = page
        page.title = "Xian Desktop Wallet"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.window.width = 900
        page.window.height = 700
        
        # Header with status
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.WALLET, size=32, color=ft.Colors.BLUE),
                ft.Text("Xian Desktop Wallet", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                self.server_status
            ]),
            padding=20,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=10,
            margin=ft.Margin(0, 0, 0, 20)
        )
        
        # Wallet info section
        wallet_info_section = ft.Container(
            content=ft.Column([
                ft.Text("Wallet Information", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Text("Address: ", weight=ft.FontWeight.BOLD),
                    self.wallet_address
                ]),
                ft.Row([
                    ft.Text("Balance: ", weight=ft.FontWeight.BOLD),
                    self.wallet_balance
                ]),
                ft.Row([
                    ft.ElevatedButton(
                        "Start Server",
                        on_click=self.start_server,
                        bgcolor=ft.Colors.GREEN,
                        color=ft.Colors.WHITE
                    ),
                    ft.ElevatedButton(
                        "Stop Server",
                        on_click=self.stop_server,
                        bgcolor=ft.Colors.RED,
                        color=ft.Colors.WHITE
                    ),
                    ft.ElevatedButton(
                        "Refresh Balance",
                        on_click=self.refresh_balance,
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE
                    )
                ])
            ]),
            padding=20,
            bgcolor=ft.Colors.GREY_50,
            border_radius=10,
            margin=ft.Margin(0, 0, 0, 20)
        )
        
        # Authorization requests section
        auth_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("DApp Authorization Requests", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Refresh",
                        on_click=self.refresh_requests,
                        bgcolor=ft.Colors.ORANGE,
                        color=ft.Colors.WHITE
                    )
                ]),
                ft.Divider(),
                self.pending_requests_list
            ]),
            padding=20,
            bgcolor=ft.Colors.GREY_50,
            border_radius=10,
            margin=ft.Margin(0, 0, 0, 20),
            height=250
        )
        
        # Test section for development
        test_section = ft.Container(
            content=ft.Column([
                ft.Text("Test Wallet Functions", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.ElevatedButton(
                        "Test Connect",
                        on_click=self.test_connect,
                        bgcolor=ft.Colors.PURPLE,
                        color=ft.Colors.WHITE
                    ),
                    ft.ElevatedButton(
                        "Test Balance",
                        on_click=self.test_balance,
                        bgcolor=ft.Colors.INDIGO,
                        color=ft.Colors.WHITE
                    ),
                    ft.ElevatedButton(
                        "Test Sign",
                        on_click=self.test_sign,
                        bgcolor=ft.Colors.TEAL,
                        color=ft.Colors.WHITE
                    )
                ])
            ]),
            padding=20,
            bgcolor=ft.Colors.GREY_50,
            border_radius=10,
            margin=ft.Margin(0, 0, 0, 20)
        )
        
        # Log output section
        log_section = ft.Container(
            content=ft.Column([
                ft.Text("Activity Log", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=self.log_output,
                    bgcolor=ft.Colors.BLACK,
                    padding=15,
                    border_radius=5,
                    height=150
                )
            ]),
            padding=20,
            bgcolor=ft.Colors.GREY_50,
            border_radius=10
        )
        
        # Add all sections to page
        page.add(
            header,
            wallet_info_section,
            auth_section,
            test_section,
            log_section
        )
    
    def log_message(self, message: str, color: str = "white"):
        """Add message to log output"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        
        if self.log_output.value:
            self.log_output.value += f"\n{log_line}"
        else:
            self.log_output.value = log_line
        
        self.log_output.color = color
        
        # Keep only last 20 lines
        lines = self.log_output.value.split('\n')
        if len(lines) > 20:
            self.log_output.value = '\n'.join(lines[-20:])
        
        if self.page:
            self.page.update()
    
    def run_in_thread(self, func, *args, **kwargs):
        """Run function in separate thread"""
        def wrapper():
            try:
                func(*args, **kwargs)
            except Exception as e:
                self.log_message(f"❌ Error: {str(e)}", "red")
        
        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()
    
    def start_server(self, e):
        """Start the wallet protocol server"""
        self.run_in_thread(self._start_server)
    
    def _start_server(self):
        """Internal start server method"""
        try:
            if self.server and self.server_thread and self.server_thread.is_alive():
                self.log_message("⚠️ Server already running", "yellow")
                return
            
            self.log_message("🚀 Starting wallet protocol server...", "cyan")
            
            # Create server instance
            self.server = WalletProtocolServer(wallet_type=WalletType.DESKTOP)
            
            # Start server in background thread
            def run_server():
                try:
                    import uvicorn
                    uvicorn.run(
                        self.server.app,
                        host="127.0.0.1",
                        port=8545,
                        log_level="warning"  # Reduce noise
                    )
                except Exception as e:
                    self.log_message(f"❌ Server error: {str(e)}", "red")
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            # Give server time to start
            import time
            time.sleep(2)
            
            # Update UI
            self.server_status.value = "Server: Running on :8545"
            self.server_status.color = ft.Colors.GREEN
            
            # Update wallet info
            if self.server.wallet:
                self.wallet_address.value = self.server.wallet.public_key
                self.log_message(f"📍 Wallet loaded: {self.server.wallet.public_key}", "green")
            
            self.log_message("✅ Protocol server started successfully", "green")
            self.log_message("🌐 DApps can now connect to this wallet", "cyan")
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            self.log_message(f"❌ Failed to start server: {str(e)}", "red")
            self.server_status.value = "Server: Error"
            self.server_status.color = ft.Colors.RED
            if self.page:
                self.page.update()
    
    def stop_server(self, e):
        """Stop the wallet protocol server"""
        try:
            if self.server_thread and self.server_thread.is_alive():
                self.log_message("🛑 Stopping server...", "yellow")
                # In production, implement graceful shutdown
                self.server = None
                
            self.server_status.value = "Server: Stopped"
            self.server_status.color = ft.Colors.RED
            self.log_message("✅ Server stopped", "orange")
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            self.log_message(f"❌ Error stopping server: {str(e)}", "red")
    
    def refresh_balance(self, e):
        """Refresh wallet balance"""
        self.run_in_thread(self._refresh_balance)
    
    def _refresh_balance(self):
        """Internal refresh balance method"""
        try:
            if not self.server or not self.server.wallet:
                self.log_message("❌ No wallet loaded", "red")
                return
            
            self.log_message("🔄 Refreshing balance...", "cyan")
            
            if self.server.xian_client:
                balance = self.server.xian_client.get_balance(self.server.wallet.public_key)
                self.wallet_balance.value = f"{balance} XIAN"
                self.log_message(f"💰 Balance: {balance} XIAN", "green")
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            self.log_message(f"❌ Failed to refresh balance: {str(e)}", "red")
    
    def refresh_requests(self, e):
        """Refresh authorization requests"""
        self.run_in_thread(self._refresh_requests)
    
    def _refresh_requests(self):
        """Internal refresh requests method"""
        try:
            if not self.server:
                return
            
            self.pending_requests_list.controls.clear()
            
            if not self.server.pending_requests:
                self.pending_requests_list.controls.append(
                    ft.Text(
                        "No pending authorization requests",
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    )
                )
            else:
                for request_id, request in self.server.pending_requests.items():
                    self.add_request_card(request_id, request)
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            self.log_message(f"❌ Error refreshing requests: {str(e)}", "red")
    
    def add_request_card(self, request_id: str, request: PendingRequest):
        """Add authorization request card"""
        permissions_text = ", ".join([p.value for p in request.permissions])
        
        card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.APPS, color=ft.Colors.BLUE),
                        ft.Column([
                            ft.Text(request.app_name, weight=ft.FontWeight.BOLD),
                            ft.Text(request.app_url, color=ft.Colors.GREY_600, size=12),
                        ], expand=True),
                        ft.Chip(
                            label=ft.Text("PENDING"),
                            bgcolor=ft.Colors.ORANGE_100,
                            color=ft.Colors.ORANGE_800
                        )
                    ]),
                    ft.Text(f"Permissions: {permissions_text}", size=12),
                    ft.Text(
                        f"Requested: {request.created_at.strftime('%H:%M:%S')}",
                        size=12,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Row([
                        ft.ElevatedButton(
                            "Approve",
                            on_click=lambda e, rid=request_id: self.approve_request(rid),
                            bgcolor=ft.Colors.GREEN,
                            color=ft.Colors.WHITE
                        ),
                        ft.ElevatedButton(
                            "Deny",
                            on_click=lambda e, rid=request_id: self.deny_request(rid),
                            bgcolor=ft.Colors.RED,
                            color=ft.Colors.WHITE
                        )
                    ])
                ]),
                padding=15
            ),
            margin=ft.Margin(0, 0, 0, 10)
        )
        
        self.pending_requests_list.controls.append(card)
    
    def approve_request(self, request_id: str):
        """Approve authorization request"""
        self.run_in_thread(self._approve_request, request_id)
    
    def _approve_request(self, request_id: str):
        """Internal approve request method"""
        try:
            if not self.server or request_id not in self.server.pending_requests:
                self.log_message("❌ Request not found", "red")
                return
            
            request = self.server.pending_requests[request_id]
            
            # Simulate approval (in real implementation, this would be handled by the server)
            self.log_message(f"✅ Approved: {request.app_name}", "green")
            
            # Refresh requests display
            self._refresh_requests()
            
        except Exception as e:
            self.log_message(f"❌ Error approving request: {str(e)}", "red")
    
    def deny_request(self, request_id: str):
        """Deny authorization request"""
        try:
            if self.server and request_id in self.server.pending_requests:
                request = self.server.pending_requests[request_id]
                del self.server.pending_requests[request_id]
                self.log_message(f"❌ Denied: {request.app_name}", "orange")
                self._refresh_requests()
                
        except Exception as e:
            self.log_message(f"❌ Error denying request: {str(e)}", "red")
    
    # Test functions for development
    def test_connect(self, e):
        """Test wallet connection"""
        self.run_in_thread(self._test_connect)
    
    def _test_connect(self):
        """Internal test connect method"""
        try:
            self.log_message("🧪 Testing wallet connection...", "cyan")
            
            self.test_client = XianWalletClientSync(
                app_name="Desktop Wallet Test",
                app_url="http://localhost:desktop"
            )
            
            success = self.test_client.connect(auto_approve=True)
            if success:
                wallet_info = self.test_client.get_wallet_info()
                self.log_message(f"✅ Test connection successful: {wallet_info.truncated_address}", "green")
            else:
                self.log_message("❌ Test connection failed", "red")
                
        except Exception as e:
            self.log_message(f"❌ Test connection error: {str(e)}", "red")
    
    def test_balance(self, e):
        """Test balance query"""
        self.run_in_thread(self._test_balance)
    
    def _test_balance(self):
        """Internal test balance method"""
        try:
            if not self.test_client:
                self.log_message("❌ No test connection. Try 'Test Connect' first.", "red")
                return
            
            self.log_message("🧪 Testing balance query...", "cyan")
            balance = self.test_client.get_balance("currency")
            self.log_message(f"✅ Test balance: {balance} XIAN", "green")
            
        except Exception as e:
            self.log_message(f"❌ Test balance error: {str(e)}", "red")
    
    def test_sign(self, e):
        """Test message signing"""
        self.run_in_thread(self._test_sign)
    
    def _test_sign(self):
        """Internal test sign method"""
        try:
            if not self.test_client:
                self.log_message("❌ No test connection. Try 'Test Connect' first.", "red")
                return
            
            self.log_message("🧪 Testing message signing...", "cyan")
            signature = self.test_client.sign_message("Hello from Desktop Wallet!")
            self.log_message(f"✅ Test signature: {signature[:32]}...", "green")
            
        except Exception as e:
            self.log_message(f"❌ Test sign error: {str(e)}", "red")


def main(page: ft.Page):
    """Main function for desktop wallet"""
    wallet = DesktopWallet()
    wallet.setup_ui(page)


if __name__ == "__main__":
    print("🖥️ Starting Xian Desktop Wallet...")
    print("💡 This wallet runs the universal protocol server")
    print("🌐 DApps can connect to this wallet on port 8545")
    
    ft.app(target=main, view=ft.AppView.FLET_APP)
