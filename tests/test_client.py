import pytest
from unittest.mock import Mock, patch
from tela import Tela, AsyncTela
from tela._exceptions import AuthenticationError, RateLimitError


class TestTelaClient:
    """Test suite for Tela client"""
    
    def test_client_initialization_with_params(self):
        """Test client initialization with parameters"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        assert client.api_key == "test-key"
        assert client.organization == "test-org"
        assert client.project == "test-project"
    
    def test_client_initialization_with_env(self, monkeypatch):
        """Test client initialization with environment variables"""
        monkeypatch.setenv("TELAOS_API_KEY", "env-key")
        monkeypatch.setenv("TELAOS_ORG_ID", "env-org")
        monkeypatch.setenv("TELAOS_PROJECT_ID", "env-project")
        
        client = Tela()
        assert client.api_key == "env-key"
        assert client.organization == "env-org"
        assert client.project == "env-project"
    
    def test_client_missing_credentials(self, monkeypatch):
        """Test that missing credentials raise AuthenticationError"""
        # Clear environment variables for this test
        monkeypatch.delenv("TELAOS_API_KEY", raising=False)
        monkeypatch.delenv("TELAOS_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("TELAOS_ORG_ID", raising=False)
        monkeypatch.delenv("ORG_ID", raising=False)
        monkeypatch.delenv("TELAOS_PROJECT_ID", raising=False)
        monkeypatch.delenv("PROJ_ID", raising=False)
        
        with pytest.raises(AuthenticationError):
            Tela(api_key=None, organization="org", project="proj")
    
    def test_conversation_creation(self):
        """Test conversation creation"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        conv = client.create_conversation("test-conv")
        assert conv.id == "test-conv"
        assert conv.message_count == 0
    
    def test_history_management(self):
        """Test history manager"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project",
            enable_history=True
        )
        
        conv = client.create_conversation("test-history")
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi there!")
        
        assert conv.message_count == 2
        assert client.get_conversation("test-history") == conv