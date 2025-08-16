# Xian Universal Wallet Protocol - HTML & JavaScript DApp

This example demonstrates how to integrate with the Xian Universal Wallet Protocol using pure HTML and JavaScript, without any frameworks like React, Vue, or Angular.

## Features

- **Pure HTML/CSS/JavaScript** - No build tools or frameworks required
- **Universal Wallet Support** - Works with CLI, Desktop, and Web wallets
- **Complete Integration** - Wallet connection, transactions, message signing
- **Real-time Updates** - Live balance updates and activity logging
- **Responsive Design** - Works on desktop and mobile devices
- **Error Handling** - Comprehensive error handling and user feedback

## Files

- `index.html` - Main HTML page with user interface
- `xian-wallet-client.js` - JavaScript client library for wallet communication
- `app.js` - Main application logic and UI management
- `styles.css` - CSS styling for the interface
- `README.md` - This documentation file

## Quick Start

### 1. Start a Xian Wallet

First, you need a running Xian wallet. You can use any of the example wallets:

```bash
# CLI Wallet (in daemon mode)
cd /path/to/xian-uwp
PYTHONPATH=. python examples/wallets/cli.py daemon

# Desktop Wallet
PYTHONPATH=. python examples/wallets/desktop.py

# Web Wallet
PYTHONPATH=. python examples/wallets/web.py
```

### 2. Serve the HTML Files

