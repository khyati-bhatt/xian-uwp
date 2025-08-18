# Server-Hosted DApp → Local Wallet Demo

This example demonstrates the **real-world scenario** where a DApp is hosted on a server (like Vercel, Netlify, AWS, or your own domain) but needs to connect to users' **local Xian wallets**.

## 🌐 Architecture

```
┌─────────────────────┐    CORS-enabled     ┌─────────────────────┐
│   Server-Hosted     │    HTTP Requests    │   User's Local      │
│   DApp              │ ◄─────────────────► │   Wallet            │
│                     │                     │                     │
│ • Vercel/Netlify    │                     │ • localhost:8545    │
│ • Your domain       │                     │ • Desktop/CLI/Web   │
│ • Any web host      │                     │ • CORS configured   │
└─────────────────────┘                     └─────────────────────┘
```

## ✨ Key Features

- **Real-world deployment scenario**: DApp hosted on external server
- **CORS-enabled communication**: Secure cross-origin requests
- **Universal wallet support**: Works with any Xian wallet type
- **Production-ready**: Includes proper error handling and user guidance
- **Interactive demo**: Wallet connection with address and balance display
- **Responsive design**: Works on desktop and mobile devices

## 🚀 Quick Start

### 1. Deploy the DApp

You can deploy this DApp to any web hosting service:

#### Option A: Vercel
```bash
# Clone and deploy
git clone <repository>
cd examples/dapps/server-hosted-dapp
vercel --prod
```

#### Option B: Netlify
```bash
# Drag and drop the folder to Netlify dashboard
# Or use Netlify CLI
netlify deploy --prod --dir .
```

#### Option C: GitHub Pages
```bash
# Push to GitHub and enable Pages in repository settings
git add .
git commit -m "Add server-hosted DApp"
git push origin main
```

#### Option D: Local Testing
```bash
# Serve locally to simulate server hosting
cd examples/dapps/server-hosted-dapp
python -m http.server 8080
# Open http://localhost:8080
```

### 2. Configure Local Wallet with CORS

Users need to start their local wallet with CORS configured for your domain:

#### For Production Deployment
```python
from xian_uwp import create_server, CORSConfig

# Configure CORS for your specific domain
cors_config = CORSConfig.production([
    "https://your-dapp.vercel.app",
    "https://your-domain.com"
])

server = create_server(cors_config=cors_config)
server.run(host="0.0.0.0", port=8545)  # Allow external connections
```

#### For Local Testing
```python
from xian_uwp import create_server, CORSConfig

# Use localhost development configuration
cors_config = CORSConfig.localhost_dev()
server = create_server(cors_config=cors_config)
server.run()  # Defaults to 127.0.0.1:8545
```

### 3. Connect and Use

1. Open your deployed DApp in a browser
2. The DApp will automatically test CORS connectivity
3. Follow the setup instructions shown in the UI
4. Click "Connect to Local Wallet"
5. Approve the connection in your wallet
6. Use the demo features (send transactions, sign messages)

## 📋 Files Overview

- **`index.html`** - Main HTML page with comprehensive UI
- **`styles.css`** - Professional styling with responsive design
- **`xian-wallet-client.js`** - Universal JavaScript client library
- **`server-hosted-app.js`** - DApp-specific application logic
- **`README.md`** - This documentation

## 🔧 Technical Implementation

### CORS Configuration

The DApp automatically detects its origin and provides the correct CORS configuration:

```javascript
// Automatic origin detection
const origin = window.location.origin;

// Test CORS connectivity
const testClient = new XianWalletClient('CORS Test', origin);
const result = await testClient.testConnection();
```

### Connection Flow

1. **CORS Test**: Verify wallet server is accessible with proper CORS headers
2. **Status Check**: Confirm wallet is available and unlocked
3. **Authorization**: Request permissions from user's wallet
4. **Session**: Establish authenticated session with token
5. **Operations**: Perform wallet operations (balance, transactions, signing)

### Error Handling

Comprehensive error handling with user-friendly messages:

```javascript
try {
    await client.connect();
} catch (error) {
    if (error.message.includes('not available')) {
        // Wallet not running
    } else if (error.message.includes('denied')) {
        // User denied authorization
    } else if (error.message.includes('timeout')) {
        // Connection timeout
    }
}
```

## 🌍 Deployment Examples

### Vercel Deployment

