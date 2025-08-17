"""
Tests for network configuration functionality.
"""

import pytest
from xian_uwp.server import WalletProtocolServer
from xian_uwp.models import WalletType
from xian_uwp.client import WalletProtocolError


class TestNetworkConfiguration:
    """Test network configuration functionality."""

    @pytest.mark.unit
    def test_server_creation_without_network_config(self):
        """Test server can be created without network configuration."""
        server = WalletProtocolServer(wallet_type=WalletType.DESKTOP)
        
        assert server.network_url is None
        assert server.chain_id is None
        assert server.wallet_type == WalletType.DESKTOP

    @pytest.mark.unit
    def test_server_creation_with_network_config(self):
        """Test server can be created with network configuration."""
        network_url = "https://mainnet.xian.org"
        chain_id = "xian-mainnet"
        
        server = WalletProtocolServer(
            wallet_type=WalletType.DESKTOP,
            network_url=network_url,
            chain_id=chain_id
        )
        
        assert server.network_url == network_url
        assert server.chain_id == chain_id

    @pytest.mark.unit
    def test_configure_network_method(self):
        """Test network configuration can be set after creation."""
        server = WalletProtocolServer(wallet_type=WalletType.DESKTOP)
        
        # Initially no network config
        assert server.network_url is None
        assert server.chain_id is None
        
        # Configure network
        network_url = "https://testnet.xian.org"
        chain_id = "xian-testnet"
        server.configure_network(network_url, chain_id)
        
        assert server.network_url == network_url
        assert server.chain_id == chain_id

    @pytest.mark.unit
    def test_network_validation_without_config(self):
        """Test network validation fails when not configured."""
        server = WalletProtocolServer(wallet_type=WalletType.DESKTOP)
        
        with pytest.raises(WalletProtocolError, match="Network configuration not set"):
            server._validate_network_config()

    @pytest.mark.unit
    def test_network_validation_with_partial_config(self):
        """Test network validation fails with partial configuration."""
        server = WalletProtocolServer(wallet_type=WalletType.DESKTOP)
        
        # Only set network URL
        server.network_url = "https://testnet.xian.org"
        with pytest.raises(WalletProtocolError, match="Network configuration not set"):
            server._validate_network_config()
        
        # Only set chain ID
        server.network_url = None
        server.chain_id = "xian-testnet"
        with pytest.raises(WalletProtocolError, match="Network configuration not set"):
            server._validate_network_config()

    @pytest.mark.unit
    def test_network_validation_with_complete_config(self):
        """Test network validation passes with complete configuration."""
        server = WalletProtocolServer(wallet_type=WalletType.DESKTOP)
        server.configure_network("https://testnet.xian.org", "xian-testnet")
        
        # Should not raise an exception
        server._validate_network_config()

    @pytest.mark.unit
    def test_network_reconfiguration(self):
        """Test network can be reconfigured."""
        server = WalletProtocolServer(wallet_type=WalletType.DESKTOP)
        
        # Initial configuration
        server.configure_network("https://testnet.xian.org", "xian-testnet")
        assert server.network_url == "https://testnet.xian.org"
        assert server.chain_id == "xian-testnet"
        
        # Reconfigure
        server.configure_network("https://mainnet.xian.org", "xian-mainnet")
        assert server.network_url == "https://mainnet.xian.org"
        assert server.chain_id == "xian-mainnet"