Since the JavaScript makes HTTP requests to `localhost:8545`, you need to serve the HTML files over HTTP (not file://) to avoid CORS issues. The wallet server is configured with CORS support for common development ports.

#### Option A: Python HTTP Server
```bash
cd examples/dapps/html-js-dapp
python -m http.server 8080
```

#### Option B: Node.js HTTP Server
```bash
cd examples/dapps/html-js-dapp
npx http-server -p 8080 -c-1
```

#### Option C: PHP Built-in Server
```bash
cd examples/dapps/html-js-dapp
php -S localhost:8080
```

#### Option D: Use Provided Ports (Recommended)
The wallet server is pre-configured for these development ports:
```bash
# Port 3000 (React/Next.js default)
python -m http.server 3000

# Port 5173 (Vite default)
python -m http.server 5173

# Port 51644 or 57158 (OpenHands environment)
python -m http.server 51644
```

### 3. Open in Browser

Navigate to `http://localhost:8080` in your web browser.

### 4. Connect and Use

1. Click "Connect Wallet"
2. Approve the connection in your wallet
3. Send transactions and sign messages!

## How It Works

### JavaScript Client Library

The `xian-wallet-client.js` file provides a JavaScript implementation of the Xian Universal Wallet Protocol client. It includes:

```javascript
// Initialize client
const client = new XianWalletClient(
    'My DApp',                    // App name
    'http://localhost:8080',      // App URL
    'http://127.0.0.1:8545',     // Wallet server URL
    ['wallet_info', 'balance', 'transactions', 'sign_message']  // Permissions
);

// Connect to wallet
await client.connect();

// Get wallet info
const info = await client.getWalletInfo();

// Get balance
const balance = await client.getBalance('currency');

// Send transaction
const result = await client.sendTransaction(
    'currency',
    'transfer',
    { to: 'recipient_address', amount: 10.0 },
    50000
);

// Sign message
const signature = await client.signMessage('Hello, Xian!');
```

### Authorization Flow

1. **Request Authorization**: DApp requests access with specific permissions
2. **User Approval**: Wallet shows approval dialog to user
3. **Session Token**: Wallet returns session token for authenticated requests
4. **API Calls**: DApp uses token for subsequent wallet operations

### API Endpoints Used

The JavaScript client communicates with these wallet endpoints:

- `GET /api/v1/wallet/status` - Check wallet availability
- `POST /api/v1/auth/request` - Request authorization
- `GET /api/v1/auth/approve/{request_id}` - Poll for approval
- `GET /api/v1/wallet/info` - Get wallet information
- `GET /api/v1/balance/{contract}` - Get token balance
- `POST /api/v1/transaction` - Send transaction
- `POST /api/v1/sign` - Sign message

## Error Handling

The client includes comprehensive error handling:

```javascript
try {
    await client.connect();
} catch (error) {
    if (error.message.includes('Unable to connect')) {
        // Wallet not running
    } else if (error.message.includes('locked')) {
        // Wallet is locked
    } else if (error.message.includes('denied')) {
        // User denied authorization
    }
}
```

## Customization

### Styling

Modify `styles.css` to customize the appearance:

```css
/* Change primary color */
.btn-primary {
    background: linear-gradient(135deg, #your-color 0%, #your-color-2 100%);
}

/* Customize cards */
.status-card {
    background: your-background;
    border-radius: your-radius;
}
```

### Functionality

Extend `app.js` to add new features:

```javascript
class XianDApp {
    // Add custom methods
    async getTokenList() {
        // Implement token listing
    }
    
    async addCustomToken(address) {
        // Implement token addition
    }
}
```

### Client Configuration

Modify `xian-wallet-client.js` for different configurations:

```javascript
// Custom server URL
const client = new XianWalletClient(
    'My DApp',
    window.location.origin,
    'http://custom-host:custom-port'  // Custom wallet server
);

// Custom permissions
const client = new XianWalletClient(
    'My DApp',
    window.location.origin,
    'http://127.0.0.1:8545',
    ['wallet_info', 'balance']  // Limited permissions
);
```

## Browser Compatibility

This example works in all modern browsers that support:

- ES6+ JavaScript (async/await, classes, arrow functions)
- Fetch API
- CSS Grid and Flexbox

Tested browsers:
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## CORS Configuration

The Xian Universal Wallet Protocol includes comprehensive CORS support for web-based DApps:

### Development Mode (Default)
The wallet server uses `CORSConfig.localhost_dev()` by default, which allows:
- Common development ports: 3000, 3001, 5000, 5173, 8000, 8080, 8081
- OpenHands environment ports: 51644, 57158
- Both `localhost` and `127.0.0.1` origins

### Production Mode
For production deployments, configure specific origins:
```python
from xian_uwp import create_server, CORSConfig

# Production CORS configuration
cors_config = CORSConfig.production([
    "https://mydapp.com",
    "https://app.mydapp.com"
])

server = create_server(cors_config=cors_config)
server.run(host="0.0.0.0", port=8545)
```

### Custom CORS Configuration
```python
from xian_uwp import CORSConfig

# Custom configuration
cors_config = CORSConfig(
    allow_origins=["http://localhost:3000", "https://mydapp.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600
)
```

## Security Considerations

- **HTTPS in Production**: Use HTTPS for production deployments
- **Input Validation**: Always validate user inputs before sending to wallet
- **Session Management**: Session tokens are stored in memory only
- **CORS Origins**: Configure specific origins in production, avoid wildcards
- **Origin Validation**: The wallet server validates request origins against allowed list

## Troubleshooting

### Connection Issues

1. **"Unable to connect to wallet"**
   - Ensure a Xian wallet is running on localhost:8545
   - Check that the wallet is unlocked
   - Verify no firewall is blocking the connection

2. **"Authorization timeout"**
   - Check the wallet UI for pending authorization requests
   - Ensure the wallet is not locked or busy
   - Try refreshing the page and connecting again

3. **CORS Errors**
   - Serve the HTML files over HTTP, not file://
   - Use a local web server (Python, Node.js, etc.)

### Transaction Issues

1. **"Insufficient balance"**
   - Check wallet balance is sufficient for transaction + gas
   - Verify the correct token contract address

2. **"Transaction failed"**
   - Check transaction parameters (recipient, amount)
   - Ensure wallet has enough stamps for gas
   - Verify network connectivity

## Integration with Other Frameworks

This pure JavaScript client can be easily integrated into other frameworks:

### React Integration
```javascript
import { useEffect, useState } from 'react';

function useXianWallet() {
    const [client, setClient] = useState(null);
    const [connected, setConnected] = useState(false);
    
    const connect = async () => {
        const walletClient = new XianWalletClient('React DApp');
        await walletClient.connect();
        setClient(walletClient);
        setConnected(true);
    };
    
    return { client, connected, connect };
}
```

### Vue Integration
```javascript
export default {
    data() {
        return {
            client: null,
            connected: false
        }
    },
    methods: {
        async connectWallet() {
            this.client = new XianWalletClient('Vue DApp');
            await this.client.connect();
            this.connected = true;
        }
    }
}
```

## Next Steps

- Explore the other example DApps (Flet, Reflex)
- Try different wallet types (CLI, Desktop, Web)
- Build your own DApp using this as a template
- Contribute improvements to the protocol

## Support

For questions and support:
- Check the main README.md for protocol documentation
- Review the QUICK_REFERENCE.md for API details
- Examine other example implementations
- Open issues on the repository for bugs or feature requests