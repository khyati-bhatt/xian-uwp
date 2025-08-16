/**
 * Xian Universal Wallet Protocol - JavaScript Client
 * 
 * This client library enables any web application to connect to Xian wallets
 * through the Universal Wallet Protocol HTTP API.
 * 
 * Features:
 * - Works with any wallet type (CLI, Desktop, Web)
 * - Session-based authentication
 * - Comprehensive error handling
 * - Real-time event support
 * - CORS-enabled for server-hosted DApps
 */

class XianWalletClient {
    constructor(appName, appUrl = null, serverUrl = 'http://localhost:8545', permissions = []) {
        this.appName = appName;
        this.appUrl = appUrl || window.location.origin;
        this.serverUrl = serverUrl;
        this.permissions = permissions.length > 0 ? permissions : [
            'wallet_info', 'balance', 'transactions', 'sign_message'
        ];
        
        this.sessionToken = null;
        this.connected = false;
        this.eventSource = null;
        
        // Bind methods to preserve 'this' context
        this.connect = this.connect.bind(this);
        this.disconnect = this.disconnect.bind(this);
        this.makeRequest = this.makeRequest.bind(this);
    }

    /**
     * Test connection to wallet server and check CORS configuration
     */
    async testConnection() {
        try {
            const response = await fetch(`${this.serverUrl}/api/v1/wallet/status`, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Origin': this.appUrl
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            return {
                success: true,
                available: data.available,
                corsEnabled: response.headers.get('Access-Control-Allow-Origin') !== null,
                walletType: data.wallet_type,
                network: data.network
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                corsEnabled: false
            };
        }
    }

    /**
     * Connect to the wallet with authorization flow
     */
    async connect() {
        try {
            // Step 1: Check wallet status
            const status = await this.makeRequest('/api/v1/wallet/status');
            
            if (!status.available) {
                throw new Error('Wallet is not available. Please ensure your wallet is running and unlocked.');
            }

            // Step 2: Request authorization
            const authRequest = {
                app_name: this.appName,
                app_url: this.appUrl,
                permissions: this.permissions
            };

            const authResponse = await this.makeRequest('/api/v1/auth/request', 'POST', authRequest);
            
            if (!authResponse.request_id) {
                throw new Error('Failed to create authorization request');
            }

            // Step 3: Poll for approval
            const session = await this.pollForApproval(authResponse.request_id);
            
            if (session.status === 'approved') {
                this.sessionToken = session.token;
                this.connected = true;
                return true;
            } else {
                throw new Error('Authorization was denied or timed out');
            }

        } catch (error) {
            this.connected = false;
            this.sessionToken = null;
            throw error;
        }
    }

    /**
     * Poll for authorization approval
     */
    async pollForApproval(requestId, maxAttempts = 30, interval = 1000) {
        for (let attempt = 0; attempt < maxAttempts; attempt++) {
            try {
                const session = await this.makeRequest(`/api/v1/auth/session/${requestId}`);
                
                if (session.status === 'approved') {
                    return session;
                } else if (session.status === 'denied') {
                    throw new Error('Authorization denied by user');
                }
                
                // Wait before next attempt
                await new Promise(resolve => setTimeout(resolve, interval));
                
            } catch (error) {
                if (error.message.includes('404')) {
                    // Session not found yet, continue polling
                    await new Promise(resolve => setTimeout(resolve, interval));
                    continue;
                } else {
                    throw error;
                }
            }
        }
        
        throw new Error('Authorization timeout - please try again');
    }

    /**
     * Disconnect from wallet
     */
    async disconnect() {
        if (this.sessionToken) {
            try {
                await this.makeRequest('/api/v1/auth/logout', 'POST');
            } catch (error) {
                console.warn('Error during logout:', error);
            }
        }
        
        this.sessionToken = null;
        this.connected = false;
        
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }

    /**
     * Get wallet information
     */
    async getWalletInfo() {
        this.ensureConnected();
        return await this.makeRequest('/api/v1/wallet/info');
    }

    /**
     * Get balance for a specific contract
     */
    async getBalance(contract = 'currency') {
        this.ensureConnected();
        return await this.makeRequest(`/api/v1/wallet/balance/${contract}`);
    }

    /**
     * Send a transaction
     */
    async sendTransaction(contract, function_name, kwargs, stamps = 50000) {
        this.ensureConnected();
        
        const transaction = {
            contract,
            function: function_name,
            kwargs,
            stamps
        };
        
        return await this.makeRequest('/api/v1/wallet/transaction', 'POST', transaction);
    }

    /**
     * Sign a message
     */
    async signMessage(message) {
        this.ensureConnected();
        
        const signRequest = {
            message: message
        };
        
        return await this.makeRequest('/api/v1/wallet/sign', 'POST', signRequest);
    }

    /**
     * Get transaction history
     */
    async getTransactionHistory(limit = 50) {
        this.ensureConnected();
        return await this.makeRequest(`/api/v1/wallet/transactions?limit=${limit}`);
    }

    /**
     * Listen for real-time events
     */
    async listenForEvents(onEvent) {
        this.ensureConnected();
        
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        const eventUrl = `${this.serverUrl}/api/v1/wallet/events`;
        this.eventSource = new EventSource(eventUrl);
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onEvent(data);
            } catch (error) {
                console.error('Error parsing event data:', error);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('EventSource error:', error);
        };
        
        return this.eventSource;
    }

    /**
     * Make HTTP request to wallet server
     */
    async makeRequest(endpoint, method = 'GET', body = null) {
        const url = `${this.serverUrl}${endpoint}`;
        
        const headers = {
            'Content-Type': 'application/json',
            'Origin': this.appUrl
        };
        
        if (this.sessionToken) {
            headers['Authorization'] = `Bearer ${this.sessionToken}`;
        }

        const config = {
            method,
            headers,
            credentials: 'include'
        };

        if (body) {
            config.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                
                try {
                    const errorData = await response.json();
                    if (errorData.detail) {
                        errorMessage = errorData.detail;
                    }
                } catch (e) {
                    // Use default error message
                }
                
                throw new Error(errorMessage);
            }
            
            return await response.json();
            
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Unable to connect to wallet server. Please ensure your wallet is running on localhost:8545 with CORS enabled.');
            }
            throw error;
        }
    }

    /**
     * Ensure client is connected
     */
    ensureConnected() {
        if (!this.connected || !this.sessionToken) {
            throw new Error('Not connected to wallet. Please call connect() first.');
        }
    }

    /**
     * Get connection status
     */
    isConnected() {
        return this.connected && this.sessionToken !== null;
    }

    /**
     * Get current session token
     */
    getSessionToken() {
        return this.sessionToken;
    }

    /**
     * Set session token (for restoring sessions)
     */
    setSessionToken(token) {
        this.sessionToken = token;
        this.connected = token !== null;
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = XianWalletClient;
} else if (typeof window !== 'undefined') {
    window.XianWalletClient = XianWalletClient;
}