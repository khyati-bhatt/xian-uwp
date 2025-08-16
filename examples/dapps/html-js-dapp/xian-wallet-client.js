/**
 * Xian Universal Wallet Protocol - JavaScript Client
 * Pure JavaScript implementation for browser-based DApps
 */

class XianWalletClient {
    constructor(appName, appUrl = 'http://localhost', serverUrl = 'http://127.0.0.1:8545', permissions = null) {
        this.appName = appName;
        this.appUrl = appUrl;
        this.serverUrl = serverUrl.replace(/\/$/, ''); // Remove trailing slash
        this.permissions = permissions || [
            'wallet_info',
            'balance', 
            'transactions',
            'sign_message'
        ];
        
        this.sessionToken = null;
        this.isConnected = false;
        this.walletInfo = null;
        
        // API endpoints
        this.endpoints = {
            WALLET_STATUS: '/api/v1/wallet/status',
            AUTH_REQUEST: '/api/v1/auth/request',
            AUTH_APPROVE: '/api/v1/auth/approve',
            AUTH_DENY: '/api/v1/auth/deny',
            WALLET_INFO: '/api/v1/wallet/info',
            BALANCE: '/api/v1/balance',
            TRANSACTION: '/api/v1/transaction',
            SIGN_MESSAGE: '/api/v1/sign'
        };
    }

    /**
     * Make HTTP request with error handling
     */
    async makeRequest(endpoint, options = {}) {
        const url = `${this.serverUrl}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        };

        // Add session token if available
        if (this.sessionToken) {
            defaultOptions.headers['Authorization'] = `Bearer ${this.sessionToken}`;
        }

        const requestOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...(options.headers || {})
            }
        };

        try {
            const response = await fetch(url, requestOptions);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            return data;
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Unable to connect to wallet. Make sure a Xian wallet is running on localhost:8545');
            }
            throw error;
        }
    }

    /**
     * Check if wallet is available
     */
    async checkWalletStatus() {
        try {
            const status = await this.makeRequest(this.endpoints.WALLET_STATUS);
            return status;
        } catch (error) {
            return { available: false, error: error.message };
        }
    }

    /**
     * Request authorization from wallet
     */
    async requestAuthorization() {
        const authRequest = {
            app_name: this.appName,
            app_url: this.appUrl,
            permissions: this.permissions,
            description: `${this.appName} requests access to your Xian wallet`
        };

        try {
            const response = await this.makeRequest(this.endpoints.AUTH_REQUEST, {
                method: 'POST',
                body: JSON.stringify(authRequest)
            });

            return response;
        } catch (error) {
            throw new Error(`Authorization request failed: ${error.message}`);
        }
    }

    /**
     * Poll for authorization approval
     */
    async pollForApproval(requestId, maxAttempts = 30, intervalMs = 2000) {
        for (let attempt = 0; attempt < maxAttempts; attempt++) {
            try {
                const response = await this.makeRequest(`${this.endpoints.AUTH_APPROVE}/${requestId}`);
                
                if (response.session_token) {
                    this.sessionToken = response.session_token;
                    this.isConnected = true;
                    return response;
                }
            } catch (error) {
                // Continue polling unless it's a permanent error
                if (error.message.includes('denied') || error.message.includes('expired')) {
                    throw error;
                }
            }

            // Wait before next attempt
            await new Promise(resolve => setTimeout(resolve, intervalMs));
        }

        throw new Error('Authorization timeout - user did not approve the request');
    }

    /**
     * Connect to wallet (full flow)
     */
    async connect() {
        try {
            // 1. Check wallet availability
            const status = await this.checkWalletStatus();
            if (!status.available) {
                throw new Error('Wallet is not available');
            }

            if (status.locked) {
                throw new Error('Wallet is locked. Please unlock it first.');
            }

            // 2. Request authorization
            const authResponse = await this.requestAuthorization();
            
            if (authResponse.request_id) {
                // 3. Wait for user approval
                const approval = await this.pollForApproval(authResponse.request_id);
                
                // 4. Get wallet info
                this.walletInfo = await this.getWalletInfo();
                
                return {
                    success: true,
                    sessionToken: this.sessionToken,
                    walletInfo: this.walletInfo
                };
            } else {
                throw new Error('Invalid authorization response');
            }
        } catch (error) {
            this.isConnected = false;
            this.sessionToken = null;
            throw error;
        }
    }

    /**
     * Disconnect from wallet
     */
    disconnect() {
        this.sessionToken = null;
        this.isConnected = false;
        this.walletInfo = null;
    }

    /**
     * Get wallet information
     */
    async getWalletInfo() {
        if (!this.isConnected) {
            throw new Error('Not connected to wallet');
        }

        try {
            const info = await this.makeRequest(this.endpoints.WALLET_INFO);
            this.walletInfo = info;
            return info;
        } catch (error) {
            throw new Error(`Failed to get wallet info: ${error.message}`);
        }
    }

    /**
     * Get token balance
     */
    async getBalance(contract = 'currency') {
        if (!this.isConnected) {
            throw new Error('Not connected to wallet');
        }

        try {
            const balance = await this.makeRequest(`${this.endpoints.BALANCE}/${contract}`);
            return balance;
        } catch (error) {
            throw new Error(`Failed to get balance: ${error.message}`);
        }
    }

    /**
     * Send transaction
     */
    async sendTransaction(contract, functionName, kwargs, stampsSupplied = 50000) {
        if (!this.isConnected) {
            throw new Error('Not connected to wallet');
        }

        const transactionRequest = {
            contract: contract,
            function: functionName,
            kwargs: kwargs,
            stamps_supplied: stampsSupplied
        };

        try {
            const result = await this.makeRequest(this.endpoints.TRANSACTION, {
                method: 'POST',
                body: JSON.stringify(transactionRequest)
            });
            return result;
        } catch (error) {
            throw new Error(`Transaction failed: ${error.message}`);
        }
    }

    /**
     * Sign message
     */
    async signMessage(message) {
        if (!this.isConnected) {
            throw new Error('Not connected to wallet');
        }

        const signRequest = {
            message: message
        };

        try {
            const signature = await this.makeRequest(this.endpoints.SIGN_MESSAGE, {
                method: 'POST',
                body: JSON.stringify(signRequest)
            });
            return signature;
        } catch (error) {
            throw new Error(`Message signing failed: ${error.message}`);
        }
    }

    /**
     * Get connection status
     */
    getConnectionStatus() {
        return {
            connected: this.isConnected,
            sessionToken: this.sessionToken,
            walletInfo: this.walletInfo
        };
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = XianWalletClient;
}