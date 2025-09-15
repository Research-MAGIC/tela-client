"""
pytest configuration and fixtures
"""

import os
import pytest
from pathlib import Path

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Handle variable substitution
                    if value.startswith('${') and value.endswith('}'):
                        var_name = value[2:-1]
                        value = os.environ.get(var_name, value)
                    os.environ[key] = value

# Load environment variables at import time
load_env_file()


@pytest.fixture(scope="session")
def api_credentials():
    """Provide API credentials for testing"""
    return {
        "api_key": os.getenv("TELAOS_API_KEY") or os.getenv("TELAOS_ACCESS_TOKEN"),
        "organization": os.getenv("TELAOS_ORG_ID") or os.getenv("ORG_ID"),
        "project": os.getenv("TELAOS_PROJECT_ID") or os.getenv("PROJ_ID")
    }


@pytest.fixture
def tela_client(api_credentials):
    """Provide a Tela client for testing"""
    from tela import Tela
    
    client = Tela(
        api_key=api_credentials["api_key"],
        organization=api_credentials["organization"],
        project=api_credentials["project"],
        enable_history=True
    )
    
    yield client
    
    # Cleanup: clear any test conversations
    try:
        conversations = client.list_conversations()
        for conv_id in conversations:
            if conv_id.startswith("test-") or "test" in conv_id:
                client.history.delete_conversation(conv_id)
    except:
        pass


@pytest.fixture
async def async_tela_client(api_credentials):
    """Provide an AsyncTela client for testing"""
    from tela import AsyncTela
    
    client = AsyncTela(
        api_key=api_credentials["api_key"],
        organization=api_credentials["organization"],
        project=api_credentials["project"],
        enable_history=True
    )
    
    yield client
    
    # Cleanup
    try:
        conversations = client.list_conversations()
        for conv_id in conversations:
            if conv_id.startswith("test-") or "test" in conv_id:
                client.history.delete_conversation(conv_id)
    except:
        pass
    
    await client.close()


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", 
        "integration: marks tests as integration tests requiring API credentials"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow running"
    )