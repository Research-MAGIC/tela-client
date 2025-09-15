# Tela Client - Python SDK

Official Python SDK for the Tela API (Fabric by MAGIC Research) - OpenAI-compatible with conversation history management.

## Features

- 🔄 **OpenAI SDK Compatible** - Easy migration from OpenAI
- 💬 **Conversation History** - Manual conversation tracking and management
- 🌊 **Streaming Support** - Real-time responses with SSE
- ⚡ **Async/Await** - High-performance async operations
- 🛠️ **Tool Calling** - Function/tool support
- 🖼️ **Multimodal** - Image input support
- 📊 **JSON Mode** - Structured outputs
- 💾 **Persistence** - Save and load conversations to JSON
- 🔍 **Model Discovery** - List and inspect available models

## Installation

```bash
# Install from source (development)
pip install -e .

# Or install from GitHub
pip install git+https://github.com/Research-MAGIC/tela-client.git
```

## Quick Start

```python
from tela import Tela

# Initialize client (reads from environment variables)
client = Tela()

# Simple chat
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)

# List available models
models = client.get_models()
print(f"Available models: {[model.id for model in models.data]}")
```

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
export TELAOS_API_KEY="your-api-key"
export TELAOS_ORG_ID="your-organization-id"
export TELAOS_PROJECT_ID="your-project-id"
```

### Client Initialization

```python
from tela import Tela

# Using environment variables (recommended)
client = Tela()

# Or with explicit credentials
client = Tela(
    api_key="your-api-key",
    organization="your-org-id",
    project="your-project-id",
    enable_history=True,  # Enable conversation tracking
    history_file="conversations.json"  # Persist conversations
)
```

## Core Features

### Basic Chat Completion

```python
response = client.chat.completions.create(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing"}
    ],
    model="qwen3-max",  # Use an available model
    temperature=0.5,
    max_tokens=5000
)

print(response.choices[0].message.content)
print(f"Tokens used: {response.usage.total_tokens}")
```

### Streaming Responses

```python
stream = client.chat.completions.create(
    messages=[{"role": "user", "content": "Write a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### Async Operations

```python
import asyncio
from tela import AsyncTela

async def main():
    client = AsyncTela()
    
    response = await client.chat.completions.create(
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```

## Conversation History Management

### Manual Conversation Management

```python
# Create a conversation
conv = client.create_conversation("support-ticket-123")

# Add messages manually
conv.add_message("user", "I can't log in")
conv.add_message("assistant", "Let me help you with that")

# Get conversation context for API calls
messages = client.get_conversation_context(conversation_id="support-ticket-123")

# Use in chat completions
response = client.chat.completions.create(
    messages=messages + [{"role": "user", "content": "My username is john@example.com"}]
)

# Add the response to conversation
conv.add_message("assistant", response.choices[0].message.content)
```

### Conversation Management

```python
# List all conversations
conversation_ids = client.list_conversations()
print(f"Found {len(conversation_ids)} conversations")

# Get a specific conversation
conv = client.get_conversation("support-ticket-123")
if conv:
    print(f"Conversation has {len(conv.messages)} messages")

# Save/Load conversations
client.history.save("backup.json")
client.history.load("backup.json")
```

## Advanced Features

### Tool/Function Calling

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }
}]

response = client.chat.completions.create(
    messages=[{"role": "user", "content": "What's the weather in NYC?"}],
    tools=tools,
    tool_choice="auto"
)

if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        print(f"Calling: {tool_call['function']['name']}")
        # Execute function and continue conversation
```

### JSON Mode

```python
response = client.chat.completions.create(
    messages=[
        {"role": "system", "content": "Output JSON only"},
        {"role": "user", "content": "List 3 programming languages"}
    ],
    response_format={"type": "json_object"},
    temperature=0  # For consistent output
)

import json
data = json.loads(response.choices[0].message.content)
```

### Multimodal (Images)

```python
import base64

def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{encode_image('image.jpg')}"
                }
            }
        ]
    }]
)
```

## Error Handling

```python
from tela import Tela
from tela._exceptions import (
    AuthenticationError,
    RateLimitError,
    APIError
)

try:
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "Hello"}]
    )
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except RateLimitError as e:
    print(f"Rate limited: {e}")
    # Implement exponential backoff
except APIError as e:
    print(f"API error: {e}")
```

## Migration from OpenAI

The Tela client is designed to be compatible with OpenAI's SDK:

```python
# OpenAI
from openai import OpenAI
client = OpenAI(api_key="sk-...")
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello"}]
)

# Tela (nearly identical!)
from tela import Tela
client = Tela(
    api_key="...",
    organization="...",  # Additional required
    project="..."        # Additional required
)
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello"}]
)
```

Key differences:
- Additional required headers: `organization` and `project`
- Default model: `"wizard"` instead of GPT models
- Base URL: `https://api.telaos.com/v1`
- Built-in conversation history management

## API Reference

### Client Initialization

```python
Tela(
    api_key: str = None,         # From TELAOS_API_KEY env
    organization: str = None,     # From TELAOS_ORG_ID env
    project: str = None,         # From TELAOS_PROJECT_ID env
    base_url: str = None,        # Override base URL
    timeout: float = 600.0,      # Request timeout
    max_retries: int = 2,        # Retry attempts
    enable_history: bool = True, # Enable history tracking
    history_file: str = None     # Persistence file
)
```

### Chat Completions

```python
client.chat.completions.create(
    messages: List[Dict],         # Required
    model: str = None,           # Model to use (auto-selected if None)
    temperature: float = 1.0,    # Randomness (0-2)
    max_tokens: int = None,      # Max response length
    stream: bool = False,        # Enable streaming
    tools: List[Dict] = None,    # Available tools
    response_format: Dict = None, # JSON mode
    # ... more parameters
)
```

### Available Methods

```python
# Model discovery
models = client.get_models()

# Conversation management
conv = client.create_conversation(conversation_id: str = None)
conv = client.get_conversation(conversation_id: str)
ids = client.list_conversations()
messages = client.get_conversation_context(conversation_id: str)

# History persistence
client.history.save(filename: str)
client.history.load(filename: str)
```

## Development

### Installation for Development

```bash
# Clone repository
git clone https://github.com/Research-MAGIC/tela-client.git
cd tela-client

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest tests/

# With coverage
pytest --cov=tela tests/

# Specific test
pytest tests/test_client.py -v
```

### Code Quality

```bash
# Format code
make format

# Run linters
make lint

# Type checking
make type-check

# All checks
make all
```

## Examples

See the `examples/` directory for complete examples:

- `basic_test.py` - Basic chat completions and model listing
- `conversation_history.py` - Manual conversation history management
- `streaming_cli.py` - Streaming responses in CLI
- `streaming_nicegui.py` - Streaming with NiceGUI interface
- `tool_calling_cli.py` - Tool/function calling in CLI
- `tool_calling_nicegui.py` - Tool calling with NiceGUI
- `endpoint_information.py` - Endpoint and model information
- `list_models.py` - Model discovery and capabilities
- `advanced_nicegui_test.py` - Advanced NiceGUI features
- `basic_nicegui_test.py` - Basic NiceGUI chat interface

## Support

- GitHub: https://github.com/Research-MAGIC/tela-client
- Email: rodrigo@researchmagic.com

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgments

- Built for the Fabric API by TelaOS
- Compatible with OpenAI SDK patterns
- Implements conversation best practices from official documentation