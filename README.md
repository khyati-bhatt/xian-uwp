# Xian Universal Wallet Protocol

## Overview

The Xian Universal Wallet Protocol provides a **unified interface** for all wallet types (desktop, CLI, web) to communicate with DApps. Every wallet exposes the same HTTP API on `localhost:8545`, making wallet integration **programming language independent** and **wallet type agnostic**.

## Universal Protocol Architecture

```
┌─────────────────┐    HTTP API      ┌─────────────────┐
│   Any DApp      │ ◄──────────────► │  Any Wallet     │
│ (Python, JS,    │  localhost:8545  │ (Desktop, Web,  │
│  etc.)          │                  │  CLI)           │
└─────────────────┘                  └─────────────────┘
         │                                    │
         │                                    │
         ▼                                    ▼
┌─────────────────┐                  ┌─────────────────┐
│ Universal       │                  │ Protocol Server │
│ Client Library  │                  │ (Port 8545)     │
└─────────────────┘                  └─────────────────┘
```

### Key Benefits

- **Universal Interface**: All wallets expose identical HTTP API
- **Language Independent**: Works with any programming language
- **Wallet Agnostic**: DApps work with desktop, web, or CLI wallets
- **Drop-in Replacement**: Compatible with existing dapp-utils API
- **Professional**: Session-based auth, caching, error handling

## How the Protocol Works

### 1. Standard Port & API
All Xian wallets run a local HTTP server on `localhost:8545` with standardized endpoints:

```
GET  /api/v1/wallet/status        # Check wallet availability
POST /api/v1/auth/request         # Request DApp authorization  
GET  /api/v1/wallet/info          # Get wallet information
GET  /api/v1/balance/{contract}   # Get token balance
POST /api/v1/transaction          # Send transaction
POST /api/v1/sign                 # Sign message
```

### 2. Authorization Flow
1. DApp requests authorization with permissions
2. Wallet shows approval UI to user
3. User approves/denies the request
4. Wallet returns session token to DApp
5. DApp uses token for subsequent requests

### 3. Session Management
- Time-limited session tokens (default 1 hour)
- Permission-based access control
- Auto-lock after inactivity
- Multiple concurrent sessions supported

## Wallet Implementation Guide

### Desktop Wallet Implementation

Desktop wallets run the protocol server directly in the application:

```python
from protocol.server import WalletProtocolServer
from protocol.models import WalletType

# Create server instance
server = WalletProtocolServer(wallet_type=WalletType.DESKTOP)

# Load your wallet
server.wallet = your_wallet_instance
server.password_hash = your_password_hash
server.is_locked = False

# Run server (usually in background thread)
server.run(host="127.0.0.1", port=8545)
```

**Key Implementation Points:**
- Embed server in your desktop app
- Handle user authorization via native UI
- Manage wallet unlock/lock states
- Optional: Add systray integration

### CLI Wallet Implementation  

CLI wallets run as daemon processes:

```bash
# Create wallet
xian-wallet create

# Start daemon
xian-wallet start --background

# Check status  
xian-wallet status
```

```python
# CLI daemon implementation
class CLIWalletDaemon:
    def start_daemon(self, password):
        # Load wallet from encrypted file
        wallet = self.load_wallet(password)
        
        # Create and start server
        server = WalletProtocolServer(wallet_type=WalletType.CLI)
        server.wallet = wallet
        server.run()
```

**Key Implementation Points:**
- Encrypted wallet storage on disk
- Background daemon process
- Command-line interface for management
- Auto-approval or terminal-based approval UI

### Web Wallet (Flet-based) Implementation

Web wallets run in the browser but use Python/Flet:

```python
from protocol.server import WalletProtocolServer
from protocol.models import WalletType
import flet as ft

# Create server instance  
server = WalletProtocolServer(wallet_type=WalletType.WEB)

# Load your wallet
server.wallet = your_wallet_instance
server.password_hash = your_password_hash
server.is_locked = False

# Run server in background thread
def run_server():
    server.run(host="127.0.0.1", port=8545)

# Run Flet web interface
ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080)
```

**Key Implementation Points:**
- Flet-based web interface (100% Python)
- Same codebase as desktop wallet
- Works on any device with browser
- No browser extension needed
- Professional UI with tabs and responsive design

## DApp Integration

### Using the Universal Client

DApps use the same client library regardless of wallet type:

```python
from protocol.client import XianWalletClientSync

# Create client - works with any wallet type
client = XianWalletClientSync(
    app_name="My DApp", 
    app_url="http://localhost:8080"
)

# Connect to any wallet
client.connect()

# Use identical API regardless of wallet type
wallet_info = client.get_wallet_info()
balance = client.get_balance("currency")
result = client.send_transaction("currency", "transfer", {"to": "addr", "amount": 100})
```

### Legacy Compatibility

For existing JavaScript DApps:

```javascript
// Same API as original dapp-utils
XianWalletUtils.init();
const info = await XianWalletUtils.requestWalletInfo();
const balance = await XianWalletUtils.getBalance("currency");
```

