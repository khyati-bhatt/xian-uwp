/**
 * Server-Hosted DApp Application Logic
 * 
 * This demonstrates how a DApp hosted on a server (Vercel, Netlify, etc.)
 * can connect to a user's local Xian wallet using CORS.
 */

class ServerHostedDApp {
    constructor() {
        this.client = null;
        this.connected = false;
        
        // Initialize on DOM load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    async init() {
        this.setupUI();
        this.updateOriginInfo();
        await this.testCORSConnection();
        this.setupEventListeners();
        this.logMessage('DApp initialized and ready', 'info');
    }

    setupUI() {
        // Get DOM elements
        this.elements = {
            dappOrigin: document.getElementById('dappOrigin'),
            currentOrigin: document.getElementById('currentOrigin'),
            corsStatus: document.getElementById('corsStatus'),
            corsDetails: document.getElementById('corsDetails'),
            connectionIndicator: document.getElementById('connectionIndicator'),
            connectionText: document.getElementById('connectionText'),
            connectBtn: document.getElementById('connectBtn'),
            disconnectBtn: document.getElementById('disconnectBtn'),
            walletInfo: document.querySelector('.wallet-info'),

            walletAddress: document.getElementById('walletAddress'),
            walletBalance: document.getElementById('walletBalance'),
            walletNetwork: document.getElementById('walletNetwork'),
            walletType: document.getElementById('walletType'),
            refreshBtn: document.getElementById('refreshBtn'),
            resultsLog: document.getElementById('resultsLog'),
            clearLogBtn: document.getElementById('clearLogBtn')
        };
    }

    updateOriginInfo() {
        const origin = window.location.origin;
        this.elements.dappOrigin.textContent = origin;
        this.elements.currentOrigin.textContent = origin;
    }

