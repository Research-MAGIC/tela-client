import os
import sys
from pathlib import Path

def create_file(path, content):
    """Create a file with content"""
    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content)
    print(f"✓ Created {path}")

def setup_tela_client():
    """Set up the complete Tela client structure"""
    
    print("🚀 Setting up Tela Client...")
    print("-" * 40)
    
    # Check if we're in the right directory
    if Path("tela/_client.py").exists():
        print("✓ Found existing _client.py")
    else:
        print("⚠️  Warning: _client.py not found. Make sure you have it!")
    
    # Create directories
    dirs = [
        "tela/types/chat",
        "examples",
        "tests"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory {dir_path}")
    
    # Create all files with their content
    files = {
        # Core tela package files
        "tela/__init__.py": '''"""
tela/__init__.py
Tela Python Library with Conversation History Support
"""

from . import types
from ._client import Tela, AsyncTela, Client, AsyncClient
from ._version import __version__
from ._exceptions import (
    TelaError,
    APIError,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)
from ._history import (
    ConversationHistory,
    HistoryManager,
    Message,
    MessageRole,
)

__all__ = [
    "types",
    "Tela",
    "AsyncTela", 
    "Client",
    "AsyncClient",
    "ConversationHistory",
    "HistoryManager",
    "Message",
    "MessageRole",
    "TelaError",
    "APIError",
    "APIConnectionError",
    "APIStatusError",
    "APITimeoutError",
    "AuthenticationError",
    "BadRequestError",
    "ConflictError",
    "InternalServerError",
    "NotFoundError",
    "PermissionDeniedError",
    "RateLimitError",
    "UnprocessableEntityError",
    "__version__",
]
''',

        "tela/_version.py": '''"""
tela/_version.py
Version information for Tela SDK
"""

__version__ = "1.0.0"
''',

        "tela/py.typed": "# Marker file for PEP 561\n# This package supports type hints",
        
        "tela/types/__init__.py": '''"""
tela/types/__init__.py
Type exports for Tela SDK
"""

from .chat import (
    Chat,
    AsyncChat,
    Completions,
    AsyncCompletions,
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionChoice,
)

__all__ = [
    "Chat",
    "AsyncChat",
    "Completions", 
    "AsyncCompletions",
    "ChatCompletion",
    "ChatCompletionMessage",
    "ChatCompletionChoice",
]
''',

        # Configuration files
        "pyproject.toml": '''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "tela-client"
version = "1.0.0"
description = "The official Python library for the Tela API with conversation history support"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "TelaOS", email = "support@telaos.com"}
]
requires-python = ">=3.8"
dependencies = [
    "httpx>=0.23.0,<1",
    "typing-extensions>=4.5,<5",
    "pydantic>=2.0,<3",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.1.3,<8",
    "pytest-asyncio>=0.21.0,<1",
    "pytest-mock>=3.10.0,<4",
    "black>=22.3.0,<24",
    "mypy>=1.0,<2",
    "ruff>=0.1.0",
]
''',

        "requirements.txt": """httpx>=0.23.0,<1
typing-extensions>=4.5,<5
pydantic>=2.0,<3
""",

        "requirements-dev.txt": """pytest>=7.1.3,<8
pytest-asyncio>=0.21.0,<1
pytest-mock>=3.10.0,<4
black>=22.3.0,<24
mypy>=1.0,<2
ruff>=0.1.0
httpx>=0.23.0,<1
typing-extensions>=4.5,<5
pydantic>=2.0,<3
""",

        ".env.example": """# Tela API Configuration
TELAOS_API_KEY=your-api-key-here
TELAOS_ORG_ID=your-organization-id-here
TELAOS_PROJECT_ID=your-project-id-here

# Optional: Override base URL
# TELA_BASE_URL=https://api.telaos.com/v1

# Optional: History file location
# TELA_HISTORY_FILE=conversations.json
""",

        ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/

# Virtual environments
venv/
env/
.env

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store

# Project specific
conversations.json
*.conversation.json
temp/
tmp/
""",

        "tests/__init__.py": '"""Test suite for Tela client"""',
    }
    
    # Create all files
    for filepath, content in files.items():
        create_file(filepath, content)
    
    print("-" * 40)
    print("✅ Setup complete!")
    print("\nNext steps:")
    print("1. Create virtual environment: python -m venv venv")
    print("2. Activate it: source venv/bin/activate")
    print("3. Install package: pip install -e .")
    print("4. Copy .env.example to .env and add your credentials")
    print("5. Test: python -c 'from tela import Tela; print(\"Success!\")'")
    
    # Create a simple test file
    test_content = '''"""Quick test of Tela client setup"""
from tela import Tela

try:
    print("✓ Import successful")
    
    # Try to create client (will fail without credentials)
    try:
        client = Tela()
        print("✓ Client created with environment credentials")
    except Exception as e:
        print("⚠️  Client creation failed (expected without credentials)")
        print(f"   Set your credentials in .env file")
    
    print("\\n🎉 Basic setup verified!")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("   Run: pip install -e .")
'''
    
    create_file("test_setup.py", test_content)
    print("\n📝 Created test_setup.py - run it after installation")

if __name__ == "__main__":
    setup_tela_client()