# wallets/cli.py
"""
Xian CLI Wallet Daemon
Command-line wallet that runs the universal protocol server
"""

import click
import getpass
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from xian_py.wallet import Wallet, HDWallet

# Import our protocol components
from protocol.server import WalletProtocolServer
from protocol.models import WalletType, ProtocolConfig


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CLIWalletDaemon:
    """CLI Wallet Daemon that exposes the universal protocol"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.wallet_file = self.data_dir / "wallet.json"
        self.config_file = self.data_dir / "config.json"
        self.server: Optional[WalletProtocolServer] = None
    
    def create_wallet(self, password: str, mnemonic: Optional[str] = None) -> str:
        """Create a new wallet"""
        try:
            if mnemonic:
                # Import from mnemonic
                hd_wallet = HDWallet(mnemonic)
                wallet = hd_wallet.get_wallet([44, 0, 0, 0, 0])
                wallet_data = {
                    "type": "hd",
                    "mnemonic": mnemonic,
                    "derivation_path": [44, 0, 0, 0, 0]
                }
            else:
                # Generate new wallet
                wallet = Wallet()
                wallet_data = {
                    "type": "simple",
                    "private_key": wallet.private_key
                }
            
            # Encrypt wallet data (simplified - in production use proper encryption)
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            encrypted_data = {
                "wallet": wallet_data,
                "password_hash": password_hash,
                "address": wallet.public_key
            }
            
            # Save to file
            with open(self.wallet_file, 'w') as f:
                json.dump(encrypted_data, f, indent=2)
            
            logger.info(f"✅ Wallet created: {wallet.public_key}")
            return wallet.public_key
            
        except Exception as e:
            logger.error(f"Failed to create wallet: {e}")
            raise
    
    def load_wallet(self, password: str) -> Wallet:
        """Load wallet from file"""
        if not self.wallet_file.exists():
            raise FileNotFoundError("No wallet found. Create one first with 'xian-wallet create'")
        
        try:
            with open(self.wallet_file, 'r') as f:
                encrypted_data = json.load(f)
            
            # Verify password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash != encrypted_data["password_hash"]:
                raise ValueError("Invalid password")
            
            # Decrypt wallet data
            wallet_data = encrypted_data["wallet"]
            
            if wallet_data["type"] == "hd":
                hd_wallet = HDWallet(wallet_data["mnemonic"])
                wallet = hd_wallet.get_wallet(wallet_data["derivation_path"])
            else:
                wallet = Wallet(wallet_data["private_key"])
            
            logger.info(f"📍 Wallet loaded: {wallet.public_key}")
            return wallet
            
        except Exception as e:
            logger.error(f"Failed to load wallet: {e}")
            raise
    
    def start_daemon(self, password: str, host: str = ProtocolConfig.DEFAULT_HOST, port: int = ProtocolConfig.DEFAULT_PORT):
        """Start the wallet daemon"""
        try:
            # Load wallet
            wallet = self.load_wallet(password)
            
            # Create and configure server
            self.server = WalletProtocolServer(wallet_type=WalletType.CLI)
            
            # Override wallet initialization
            self.server.wallet = wallet
            self.server.password_hash = hashlib.sha256(password.encode()).hexdigest()
            self.server.is_locked = False
            
            # Initialize Xian client
            from xian_py.xian import Xian
            self.server.xian_client = Xian(self.server.network_url, wallet=wallet)
            
            logger.info(f"🚀 Starting CLI Wallet Daemon on {host}:{port}")
            logger.info(f"📍 Wallet: {wallet.public_key}")
            logger.info(f"🌐 Network: {self.server.network_url}")
            logger.info("💡 DApps can now connect to this wallet")
            
            # Run server
            self.server.run(host=host, port=port)
            
        except Exception as e:
            logger.error(f"Failed to start daemon: {e}")
            sys.exit(1)
    
    def stop_daemon(self):
        """Stop the wallet daemon"""
        if self.server:
            logger.info("🛑 Stopping CLI Wallet Daemon")
            # In a real implementation, this would gracefully shut down the server


@click.group()
@click.option('--data-dir', default=None, help='Data directory for wallet files')
@click.pass_context
def cli(ctx, data_dir):
    """Xian CLI Wallet - Universal Protocol Compatible"""
    if data_dir is None:
        data_dir = Path.home() / ".xian-wallet"
    else:
        data_dir = Path(data_dir)
    
    ctx.ensure_object(dict)
    ctx.obj['daemon'] = CLIWalletDaemon(data_dir)


@cli.command()
@click.option('--mnemonic', help='Import from mnemonic phrase (leave empty to generate new)')
@click.pass_context
def create(ctx, mnemonic):
    """Create a new wallet"""
    daemon = ctx.obj['daemon']
    
    if daemon.wallet_file.exists():
        if not click.confirm("Wallet already exists. Overwrite?"):
            return
    
    password = getpass.getpass("Enter wallet password: ")
    confirm_password = getpass.getpass("Confirm password: ")
    
    if password != confirm_password:
        click.echo("❌ Passwords don't match")
        return
    
    if len(password) < 8:
        click.echo("❌ Password must be at least 8 characters")
        return
    
    try:
        if mnemonic:
            # Validate mnemonic
            from xian_py.wallet import HDWallet
            try:
                HDWallet(mnemonic)
            except Exception:
                click.echo("❌ Invalid mnemonic phrase")
                return
        
        address = daemon.create_wallet(password, mnemonic)
        click.echo(f"✅ Wallet created successfully!")
        click.echo(f"📍 Address: {address}")
        
        if not mnemonic:
            click.echo("💡 Use 'xian-wallet backup' to view your mnemonic phrase")
        
    except Exception as e:
        click.echo(f"❌ Failed to create wallet: {e}")


@cli.command()
@click.option('--host', default=ProtocolConfig.DEFAULT_HOST, help='Host to bind to')
@click.option('--port', default=ProtocolConfig.DEFAULT_PORT, help='Port to bind to')
@click.option('--background', '-d', is_flag=True, help='Run in background')
@click.pass_context
def start(ctx, host, port, background):
    """Start the wallet daemon"""
    daemon = ctx.obj['daemon']
    
    if not daemon.wallet_file.exists():
        click.echo("❌ No wallet found. Create one first with 'xian-wallet create'")
        return
    
    password = getpass.getpass("Enter wallet password: ")
    
    if background:
        click.echo("🔄 Starting daemon in background...")
        # In production, implement proper daemonization
        import threading
        thread = threading.Thread(target=daemon.start_daemon, args=(password, host, port))
        thread.daemon = True
        thread.start()
        click.echo(f"✅ Daemon started on {host}:{port}")
        
        # Keep main thread alive
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            click.echo("🛑 Stopping daemon...")
    else:
        daemon.start_daemon(password, host, port)


@cli.command()
@click.pass_context
def status(ctx):
    """Check wallet status"""
    daemon = ctx.obj['daemon']
    
    if not daemon.wallet_file.exists():
        click.echo("❌ No wallet found")
        return
    
    try:
        with open(daemon.wallet_file, 'r') as f:
            data = json.load(f)
        
        click.echo("📋 Wallet Status:")
        click.echo(f"   Address: {data['address']}")
        click.echo(f"   Type: {data['wallet']['type']}")
        click.echo(f"   File: {daemon.wallet_file}")
        
        # Check if daemon is running
        import httpx
        try:
            response = httpx.get(f"http://{ProtocolConfig.DEFAULT_HOST}:{ProtocolConfig.DEFAULT_PORT}/api/v1/wallet/status", timeout=2)
            if response.status_code == 200:
                click.echo("   Daemon: ✅ Running")
            else:
                click.echo("   Daemon: ❌ Not responding")
        except:
            click.echo("   Daemon: ❌ Not running")
            
    except Exception as e:
        click.echo(f"❌ Error checking status: {e}")


@cli.command()
@click.pass_context
def backup(ctx):
    """Show wallet backup information"""
    daemon = ctx.obj['daemon']
    
    if not daemon.wallet_file.exists():
        click.echo("❌ No wallet found")
        return
    
    password = getpass.getpass("Enter wallet password: ")
    
    try:
        wallet = daemon.load_wallet(password)
        
        with open(daemon.wallet_file, 'r') as f:
            data = json.load(f)
        
        click.echo("🔐 Wallet Backup Information:")
        click.echo(f"   Address: {wallet.public_key}")
        
        if data['wallet']['type'] == 'hd':
            click.echo("   Type: HD Wallet")
            click.echo(f"   Mnemonic: {data['wallet']['mnemonic']}")
        else:
            click.echo("   Type: Simple Wallet")
            click.echo(f"   Private Key: {data['wallet']['private_key']}")
        
        click.echo("\n⚠️  Keep this information secure and private!")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.command()
@click.pass_context
def info(ctx):
    """Show wallet information"""
    daemon = ctx.obj['daemon']
    
    password = getpass.getpass("Enter wallet password: ")
    
    try:
        wallet = daemon.load_wallet(password)
        
        # Get balance
        from xian_py.xian import Xian
        xian_client = Xian("https://testnet.xian.org", wallet=wallet)
        balance = xian_client.get_balance(wallet.public_key)
        
        click.echo("💼 Wallet Information:")
        click.echo(f"   Address: {wallet.public_key}")
        click.echo(f"   Balance: {balance} XIAN")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.command()
@click.option('--to', required=True, help='Recipient address')
@click.option('--amount', required=True, type=float, help='Amount to send')
@click.option('--contract', default='currency', help='Token contract')
@click.pass_context
def send(ctx, to, amount, contract):
    """Send tokens"""
    daemon = ctx.obj['daemon']
    
    password = getpass.getpass("Enter wallet password: ")
    
    try:
        wallet = daemon.load_wallet(password)
        
        click.echo(f"📤 Sending {amount} {contract.upper()} to {to[:8]}...")
        
        # Send transaction
        from xian_py.xian import Xian
        xian_client = Xian("https://testnet.xian.org", wallet=wallet)
        result = xian_client.send_tx(
            contract=contract,
            function='transfer',
            kwargs={'to': to, 'amount': amount}
        )
        
        click.echo("✅ Transaction sent!")
        click.echo(f"   Result: {result}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")


if __name__ == "__main__":
    cli()