## API Reference

### Core Endpoints

#### GET /api/v1/wallet/status
```json
{
  "available": true,
  "locked": false,
  "wallet_type": "desktop",
  "network": "https://testnet.xian.org",
  "chain_id": "xian-testnet",
  "version": "1.0.0"
}
```

#### POST /api/v1/auth/request
```json
{
  "app_name": "My DApp",
  "app_url": "http://localhost:8080", 
  "permissions": ["wallet_info", "balance", "transactions"]
}
```

Response:
```json
{
  "request_id": "req_abc123",
  "status": "pending"
}
```

#### POST /api/v1/auth/approve/{request_id}
```json
{
  "session_token": "token_xyz789",
  "expires_at": "2024-01-01T12:00:00Z",
  "permissions": ["wallet_info", "balance", "transactions"]
}
```

#### GET /api/v1/wallet/info
*Requires Authorization: Bearer {session_token}*

```json
{
  "address": "abc123...",
  "truncated_address": "abc123...xyz789",
  "locked": false,
  "chain_id": "xian-testnet", 
  "network": "https://testnet.xian.org",
  "wallet_type": "desktop",
  "version": "1.0.0"
}
```

#### GET /api/v1/balance/{contract}
*Requires Authorization: Bearer {session_token}*

```json
{
  "balance": 1000.0,
  "contract": "currency",
  "symbol": "XIAN",
  "decimals": 8
}
```

#### POST /api/v1/transaction
*Requires Authorization: Bearer {session_token}*

```json
{
  "contract": "currency",
  "function": "transfer",
  "kwargs": {"to": "recipient_address", "amount": 100},
  "stamps_supplied": 50000
}
```

Response:
```json
{
  "success": true,
  "transaction_hash": "tx_hash_here",
  "result": "transaction_result",
  "gas_used": 45000
}
```

## Installation & Setup

### 1. Install Core Protocol Dependencies

```bash
pip install fastapi uvicorn httpx websockets pydantic xian-py
```

**Core Dependencies Explained:**
- `fastapi` - HTTP API server framework
- `uvicorn` - ASGI server to run FastAPI
- `httpx` - Async HTTP client for wallet connections  
- `websockets` - WebSocket support for real-time communication
- `pydantic` - Data validation and serialization
- `xian-py` - Xian blockchain SDK for wallet operations

### 2. Optional Dependencies (Install as needed)

**For Desktop Wallet Development:**
```bash
pip install flet
```

**For CLI Wallet Development:**
```bash
pip install click
pip install cryptography  # For encrypted wallet storage
```

**For Running Examples:**
```bash
pip install flet          # Required for Flet examples
pip install reflex        # Required for Reflex examples
```

### 2. Project Structure

```
xian-universal-wallet-protocol/
├── protocol/
│   ├── __init__.py
│   ├── models.py          # Data models & constants
│   ├── server.py          # Universal protocol server  
│   └── client.py          # Universal client library
├── examples/
│   ├── wallets/           # Wallet implementation examples
│   │   ├── desktop.py     # Desktop wallet example (requires: flet)
│   │   ├── web.py         # Web wallet example (requires: flet)
│   │   └── cli.py         # CLI wallet example (requires: click, cryptography)
│   └── dapps/             # DApp examples
│       ├── universal_dapp.py  # Flet DApp example (requires: flet)
│       └── reflex_dapp.py     # Reflex DApp example (requires: reflex)
├── requirements.txt       # Core protocol dependencies only
└── README.md
```

**Dependency Notes:**
- `requirements.txt` contains **only core protocol dependencies**
- Additional dependencies listed above are needed for specific wallet examples
- All files outside `protocol/` are **examples** to learn from and adapt
- Web wallet uses Flet for browser-based interface (not browser extension)
- DApp examples available in both Flet and Reflex frameworks

### 3. Run Desktop Wallet Example

```bash
# Install desktop wallet dependencies
pip install flet

# Run desktop wallet example
python examples/wallets/desktop.py
```

### 4. Run Web Wallet Example

```bash
# Install web wallet dependencies
pip install flet

# Run web wallet example (opens in browser)
python examples/wallets/web.py
```

### 5. Run CLI Wallet Example

```bash
# Install CLI wallet dependencies  
pip install click cryptography

# Create wallet
python examples/wallets/cli.py create

# Start daemon
python examples/wallets/cli.py start
```

### 6. Run DApp Examples

**Flet DApp Example:**
```bash
# Install Flet DApp dependencies
pip install flet

# Run Flet DApp example
python examples/dapps/universal_dapp.py
```

**Reflex DApp Example:**
```bash
# Install Reflex DApp dependencies
pip install reflex

# Initialize and run Reflex DApp
cd examples/dapps/
reflex init --template blank
# Copy reflex_dapp.py content to the generated app
reflex run
```

## Example Implementations

### Flet DApp Example

