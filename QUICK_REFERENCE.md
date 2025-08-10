# Xian Universal Protocol - Quick Reference

> **Cheat sheet for developers** | See README.md for complete documentation

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
from protocol import XianWalletClientSync

client = XianWalletClientSync("My DApp")
client.connect()  # Works with desktop, CLI, or web wallets
```

## 📡 Essential API

| Operation | Code |
|-----------|------|
| **Get wallet info** | `client.get_wallet_info()` |
| **Get balance** | `client.get_balance("currency")` |
| **Send transaction** | `client.send_transaction("currency", "transfer", {"to": "addr", "amount": 100})` |
| **Sign message** | `client.sign_message("Hello!")` |

## 🔗 HTTP Endpoints (localhost:8545)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/wallet/status` | Check availability |
| `GET` | `/api/v1/wallet/info` | Wallet info (auth required) |
| `GET` | `/api/v1/balance/{contract}` | Token balance (auth required) |
| `POST` | `/api/v1/transaction` | Send transaction (auth required) |
| `POST` | `/api/v1/sign` | Sign message (auth required) |

## 🏗️ Implement Wallet

```python
# Desktop Wallet
from protocol import WalletProtocolServer, WalletType
server = WalletProtocolServer(WalletType.DESKTOP)
server.wallet = your_wallet
server.run()  # Same for all wallet types: localhost:8545

# Web Wallet (Flet-based)
from protocol import WalletProtocolServer, WalletType
import flet as ft
server = WalletProtocolServer(WalletType.WEB)
server.wallet = your_wallet
# Run server in background + Flet web UI
ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080)

# CLI Wallet
python examples/wallets/cli.py create
python examples/wallets/cli.py start
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
| 423 | Wallet locked | Unlock wallet |
| 404 | Not found | Start wallet on port 8545 |

## 🧪 Quick Test

```python
from protocol import check_wallet_available_sync

if check_wallet_available_sync():
    client = XianWalletClientSync("Test")
    client.connect(auto_approve=True)
    print(f"Connected to {client.get_wallet_info().wallet_type} wallet")
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
python examples/wallets/desktop.py    # Desktop
python examples/wallets/web.py        # Web  
python examples/wallets/cli.py start  # CLI

# Run DApp examples
python examples/dapps/universal_dapp.py  # Flet
cd examples/dapps && reflex run          # Reflex
```

---

📚 **For complete documentation, implementation guides, and examples**: See [README.md](README.md)