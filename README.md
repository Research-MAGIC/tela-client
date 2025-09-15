# Tela Client - Python SDK

Official Python SDK for the Tela API (Fabric by MAGIC Research) - OpenAI-compatible with advanced conversation history management.

## Features

- 🔄 **OpenAI SDK Compatible** - Easy migration from OpenAI
- 💬 **Conversation History** - Automatic tracking and management
- 📝 **Smart Summarization** - Best practices for conversation summaries
- 🌊 **Streaming Support** - Real-time responses with SSE
- ⚡ **Async/Await** - High-performance async operations
- 🛠️ **Tool Calling** - Function/tool support
- 🖼️ **Multimodal** - Image input support
- 📊 **JSON Mode** - Structured outputs
- 💾 **Persistence** - Save and load conversations

## Installation

```bash
pip install -e .
```

Or install from GitHub:

```bash
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

# With conversation history
response = client.chat.completions.create_with_history(
    user_message="What's the weather like?",
    conversation_id="weather-chat"
)
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
    model="wizard",  # Optional, defaults to "wizard"
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

### Automatic History Tracking

```python
# Create a conversation with automatic history
response = client.chat.completions.create_with_history(
    user_message="I need help with Python",
    conversation_id="python-help",
    system_message="You are a Python expert."
)

# Continue the conversation - context is maintained
response = client.chat.completions.create_with_history(
    user_message="How do I use decorators?",
    conversation_id="python-help"  # Same ID continues conversation
)
```

### Manual Conversation Management

```python
# Create a conversation
conv = client.create_conversation("support-ticket-123")

# Add messages
conv.add_user_message("I can't log in")
conv.add_assistant_message("Let me help you with that")

# Use conversation in completions
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "My username is john@example.com"}],
    conversation=conv,
    save_to_history=True,
    use_conversation_context=True
)
```

### Conversation Summarization

Following best practices from the documentation, conversations are formatted as DATA blocks:

```python
# Summarize a conversation
summary = client.chat.completions.summarize_conversation(
    conversation_id="support-ticket-123",
    format="paragraph"  # or "bullets" or "json"
)

# The SDK automatically formats conversations to prevent continuation
# Uses the best practice of treating logs as static data
```

### Context Window Management

```python
# Manage long conversations
conv = client.get_conversation("long-chat")

# Get messages that fit in context window
messages = conv.get_context_window(
    max_tokens=3000,
    preserve_system=True  # Keep system message
)

# Use with limited context
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Summarize our discussion"}],
    conversation=conv,
    context_window_tokens=3000
)
```

### Export and Import

```python
# Export conversation
data = client.export_conversation(
    "support-ticket-123",
    format="json"  # or "text" or "markdown"
)

# Save all conversations
client.history.save("conversations_backup.json")

# Load conversations
client.history.load("conversations_backup.json")
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
    model: str = "wizard",       # Model to use
    temperature: float = 1.0,    # Randomness (0-2)
    max_tokens: int = None,      # Max response length
    stream: bool = False,        # Enable streaming
    tools: List[Dict] = None,    # Available tools
    response_format: Dict = None, # JSON mode
    # ... more parameters
)
```

### Conversation Methods

```python
# Create conversation
conv = client.create_conversation(conversation_id: str = None)

# Get conversation
conv = client.get_conversation(conversation_id: str)

# List all conversations
ids = client.list_conversations()

# Summarize
summary = client.summarize_conversation(
    conversation_id: str,
    format: str = "paragraph"
)

# Export
data = client.export_conversation(
    conversation_id: str,
    format: str = "json"
)
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

- `basic_usage.py` - Basic chat completions
- `conversation_history.py` - History management
- `streaming.py` - Streaming responses
- `async_usage.py` - Async operations
- `function_calling.py` - Tool/function calling
- `json_mode.py` - Structured outputs
- `multimodal.py` - Image inputs
- `error_handling.py` - Error handling
- `advanced_usage.py` - Advanced features

## Support

- Documentation: https://docs.telaos.com
- GitHub: https://github.com/Research-MAGIC/tela-client
- Email: support@researchmagic.com

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