```python
# examples/dapps/universal_dapp.py
# Requires: pip install flet

from protocol.client import XianWalletClientSync

class MyDApp:
    def __init__(self):
        self.client = XianWalletClientSync("My DApp")
    
    def connect_wallet(self):
        self.client.connect()
        info = self.client.get_wallet_info()
        print(f"Connected: {info.address}")
    
    def send_tokens(self, to, amount):
        result = self.client.send_transaction(
            "currency", "transfer", 
            {"to": to, "amount": amount}
        )
        return result.success
```

### Reflex DApp Example

```python
# examples/dapps/reflex_dapp.py  
# Requires: pip install reflex

import reflex as rx
from protocol.client import XianWalletClientSync

class WalletState(rx.State):
    """Wallet DApp state with Reflex"""
    is_connected: bool = False
    wallet_address: str = "No wallet connected"
    
    async def connect_wallet(self):
        self._client = XianWalletClientSync("Reflex DApp")
        success = self._client.connect()
        if success:
            info = self._client.get_wallet_info()
            self.is_connected = True
            self.wallet_address = info.truncated_address

def index():
    return rx.center(
        rx.vstack(
            rx.heading("Universal Xian DApp"),
            rx.text(WalletState.wallet_address),
            rx.button(
                "Connect Wallet",
                on_click=WalletState.connect_wallet,
                disabled=WalletState.is_connected
            )
        )
    )

app = rx.App()
app.add_page(index)
```

**Both examples work with any wallet type:** Desktop, Web, CLI, or Hardware wallets.

### Web DApp Example

```html
<!-- For legacy JavaScript compatibility -->
<script>
// Works with any wallet type (desktop, web, CLI)
XianWalletUtils.init().then(() => {
    return XianWalletUtils.requestWalletInfo();
}).then(info => {
    console.log('Connected:', info.address);
});
</script>
```

**Note:** Web wallets provide the same localhost:8545 API, so existing JavaScript code works unchanged.

## Security Considerations

### Local-Only Communication
- Server binds to 127.0.0.1 only (no external access)
- No cross-origin issues (same machine)
- No network exposure of wallet operations

### Session Security
- Time-limited tokens with automatic expiration
- Permission-based access control
- Session invalidation on wallet lock
- Multiple session support with individual revocation

### Data Protection
- No sensitive data in logs
- Encrypted wallet storage (CLI)
- Secure password handling (SHA256 minimum)
- Auto-lock on inactivity

## Production Deployment

### For Wallet Developers

1. **Implement the protocol server** in your wallet
2. **Handle authorization UI** for user approval
3. **Manage session lifecycle** properly
4. **Add proper error handling** and logging
5. **Test with multiple DApps** to ensure compatibility

### For DApp Developers

1. **Use the universal client library** for any language
2. **Handle connection errors** gracefully
3. **Implement user-friendly authorization** requests
4. **Cache wallet info** appropriately
5. **Test with multiple wallet types**

## Migration from dapp-utils

### For Existing DApps

**No changes required!** The protocol provides full backward compatibility:

```javascript
// Existing code works unchanged
XianWalletUtils.init();
const balance = await XianWalletUtils.getBalance("currency");
```

### Benefits of Migration

- **Multi-wallet support**: Works with desktop, CLI, and web wallets
- **Better performance**: Local HTTP is faster than extension messaging
- **More reliable**: Direct communication, no extension dependencies
- **Language agnostic**: Use Python, JavaScript, or any language

## Development & Testing

### Start Protocol Server

```bash
# Core dependencies only needed
python protocol/server.py
```

### Test with Client

```python
# Core dependencies only needed
from protocol.client import XianWalletClientSync

client = XianWalletClientSync("Test App")
client.connect(auto_approve=True)  # For testing only
print(client.get_wallet_info())
```

### Test Different Wallet Types

```bash
# Test desktop wallet example
python examples/wallets/desktop.py

# Test web wallet example
python examples/wallets/web.py

# Test CLI wallet example
python examples/wallets/cli.py start
```

### Run Examples

```bash
# Install example dependencies first
pip install flet      # For Flet examples
pip install reflex    # For Reflex examples

# Run Flet DApp example
python examples/dapps/universal_dapp.py

# Run Reflex DApp example
cd examples/dapps/
reflex run  # Assuming reflex_dapp.py is set up as Reflex app
```

## Troubleshooting

### Common Issues

**Connection Refused**
- Ensure wallet server is running on port 8545
- Check firewall settings

**Authorization Failed**
- Verify wallet is unlocked
- Check authorization request was approved

**Session Expired**
- Tokens expire after 1 hour by default
- Client will auto-reconnect

### Debug Mode

```bash
# Enable debug logging
export XIAN_WALLET_DEBUG=1
python wallets/desktop.py
```

## Future Enhancements

- **Hardware wallet support** via protocol adapters
- **Multi-network support** (mainnet, testnet, custom)
- **Enhanced security** with HSM integration
- **Browser extension version** of web wallet (optional)
- **Mobile wallet support** via Flet mobile apps
- **Cross-platform notifications** for transaction requests

---

**The Universal Wallet Protocol makes Xian wallet integration simple, secure, and unified across all platforms.**