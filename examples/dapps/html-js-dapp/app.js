/**
 * Xian DApp - Main Application Logic
 * Demonstrates how to use the Xian Universal Wallet Protocol with pure JavaScript
 */

class XianDApp {
    constructor() {
        this.client = null;
        this.isConnected = false;
        this.walletInfo = null;
        this.balance = null;
        
        this.initializeUI();
        this.bindEvents();
    }

    initializeUI() {
        // Get UI elements
        this.elements = {
            connectBtn: document.getElementById('connectBtn'),
            disconnectBtn: document.getElementById('disconnectBtn'),
            statusIndicator: document.getElementById('statusIndicator'),
            statusText: document.getElementById('statusText'),
            walletAddress: document.getElementById('walletAddress'),
            walletBalance: document.getElementById('walletBalance'),
            walletNetwork: document.getElementById('walletNetwork'),
            
            // Transaction form
            recipientInput: document.getElementById('recipientInput'),
            amountInput: document.getElementById('amountInput'),
            sendBtn: document.getElementById('sendBtn'),
            
            // Message signing
            messageInput: document.getElementById('messageInput'),
            signBtn: document.getElementById('signBtn'),
            
            // Results
            transactionResult: document.getElementById('transactionResult'),
            signatureResult: document.getElementById('signatureResult'),
            
            // Logs
            logContainer: document.getElementById('logContainer')
        };

        this.updateUI();
    }