    async testCORSConnection() {
        this.elements.corsStatus.className = 'status-indicator testing';
        this.elements.corsStatus.innerHTML = '<div class="spinner"></div><span>Testing CORS connection...</span>';

        // Create a test client
        const testClient = new XianWalletClient('CORS Test', window.location.origin);
        
        try {
            const result = await testClient.testConnection();
            
            if (result.success) {
                this.elements.corsStatus.className = 'status-indicator success';
                this.elements.corsStatus.innerHTML = '<span>✅ CORS connection successful!</span>';
                
                this.elements.corsDetails.innerHTML = `
                    <strong>Connection Details:</strong><br>
                    • Wallet Available: ${result.available ? 'Yes' : 'No'}<br>
                    • CORS Enabled: ${result.corsEnabled ? 'Yes' : 'No'}<br>
                    • Wallet Type: ${result.walletType || 'Unknown'}<br>
                    • Network: ${result.network || 'Unknown'}
                `;
                
                this.logMessage('CORS connection test successful', 'success');
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            this.elements.corsStatus.className = 'status-indicator error';
            this.elements.corsStatus.innerHTML = '<span>❌ CORS connection failed</span>';
            
            let errorDetails = `<strong>Error:</strong> ${error.message}<br><br>`;
            
            if (error.message.includes('fetch')) {
                errorDetails += `
                    <strong>Possible Solutions:</strong><br>
                    • Ensure your wallet is running on localhost:8545<br>
                    • Configure CORS with your domain: <code>${window.location.origin}</code><br>
                    • Use <code>host='0.0.0.0'</code> when starting the wallet server<br>
                    • Check firewall settings for port 8545
                `;
            }
            
            this.elements.corsDetails.innerHTML = errorDetails;
            this.logMessage(`CORS test failed: ${error.message}`, 'error');
        }
    }

    setupEventListeners() {
        this.elements.connectBtn.addEventListener('click', () => this.connectWallet());
        this.elements.disconnectBtn.addEventListener('click', () => this.disconnectWallet());
        this.elements.refreshBtn.addEventListener('click', () => this.refreshWalletInfo());
        this.elements.clearLogBtn.addEventListener('click', () => this.clearLog());
    }

    async connectWallet() {
        try {
            this.updateConnectionStatus('connecting', 'Connecting...');
            this.elements.connectBtn.disabled = true;
            
            // Create wallet client
            this.client = new XianWalletClient(
                'Server-Hosted DApp Demo',
                window.location.origin,
                'http://localhost:8545',
                ['wallet_info', 'balance']
            );
            
            this.logMessage('Requesting wallet connection...', 'info');
            
            // Connect to wallet
            await this.client.connect();
            
            this.connected = true;
            this.updateConnectionStatus('connected', 'Connected');
            this.elements.connectBtn.style.display = 'none';
            this.elements.disconnectBtn.style.display = 'inline-flex';
            
            // Show wallet sections
            this.elements.walletInfo.style.display = 'block';

            
            // Load wallet information
            await this.refreshWalletInfo();
            
            this.logMessage('Successfully connected to wallet!', 'success');
            
        } catch (error) {
            this.updateConnectionStatus('disconnected', 'Connection Failed');
            this.elements.connectBtn.disabled = false;
            this.logMessage(`Connection failed: ${error.message}`, 'error');
            
            // Show helpful error messages
            if (error.message.includes('not available')) {
                this.logMessage('Make sure your wallet is running and unlocked', 'warning');
            } else if (error.message.includes('denied')) {
                this.logMessage('Please approve the connection request in your wallet', 'warning');
            } else if (error.message.includes('timeout')) {
                this.logMessage('Connection timed out - please try again', 'warning');
            }
        }
    }

    async disconnectWallet() {
        try {
            if (this.client) {
                await this.client.disconnect();
            }
            
            this.connected = false;
            this.client = null;
            
            this.updateConnectionStatus('disconnected', 'Not Connected');
            this.elements.connectBtn.style.display = 'inline-flex';
            this.elements.connectBtn.disabled = false;
            this.elements.disconnectBtn.style.display = 'none';
            
            // Hide wallet sections
            this.elements.walletInfo.style.display = 'none';

            
            this.logMessage('Disconnected from wallet', 'info');
            
        } catch (error) {
            this.logMessage(`Disconnect error: ${error.message}`, 'error');
        }
    }

    async refreshWalletInfo() {
        if (!this.connected || !this.client) return;
        
        try {
            this.elements.refreshBtn.disabled = true;
            this.elements.refreshBtn.textContent = 'Refreshing...';
            
            // Get wallet info and balance
            const [walletInfo, balance] = await Promise.all([
                this.client.getWalletInfo(),
                this.client.getBalance('currency').catch(() => ({ balance: 'Error loading' }))
            ]);
            
            // Update UI
            this.elements.walletAddress.textContent = walletInfo.address || 'Unknown';
            this.elements.walletBalance.textContent = `${balance.balance || 'Error'} XIAN`;
            this.elements.walletNetwork.textContent = walletInfo.network || 'Unknown';
            this.elements.walletType.textContent = walletInfo.wallet_type || 'Unknown';
            
            this.logMessage('Wallet information refreshed', 'success');
            
        } catch (error) {
            this.logMessage(`Failed to refresh wallet info: ${error.message}`, 'error');
        } finally {
            this.elements.refreshBtn.disabled = false;
            this.elements.refreshBtn.textContent = 'Refresh Info';
        }
    }



    updateConnectionStatus(status, text) {
        this.elements.connectionIndicator.className = `status-dot ${status}`;
        this.elements.connectionText.textContent = text;
    }

    logMessage(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.innerHTML = `
            <span class="timestamp">${timestamp}</span>
            <span class="message">${message}</span>
        `;
        
        this.elements.resultsLog.appendChild(logEntry);
        this.elements.resultsLog.scrollTop = this.elements.resultsLog.scrollHeight;
    }

    clearLog() {
        this.elements.resultsLog.innerHTML = `
            <div class="log-entry info">
                <span class="timestamp">Ready</span>
                <span class="message">Log cleared - DApp ready for new operations</span>
            </div>
        `;
    }
}

// Utility function for copying code to clipboard
function copyToClipboard(button) {
    const codeBlock = button.parentElement;
    const code = codeBlock.querySelector('code');
    const text = code.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        setTimeout(() => {
            button.textContent = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
        button.textContent = 'Copy failed';
        setTimeout(() => {
            button.textContent = 'Copy';
        }, 2000);
    });
}

// Initialize the DApp
const dapp = new ServerHostedDApp();