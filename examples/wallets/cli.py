# examples/wallets/cli.py
# Requires: pip install click>=8.2.1 cryptography>=41.0.0

import click
import json
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet
from protocol.server import WalletProtocolServer
from protocol.models import WalletType

WALLET_DIR = Path.home() / ".xian_wallet"
WALLET_FILE = WALLET_DIR / "wallet.enc"
CONFIG_FILE = WALLET_DIR / "config.json"


class CLIWallet:
    def __init__(self):
        self.address = None
        self.private_key = None
        self.is_locked = True
        self.balance = 1000.0

    def save_encrypted(self, password: str):
        """Save wallet to encrypted file"""
        WALLET_DIR.mkdir(exist_ok=True)

        # Generate key from password
        key = hashlib.sha256(password.encode()).digest()
        # Use base64 encoding for Fernet key
        import base64
        fernet_key = base64.urlsafe_b64encode(key)
        fernet = Fernet(fernet_key)

        wallet_data = {
            "address": self.address,
            "private_key": self.private_key
        }

        encrypted_data = fernet.encrypt(json.dumps(wallet_data).encode())

        with open(WALLET_FILE, 'wb') as f:
            f.write(encrypted_data)

    def load_encrypted(self, password: str) -> bool:
        """Load wallet from encrypted file"""
        if not WALLET_FILE.exists():
            return False

        try:
            with open(WALLET_FILE, 'rb') as f:
                encrypted_data = f.read()

            # Generate key from password
            key = hashlib.sha256(password.encode()).digest()
            # Use base64 encoding for Fernet key
            import base64
            fernet_key = base64.urlsafe_b64encode(key)
            fernet = Fernet(fernet_key)
            
            decrypted_data = fernet.decrypt(encrypted_data)
            wallet_data = json.loads(decrypted_data.decode())

            self.address = wallet_data["address"]
            self.private_key = wallet_data["private_key"]
            return True
        except Exception:
            return False


@click.group()
@click.version_option()
def cli():
    """Xian CLI Wallet - Universal Wallet Protocol"""
    pass


@cli.command()
@click.option('--password', prompt=True, hide_input=True,
              help='Password to encrypt the wallet')
def create(password):
    """Create a new wallet"""
    wallet = CLIWallet()
    wallet.address = "xian1234567890abcdef"  # Demo address
    wallet.private_key = "private_key_demo"  # Demo key

    try:
        wallet.save_encrypted(password)
        click.echo(f"✅ Wallet created successfully!")
        click.echo(f"Address: {wallet.address}")
        click.echo(f"Wallet saved to: {WALLET_FILE}")
    except Exception as e:
        click.echo(f"❌ Failed to create wallet: {e}", err=True)


@cli.command()
@click.option('--password', prompt=True, hide_input=True,
              help='Password to unlock the wallet')
@click.option('--port', default=8545, help='Port to run server on')
@click.option('--background', is_flag=True, help='Run as background daemon')
def start(password, port, background):
    """Start the wallet daemon"""
    if not WALLET_FILE.exists():
        click.echo("❌ No wallet found. Create one first with 'create' command.", err=True)
        return

    wallet = CLIWallet()
    if not wallet.load_encrypted(password):
        click.echo("❌ Invalid password or corrupted wallet.", err=True)
        return

    wallet.is_locked = False

    # Create and start server
    server = WalletProtocolServer(wallet_type=WalletType.CLI)
    server.wallet = wallet
    server.is_locked = False

    click.echo(f"🚀 Starting Xian CLI Wallet daemon...")
    click.echo(f"Address: {wallet.address}")
    click.echo(f"Server: http://localhost:{port}")
    click.echo(f"Press Ctrl+C to stop")

    try:
        if background:
            # In real implementation, you'd properly daemonize
            click.echo("Running in background mode...")

        server.run(host="127.0.0.1", port=port)
    except KeyboardInterrupt:
        click.echo("\n🛑 Shutting down wallet daemon...")
    except Exception as e:
        click.echo(f"❌ Server error: {e}", err=True)


@cli.command()
def status():
    """Check wallet and server status"""
    if not WALLET_FILE.exists():
        click.echo("❌ No wallet found")
        return

    click.echo("✅ Wallet file exists")
    click.echo(f"Location: {WALLET_FILE}")

    # Check if server is running (simplified check)
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8545))
    sock.close()

    if result == 0:
        click.echo("🟢 Server is running on port 8545")
    else:
        click.echo("🔴 Server is not running")


@cli.command()
@click.option('--password', prompt=True, hide_input=True,
              help='Password to unlock the wallet')
def info(password):
    """Show wallet information"""
    if not WALLET_FILE.exists():
        click.echo("❌ No wallet found", err=True)
        return

    wallet = CLIWallet()
    if not wallet.load_encrypted(password):
        click.echo("❌ Invalid password", err=True)
        return

    click.echo("📱 Wallet Information:")
    click.echo(f"Address: {wallet.address}")
    click.echo(f"Balance: {wallet.balance} XIAN")
    click.echo(f"Status: {'Unlocked' if not wallet.is_locked else 'Locked'}")


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to delete the wallet?')
def delete():
    """Delete the wallet (irreversible)"""
    try:
        if WALLET_FILE.exists():
            WALLET_FILE.unlink()
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()

        click.echo("✅ Wallet deleted successfully")
    except Exception as e:
        click.echo(f"❌ Failed to delete wallet: {e}", err=True)


if __name__ == '__main__':
    cli()