    bindEvents() {
        this.elements.connectBtn.addEventListener('click', () => this.connectWallet());
        this.elements.disconnectBtn.addEventListener('click', () => this.disconnectWallet());
        this.elements.sendBtn.addEventListener('click', () => this.sendTransaction());
        this.elements.signBtn.addEventListener('click', () => this.signMessage());
        
        // Auto-refresh balance every 30 seconds when connected
        setInterval(() => {
            if (this.isConnected) {
                this.refreshBalance();
            }
        }, 30000);
    }

    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        logEntry.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${message}`;
        
        this.elements.logContainer.appendChild(logEntry);
        this.elements.logContainer.scrollTop = this.elements.logContainer.scrollHeight;
        
        // Keep only last 50 log entries
        while (this.elements.logContainer.children.length > 50) {
            this.elements.logContainer.removeChild(this.elements.logContainer.firstChild);
        }
    }

    updateUI() {
        if (this.isConnected) {
            this.elements.connectBtn.style.display = 'none';
            this.elements.disconnectBtn.style.display = 'inline-block';
            this.elements.statusIndicator.className = 'status-indicator connected';
            this.elements.statusText.textContent = 'Connected';
            
            if (this.walletInfo) {
                this.elements.walletAddress.textContent = this.walletInfo.truncated_address || this.walletInfo.address;
                this.elements.walletNetwork.textContent = this.walletInfo.network || 'Unknown';
            }
            
            if (this.balance !== null) {
                this.elements.walletBalance.textContent = `${this.balance.balance} ${this.balance.symbol || 'TAU'}`;
            }
            
            // Enable transaction controls
            this.elements.sendBtn.disabled = false;
            this.elements.signBtn.disabled = false;
        } else {
            this.elements.connectBtn.style.display = 'inline-block';
            this.elements.disconnectBtn.style.display = 'none';
            this.elements.statusIndicator.className = 'status-indicator disconnected';
            this.elements.statusText.textContent = 'Not Connected';
            
            this.elements.walletAddress.textContent = '-';
            this.elements.walletBalance.textContent = '-';
            this.elements.walletNetwork.textContent = '-';
            
            // Disable transaction controls
            this.elements.sendBtn.disabled = true;
            this.elements.signBtn.disabled = true;
        }
    }

    async connectWallet() {
        this.log('Attempting to connect to wallet...', 'info');
        this.elements.connectBtn.disabled = true;
        this.elements.connectBtn.textContent = 'Connecting...';

        try {
            // Initialize client
            this.client = new XianWalletClient(
                'HTML/JS DApp Demo',
                window.location.origin,
                'http://127.0.0.1:8545',
                ['wallet_info', 'balance', 'transactions', 'sign_message']
            );

            this.log('Requesting wallet authorization...', 'info');
            this.log('Please check your wallet and approve the connection request.', 'warning');

            // Connect to wallet
            const result = await this.client.connect();
            
            this.isConnected = true;
            this.walletInfo = result.walletInfo;
            
            this.log(`Successfully connected to ${this.walletInfo.wallet_type} wallet`, 'success');
            this.log(`Wallet address: ${this.walletInfo.address}`, 'info');
            
            // Get initial balance
            await this.refreshBalance();
            
            this.updateUI();
            
        } catch (error) {
            this.log(`Connection failed: ${error.message}`, 'error');
            this.isConnected = false;
            this.client = null;
            this.updateUI();
        } finally {
            this.elements.connectBtn.disabled = false;
            this.elements.connectBtn.textContent = 'Connect Wallet';
        }
    }

    disconnectWallet() {
        if (this.client) {
            this.client.disconnect();
        }
        
        this.client = null;
        this.isConnected = false;
        this.walletInfo = null;
        this.balance = null;
        
        this.log('Disconnected from wallet', 'info');
        this.updateUI();
        
        // Clear results
        this.elements.transactionResult.innerHTML = '';
        this.elements.signatureResult.innerHTML = '';
    }

    async refreshBalance() {
        if (!this.isConnected || !this.client) return;

        try {
            this.balance = await this.client.getBalance('currency');
            this.updateUI();
        } catch (error) {
            this.log(`Failed to refresh balance: ${error.message}`, 'error');
        }
    }

    async sendTransaction() {
        const recipient = this.elements.recipientInput.value.trim();
        const amount = this.elements.amountInput.value.trim();

        if (!recipient || !amount) {
            this.log('Please enter both recipient address and amount', 'error');
            return;
        }

        if (isNaN(amount) || parseFloat(amount) <= 0) {
            this.log('Please enter a valid amount', 'error');
            return;
        }

        this.elements.sendBtn.disabled = true;
        this.elements.sendBtn.textContent = 'Sending...';
        
        try {
            this.log(`Sending ${amount} TAU to ${recipient}...`, 'info');
            
            const result = await this.client.sendTransaction(
                'currency',
                'transfer',
                {
                    to: recipient,
                    amount: parseFloat(amount)
                },
                50000
            );

            if (result.success) {
                this.log(`Transaction successful! Hash: ${result.transaction_hash}`, 'success');
                this.elements.transactionResult.innerHTML = `
                    <div class="result-success">
                        <h4>Transaction Successful</h4>
                        <p><strong>Hash:</strong> ${result.transaction_hash}</p>
                        <p><strong>Amount:</strong> ${amount} TAU</p>
                        <p><strong>Recipient:</strong> ${recipient}</p>
                    </div>
                `;
                
                // Clear form and refresh balance
                this.elements.recipientInput.value = '';
                this.elements.amountInput.value = '';
                await this.refreshBalance();
                
            } else {
                const errorMsg = result.errors ? result.errors.join(', ') : 'Unknown error';
                this.log(`Transaction failed: ${errorMsg}`, 'error');
                this.elements.transactionResult.innerHTML = `
                    <div class="result-error">
                        <h4>Transaction Failed</h4>
                        <p>${errorMsg}</p>
                    </div>
                `;
            }
            
        } catch (error) {
            this.log(`Transaction error: ${error.message}`, 'error');
            this.elements.transactionResult.innerHTML = `
                <div class="result-error">
                    <h4>Transaction Error</h4>
                    <p>${error.message}</p>
                </div>
            `;
        } finally {
            this.elements.sendBtn.disabled = false;
            this.elements.sendBtn.textContent = 'Send Transaction';
        }
    }

    async signMessage() {
        const message = this.elements.messageInput.value.trim();

        if (!message) {
            this.log('Please enter a message to sign', 'error');
            return;
        }

        this.elements.signBtn.disabled = true;
        this.elements.signBtn.textContent = 'Signing...';

        try {
            this.log(`Signing message: "${message}"`, 'info');
            
            const result = await this.client.signMessage(message);
            
            this.log('Message signed successfully', 'success');
            this.elements.signatureResult.innerHTML = `
                <div class="result-success">
                    <h4>Message Signed</h4>
                    <p><strong>Message:</strong> ${result.message}</p>
                    <p><strong>Signature:</strong> <code>${result.signature}</code></p>
                    <p><strong>Signer:</strong> ${result.address}</p>
                </div>
            `;
            
        } catch (error) {
            this.log(`Signing failed: ${error.message}`, 'error');
            this.elements.signatureResult.innerHTML = `
                <div class="result-error">
                    <h4>Signing Failed</h4>
                    <p>${error.message}</p>
                </div>
            `;
        } finally {
            this.elements.signBtn.disabled = false;
            this.elements.signBtn.textContent = 'Sign Message';
        }
    }
}

// Initialize the DApp when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.dapp = new XianDApp();
});