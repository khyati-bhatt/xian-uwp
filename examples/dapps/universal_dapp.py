# examples/dapps/universal_dapp.py
"""
Universal DApp Example - Xian Universal Protocol
Example DApp that connects to any wallet type (desktop, web, CLI)
"""

import flet as ft
import threading
from typing import Optional

# Import the universal protocol client
from protocol.client import XianWalletClientSync, WalletProtocolError
from protocol.models import WalletInfo


class UniversalXianDApp:
    """DApp that works with any Xian wallet (desktop, CLI, web extension)"""
    
    def __init__(self):
        self.client: Optional[XianWalletClientSync] = None
        self.wallet_info: Optional[WalletInfo] = None
        self.page: Optional[ft.Page] = None
        
        # UI Components
        self.connection_status = ft.Text("Not Connected", color="red")
        self.wallet_type_indicator = ft.Text("Unknown Wallet Type")
        self.wallet_address = ft.Text("No wallet connected")
        self.wallet_balance = ft.Text("0")
        self.output_text = ft.Text("Ready to connect to any Xian wallet...", expand=True)
        
    def setup_ui(self, page: ft.Page):
        """Setup the universal DApp UI"""
        self.page = page
        page.title = "Universal Xian DApp"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.scroll = ft.ScrollMode.AUTO
        
        # Header with universal wallet info
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SYNC, color=ft.Colors.PURPLE),
                ft.Text("Universal Xian DApp", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.Column([
                    self.connection_status,
                    self.wallet_type_indicator
                ], horizontal_alignment=ft.CrossAxisAlignment.END)
            ]),
            padding=20,
            bgcolor=ft.Colors.PURPLE_50,
            border_radius=10,
            margin=ft.Margin(0, 0, 0, 20)
        )
        
        # Universal wallet connection section
        wallet_section = ft.Container(
            content=ft.Column([
                ft.Text("Universal Wallet Connection", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "This DApp works with ANY Xian wallet type: Desktop, CLI, or Web Extension",
                    color=ft.Colors.GREY_700,
                    size=14
                ),
                ft.Divider(),
                ft.Row([
                    ft.Text("Status: ", weight=ft.FontWeight.BOLD),
                    self.connection_status
                ]),
                ft.Row([
                    ft.Text("Wallet Type: ", weight=ft.FontWeight.BOLD),
                    self.wallet_type_indicator
                ]),
                ft.Row([
                    ft.Text("Address: ", weight=ft.FontWeight.BOLD),
                    self.wallet_address
                ]),
                ft.Row([
                    ft.Text("Balance: ", weight=ft.FontWeight.BOLD),
                    self.wallet_balance,
                    ft.Text("XIAN")
                ]),
                ft.Row([
                    ft.ElevatedButton(
                        "Connect Any Wallet",
                        on_click=self.connect_wallet,
                        bgcolor=ft.Colors.PURPLE,
                        color=ft.Colors.WHITE,
                        icon=ft.Icons.LINK
                    ),
                    ft.ElevatedButton(
                        "Disconnect",
                        on_click=self.disconnect_wallet,
                        bgcolor=ft.Colors.RED,
                        color=ft.Colors.WHITE,
                        icon=ft.Icons.LINK_OFF
                    ),
                    ft.ElevatedButton(
                        "Refresh Data",
                        on_click=self.refresh_data,
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE,
                        icon=ft.Icons.REFRESH
                    )
                ])
            ]),
            padding=20,
            bgcolor=ft.Colors.GREY_50,
            border_radius=10,
            margin=ft.Margin(0, 0, 0, 20)
        )
        
        # Transaction section
        self.recipient_field = ft.TextField(
            label="Recipient Address",
            hint_text="Enter recipient address...",
            expand=True
        )
        
        self.amount_field = ft.TextField(
            label="Amount",
            hint_text="Enter amount to send...",
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        transaction_section = ft.Container(
            content=ft.Column([
                ft.Text("Universal Transaction", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Send transactions through any connected wallet type",
                    color=ft.Colors.GREY_700,
                    size=14
                ),
                ft.Divider(),
                ft.Row([
                    self.recipient_field,
                    self.amount_field
                ]),
                ft.Row([
                    ft.ElevatedButton(
                        "Send XIAN",
                        on_click=self.send_transaction,
                        bgcolor=ft.Colors.GREEN,
                        color=ft.Colors.WHITE,
                        icon=ft.Icons.SEND
                    ),
                    ft.ElevatedButton(
                        "Get Balance",
                        on_click=self.get_balance,
                        bgcolor=ft.Colors.ORANGE,
                        color=ft.Colors.WHITE,
                        icon=ft.Icons.ACCOUNT_BALANCE_WALLET
                    )
                ])
            ]),
            padding=20,
            bgcolor=ft.Colors.GREY_50,
            border_radius=10,
            margin=ft.Margin(0, 0, 0, 20)
        )
        
        # Message signing section
        self.message_field = ft.TextField(
            label="Message to Sign",
            hint_text="Enter message to sign...",
            multiline=True,
            min_lines=2,
            max_lines=4,
            expand=True
        )
        
        self.signature_output = ft.TextField(
            label="Signature Output",
            read_only=True,
            multiline=True,
            min_lines=2,
            max_lines=4,
            expand=True
        )
        
        signing_section = ft.Container(
            content=ft.Column([
                ft.Text("Universal Message Signing", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Sign messages with any wallet type using the same interface",
                    color=ft.Colors.GREY_700,
                    size=14
                ),
                ft.Divider(),
                self.message_field,
                ft.ElevatedButton(
                    "Sign Message",
                    on_click=self.sign_message,
                    bgcolor=ft.Colors.INDIGO,
                    color=ft.Colors.WHITE,
                    icon=ft.Icons.EDIT
                ),
                self.signature_output
            ]),
            padding=20,
            bgcolor=ft.Colors.GREY_50,
            border_radius=10,
            margin=ft.Margin(0, 0, 0, 20)
        )
        
        # Wallet compatibility section
        compatibility_section = ft.Container(
            content=ft.Column([
                ft.Text("Wallet Compatibility", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "This DApp is compatible with:",
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_700
                ),
                ft.Row([
                    ft.Icon(ft.Icons.DESKTOP_WINDOWS, color=ft.Colors.BLUE),
                    ft.Text("Desktop Wallets (Flet-based GUI)")
                ]),
                ft.Row([
                    ft.Icon(ft.Icons.TERMINAL, color=ft.Colors.GREEN),
                    ft.Text("CLI Wallets (Command-line daemon)")
                ]),
                ft.Row([
                    ft.Icon(ft.Icons.WEB, color=ft.Colors.ORANGE),
                    ft.Text("Web Wallets (Browser extension)")
                ]),
                ft.Row([
                    ft.Icon(ft.Icons.HARDWARE, color=ft.Colors.PURPLE),
                    ft.Text("Hardware Wallets (via protocol adapters)")
                ]),
                ft.Divider(),
                ft.Text(
                    "All wallet types expose the same API on localhost:8545",
                    size=12,
                    color=ft.Colors.GREY_600,
                    italic=True
                )
            ]),
            padding=20,
            bgcolor=ft.Colors.GREY_50,
            border_radius=10,
            margin=ft.Margin(0, 0, 0, 20)
        )
        
        # Output log section
        output_section = ft.Container(
            content=ft.Column([
                ft.Text("Activity Log", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=self.output_text,
                    bgcolor=ft.Colors.BLACK,
                    padding=15,
                    border_radius=5,
                    height=200
                )
            ]),
            padding=20,
            bgcolor=ft.Colors.GREY_50,
            border_radius=10
        )
        
        # Add all sections to page
        page.add(
            header,
            wallet_section,
            transaction_section,
            signing_section,
            compatibility_section,
            output_section
        )
    
    def log_output(self, message: str, color: str = "white"):
        """Add message to output log"""
        if self.page:
            self.output_text.value = f"{self.output_text.value}\n{message}"
            self.output_text.color = color
            self.page.update()
    
    def run_in_thread(self, func, *args, **kwargs):
        """Run a function in a separate thread to avoid blocking UI"""
        def wrapper():
            try:
                func(*args, **kwargs)
            except Exception as e:
                self.log_output(f"❌ Error: {str(e)}", "red")
        
        thread = threading.Thread(target=wrapper)
        thread.daemon = True
        thread.start()
    
    # Wallet connection methods
    def connect_wallet(self, e):
        """Connect to any available wallet"""
        self.run_in_thread(self._connect_wallet)
    
    def _connect_wallet(self):
        """Internal connect wallet method"""
        try:
            self.log_output("🔄 Connecting to any available Xian wallet...", "yellow")
            self.log_output("💡 Looking for wallet on localhost:8545", "cyan")
            
            # Create universal client
            self.client = XianWalletClientSync(
                app_name="Universal Xian DApp",
                app_url="http://localhost:8080"
            )
            
            # Connect to any wallet type
            success = self.client.connect(auto_approve=False)
            
            if success:
                # Get wallet info to determine type
                self.wallet_info = self.client.get_wallet_info()
                
                # Update UI with wallet info
                self.connection_status.value = "Connected"
                self.connection_status.color = "green"
                self.wallet_type_indicator.value = f"{self.wallet_info.wallet_type.value.title()} Wallet"
                self.wallet_address.value = self.wallet_info.truncated_address
                
                # Get initial balance
                self._refresh_balance()
                
                self.log_output("✅ Successfully connected to wallet!", "green")
                self.log_output(f"📱 Wallet Type: {self.wallet_info.wallet_type.value.title()}", "cyan")
                self.log_output(f"📍 Address: {self.wallet_info.address}", "cyan")
                self.log_output(f"🌐 Network: {self.wallet_info.network}", "cyan")
                
            else:
                self.log_output("❌ Failed to connect to wallet", "red")
                self.log_output("💡 Make sure a Xian wallet is running on port 8545", "yellow")
                
            if self.page:
                self.page.update()
                
        except WalletProtocolError as e:
            self.log_output(f"❌ Connection failed: {str(e)}", "red")
            if "not available" in str(e):
                self.log_output("💡 Start a Xian wallet (desktop, CLI, or web extension)", "yellow")
            self.connection_status.value = "Failed"
            self.connection_status.color = "red"
            if self.page:
                self.page.update()
    
    def disconnect_wallet(self, e):
        """Disconnect from wallet"""
        self.run_in_thread(self._disconnect_wallet)
    
    def _disconnect_wallet(self):
        """Internal disconnect wallet method"""
        try:
            if self.client:
                self.client.disconnect()
                self.client = None
            
            # Reset UI state
            self.connection_status.value = "Not Connected"
            self.connection_status.color = "red"
            self.wallet_type_indicator.value = "Unknown Wallet Type"
            self.wallet_address.value = "No wallet connected"
            self.wallet_balance.value = "0"
            self.wallet_info = None
            
            self.log_output("🔌 Disconnected from wallet", "orange")
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            self.log_output(f"❌ Disconnect error: {str(e)}", "red")
    
    def refresh_data(self, e):
        """Refresh wallet data"""
        self.run_in_thread(self._refresh_data)
    
    def _refresh_data(self):
        """Internal refresh data method"""
        try:
            if not self.client:
                self.log_output("❌ No wallet connected", "red")
                return
            
            self.log_output("🔄 Refreshing wallet data...", "yellow")
            
            # Refresh wallet info
            self.wallet_info = self.client.get_wallet_info()
            
            # Refresh balance
            self._refresh_balance()
            
            self.log_output("✅ Data refreshed successfully", "green")
            
        except Exception as e:
            self.log_output(f"❌ Failed to refresh data: {str(e)}", "red")
    
    def _refresh_balance(self):
        """Internal refresh balance method"""
        try:
            if not self.client:
                return
            
            balance = self.client.get_balance("currency")
            self.wallet_balance.value = str(balance)
            self.log_output(f"💰 Balance: {balance} XIAN", "green")
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            self.log_output(f"❌ Failed to get balance: {str(e)}", "red")
    
    # Transaction methods
    def send_transaction(self, e):
        """Send transaction through any wallet type"""
        self.run_in_thread(self._send_transaction)
    
    def _send_transaction(self):
        """Internal send transaction method"""
        try:
            if not self.client:
                self.log_output("❌ No wallet connected", "red")
                return
            
            recipient = self.recipient_field.value
            amount_str = self.amount_field.value
            
            if not recipient or not amount_str:
                self.log_output("❌ Please enter recipient and amount", "red")
                return
            
            try:
                amount = float(amount_str)
            except ValueError:
                self.log_output("❌ Invalid amount format", "red")
                return
            
            self.log_output(f"🔄 Sending {amount} XIAN to {recipient[:8]}...", "yellow")
            self.log_output(f"📱 Using {self.wallet_info.wallet_type.value} wallet", "cyan")
            
            result = self.client.send_transaction(
                contract="currency",
                function="transfer",
                kwargs={
                    "to": recipient,
                    "amount": amount
                }
            )
            
            if result.success:
                self.log_output("✅ Transaction sent successfully!", "green")
                if result.transaction_hash:
                    self.log_output(f"📜 TX Hash: {result.transaction_hash}", "cyan")
                
                # Refresh balance after successful transaction
                self._refresh_balance()
            else:
                self.log_output(f"❌ Transaction failed: {', '.join(result.errors or ['Unknown error'])}", "red")
            
        except Exception as e:
            self.log_output(f"❌ Transaction error: {str(e)}", "red")
    
    def get_balance(self, e):
        """Get balance from any wallet type"""
        self.run_in_thread(self._get_balance)
    
    def _get_balance(self):
        """Internal get balance method"""
        try:
            if not self.client:
                self.log_output("❌ No wallet connected", "red")
                return
            
            self.log_output("🔄 Querying balance...", "yellow")
            balance = self.client.get_balance("currency")
            
            self.wallet_balance.value = str(balance)
            self.log_output(f"💰 Current balance: {balance} XIAN", "green")
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            self.log_output(f"❌ Failed to get balance: {str(e)}", "red")
    
    # Message signing methods
    def sign_message(self, e):
        """Sign message with any wallet type"""
        self.run_in_thread(self._sign_message)
    
    def _sign_message(self):
        """Internal sign message method"""
        try:
            if not self.client:
                self.log_output("❌ No wallet connected", "red")
                return
            
            message = self.message_field.value
            if not message:
                self.log_output("❌ Please enter a message to sign", "red")
                return
            
            self.log_output("🔄 Signing message...", "yellow")
            self.log_output(f"📱 Using {self.wallet_info.wallet_type.value} wallet", "cyan")
            
            signature = self.client.sign_message(message)
            
            self.signature_output.value = signature
            self.log_output("✅ Message signed successfully!", "green")
            self.log_output(f"📝 Signature: {signature[:32]}...", "cyan")
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            self.log_output(f"❌ Failed to sign message: {str(e)}", "red")


def main(page: ft.Page):
    """Main function for universal DApp"""
    dapp = UniversalXianDApp()
    dapp.setup_ui(page)


if __name__ == "__main__":
    print("🚀 Starting Universal DApp Example...")
    print("🔗 This example DApp works with ANY Xian wallet type:")
    print("   📱 Desktop wallets (GUI applications)")
    print("   🌐 Web wallets (browser-based Flet apps)")
    print("   💻 CLI wallets (command-line daemons)")  
    print("   🔧 Hardware wallets (via adapters)")
    print()
    print("💡 Make sure a Xian wallet is running on port 8545")
    print("🌐 DApp will be available at http://localhost:8080")
    
    # Run as web app
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        port=8080,
        host="127.0.0.1"
    )