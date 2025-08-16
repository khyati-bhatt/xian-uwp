# Xian Universal Protocol - Quick Reference

> **Cheat sheet for developers** | See README.md for complete documentation

**⚠️ Important**: Default port is **8545** (configurable). All wallet types use the same port.

**📁 Running Examples**: All examples require `PYTHONPATH=.` to import protocol modules correctly.

## ⚡ Installation

```bash
# Core protocol only
pip install fastapi uvicorn httpx websockets pydantic xian-py

# Add as needed:
pip install flet>=0.21.0          # Desktop wallets + Flet examples
pip install reflex>=0.6.0         # Reflex DApp examples
pip install click>=8.1.0          # CLI wallets  
pip install cryptography>=41.0.0  # Encrypted storage
```

## 🔌 Connect to Any Wallet

```python
# Synchronous client
from protocol.client import XianWalletClientSync

client = XianWalletClientSync(
    app_name="My DApp",
    app_url="http://localhost:3000",
    server_url="http://localhost:8545"  # Optional: custom port
)
if client.connect():
    # Works with desktop, CLI, or web wallets
    print("Connected!")

# Async client
from protocol.client import XianWalletClient
import asyncio

async def main():
    client = XianWalletClient("My DApp", "http://localhost:3000")
    if await client.connect():
        info = await client.get_wallet_info()
        print(f"Connected to {info.wallet_type}")

asyncio.run(main())
```

## 📡 Essential API

| Operation | Code |
|-----------|------|
| **Get wallet info** | `client.get_wallet_info()` |
| **Get balance** | `client.get_balance("currency")` |
| **Send transaction** | `client.send_transaction("currency", "transfer", {"to": "addr", "amount": 100})` |
| **Sign message** | `client.sign_message("Hello!")` |
| **Add token** | `client.add_token("contract_name", "TOKEN", "https://icon.url")` |

## 🔐 Permissions

| Permission | Allows |
|------------|--------|
| `wallet_info` | Get wallet address & type |
| `balance` | Check token balances |
| `transactions` | Send transactions |
| `sign_message` | Sign messages |
| `tokens` | Add custom tokens |

## 🔗 HTTP Endpoints (localhost:8545)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/wallet/status` | Check availability |
| `POST` | `/api/v1/auth/request` | Request authorization |
| `GET` | `/api/v1/wallet/info` | Wallet info (auth required) |
| `GET` | `/api/v1/balance/{contract}` | Token balance (auth required) |
| `POST` | `/api/v1/transaction` | Send transaction (auth required) |
| `POST` | `/api/v1/sign` | Sign message (auth required) |
| `POST` | `/api/v1/wallet/unlock` | Unlock wallet |
| `POST` | `/api/v1/wallet/lock` | Lock wallet |
| `WS` | `/ws/v1` | WebSocket for real-time events |

## 🏗️ Implement Wallet

```python
# Desktop Wallet
from protocol.server import WalletProtocolServer
from protocol.models import WalletType

server = WalletProtocolServer(
    wallet_type=WalletType.DESKTOP,
    host="127.0.0.1",
    port=8545  # Default port - all wallets use same port
)
server.wallet = your_wallet_instance
server.run()

# Web Wallet (Flet-based)
from protocol.server import WalletProtocolServer
from protocol.models import WalletType
import flet as ft

server = WalletProtocolServer(WalletType.WEB)
server.wallet = your_wallet_instance
# Run server in background + Flet web UI
ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080)

# CLI Wallet
PYTHONPATH=. python examples/wallets/cli.py create
PYTHONPATH=. python examples/wallets/cli.py start
```

## 🔄 WebSocket Events

```python
# Listen for real-time events
async def handle_events():
    async for event in client.listen_events():
        if event['type'] == 'transaction_submitted':
            print(f"TX submitted: {event['data']['hash']}")
        elif event['type'] == 'wallet_locked':
            print("Wallet was locked")
```

## 🌐 Legacy Compatibility

```javascript
// Existing dapp-utils code works unchanged
await XianWalletUtils.init();
const balance = await XianWalletUtils.getBalance("currency");
```

## ❌ Error Handling

| Error Code | Meaning | Fix |
|------------|---------|-----|
| 401 | Unauthorized | Reconnect for new token |
| 404 | Not found | Start wallet on port 8545 |
| 423 | Wallet locked | Unlock wallet |
| 500 | Server error | Check wallet logs |

## 🧪 Quick Test

```python
from protocol.utils import check_wallet_available_sync
from protocol.client import XianWalletClientSync

if check_wallet_available_sync():
    client = XianWalletClientSync(
        app_name="Test App",
        app_url="http://localhost:3000"
    )
    if client.connect(auto_approve=True):
        info = client.get_wallet_info()
        print(f"Connected to {info.wallet_type} wallet")
        print(f"Address: {info.address}")
```

## 🚨 Common Issues

```bash
# Check if wallet running
curl localhost:8545/api/v1/wallet/status

# Missing dependencies for examples
pip install flet>=0.21.0          # For Flet examples
pip install reflex>=0.6.0         # For Reflex examples

# Port in use
netstat -an | grep 8545

# Run wallet examples
PYTHONPATH=. python examples/wallets/desktop.py    # Desktop
PYTHONPATH=. python examples/wallets/web.py        # Web  
PYTHONPATH=. python examples/wallets/cli.py start  # CLI

# Run DApp examples
PYTHONPATH=. python examples/dapps/universal_dapp.py  # Flet
cd examples/dapps && PYTHONPATH=../.. reflex run # Reflex
```

---

📚 **For complete documentation, implementation guides, and examples**: See [README.md](README.md)