1. **Create `vercel.json`**:
```json
{
  "functions": {},
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

2. **Deploy**:
```bash
vercel --prod
```

3. **Configure wallet CORS**:
```python
cors_config = CORSConfig.production(["https://your-app.vercel.app"])
```

### Netlify Deployment

1. **Create `_redirects`**:
```
/*    /index.html   200
```

2. **Deploy via drag-and-drop or CLI**

3. **Configure wallet CORS**:
```python
cors_config = CORSConfig.production(["https://your-app.netlify.app"])
```

### Custom Domain

1. **Deploy to your hosting service**
2. **Configure DNS**
3. **Update wallet CORS**:
```python
cors_config = CORSConfig.production([
    "https://mydapp.com",
    "https://www.mydapp.com"
])
```

## 🔒 Security Considerations

### Production CORS Configuration

**❌ Never use in production:**
```python
# DON'T: Allows any origin
cors_config = CORSConfig.development()
```

**✅ Always use specific origins:**
```python
# DO: Specific domains only
cors_config = CORSConfig.production([
    "https://mydapp.com",
    "https://app.mydapp.com"
])
```

### Network Security

- **Firewall**: Ensure port 8545 is accessible but secured
- **HTTPS**: Use HTTPS for production DApps
- **Origin Validation**: Wallet validates request origins
- **Session Tokens**: Time-limited authentication tokens

### User Education

The DApp includes clear instructions for users:

1. **Setup guidance**: Step-by-step wallet configuration
2. **Error messages**: Helpful troubleshooting information
3. **Security notes**: Explanation of CORS and local wallet benefits

## 🛠️ Customization

### Branding

Update the DApp with your branding:

```css
/* styles.css */
:root {
    --primary-color: #your-brand-color;
    --primary-hover: #your-brand-hover;
}

header h1 {
    background: linear-gradient(135deg, #your-color-1, #your-color-2);
}
```

### Functionality

Add custom features:

```javascript
// server-hosted-app.js
class ServerHostedDApp {
    async customFeature() {
        // Add your custom wallet interactions
        const result = await this.client.sendTransaction(
            'your_contract',
            'your_function',
            { param: 'value' }
        );
    }
}
```

### Configuration

Customize client settings:

```javascript
// Different permissions
this.client = new XianWalletClient(
    'Your DApp Name',
    window.location.origin,
    'http://localhost:8545',
    ['wallet_info', 'balance']  // Limited permissions
);

// Custom server URL (for development)
this.client = new XianWalletClient(
    'Your DApp Name',
    window.location.origin,
    'http://localhost:8546'  // Custom port
);
```

## 🧪 Testing

### Local Testing

1. **Start local server**:
```bash
python -m http.server 8080
```

2. **Start wallet with localhost CORS**:
```python
cors_config = CORSConfig.localhost_dev()
server = create_server(cors_config=cors_config)
server.run()
```

3. **Test in browser**: `http://localhost:8080`

### Production Testing

1. **Deploy to staging environment**
2. **Configure wallet with staging domain**
3. **Test all functionality**
4. **Deploy to production**

## 🔍 Troubleshooting

### Common Issues

1. **"CORS connection failed"**
   - Ensure wallet is running with correct CORS configuration
   - Check that your domain is in the allowed origins list
   - Verify firewall allows port 8545

2. **"Unable to connect to wallet server"**
   - Confirm wallet is running on localhost:8545
   - Check wallet is unlocked
   - Verify network connectivity

3. **"Authorization timeout"**
   - Look for approval dialog in wallet UI
   - Ensure wallet is not locked or busy
   - Try refreshing and connecting again

### Debug Mode

Enable debug logging:

```javascript
// Add to server-hosted-app.js
console.log('CORS test result:', result);
console.log('Connection attempt:', error);
```

## 🚀 Next Steps

1. **Deploy your own version** using the provided examples
2. **Customize the UI** to match your brand
3. **Add custom features** specific to your use case
4. **Test with different wallet types** (CLI, Desktop, Web)
5. **Share with users** and gather feedback

## 📚 Related Examples

- **`html-js-dapp/`** - Local development version
- **`web_cors_dapp.py`** - Python/Reflex server-hosted example
- **`universal_dapp.py`** - Flet-based universal DApp

## 💬 Support

For questions and support:
- Check the main README.md for protocol documentation
- Review QUICK_REFERENCE.md for API details
- Examine the JavaScript client library code
- Open issues on the repository for bugs or feature requests

---

**This example demonstrates the power of the Xian Universal Wallet Protocol: enabling any web technology to connect to any wallet type, regardless of where the DApp is hosted!** 🌐✨