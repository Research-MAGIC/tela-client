# Tela Client - Python SDK

Official Python SDK for the Tela API (Fabric by MAGIC Research) - OpenAI-compatible with conversation history management.

## Features

- 🔄 **OpenAI SDK Compatible** - Easy migration from OpenAI
- 💬 **Conversation History** - Manual and automatic conversation tracking
- 🗂️ **Server-Side Chat Management** - Create, list, update and sync server-side chats
- 🤖 **High-level Chat API** - `send_message()` with automatic context management
- 🌊 **Streaming Support** - Real-time responses with SSE
- ⚡ **Async/Await** - High-performance async operations
- 🛠️ **Tool Calling** - Function/tool support
- 🖼️ **Multimodal** - Image input support
- 📊 **JSON Mode** - Structured outputs
- 💾 **Export & Persistence** - Export conversations in multiple formats (JSON, text, markdown)
- 🔍 **Model Discovery** - List, inspect and get capabilities of available models
- 🔄 **History Sync** - Synchronize local conversation history with server-side chats
- 🎙️ **Audio Transcription** - Speech-to-text with Fabric Voice STT model
- 🔊 **Text-to-Speech** - Natural voice synthesis with Fabric Voice TTS model

## Installation

```bash
# Install from source (development)
pip install -e .

# Or install from GitHub
pip install git+https://github.com/Research-MAGIC/tela-client.git

# For UI examples (NiceGUI interfaces)
pip install -e ".[ui]"
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

### Advanced Conversation Management

```python
# High-level conversation method (handles context automatically)
response = client.send_message(
    message="How do I reset my password?",
    conversation_id="support-ticket-123"
)
print(response)

# List all conversations
conversation_ids = client.list_conversations()
print(f"Found {len(conversation_ids)} conversations")

# Get a specific conversation
conv = client.get_conversation("support-ticket-123")
if conv:
    print(f"Conversation has {len(conv.messages)} messages")

# Export conversation in different formats
json_data = client.export_conversation("support-ticket-123", format="json")
text_data = client.export_conversation("support-ticket-123", format="text")
markdown_data = client.export_conversation("support-ticket-123", format="markdown")

# Auto-save conversations (if persistence file configured in client init)
client.history.save()
```

## Server-Side Chat Management

### List Server-Side Chats

```python
# List all chats with pagination
chats = client.chats.list(page=1, page_size=10)
print(f"Found {len(chats.data)} chats on page {chats.page}")

for chat in chats.data:
    print(f"Chat {chat.id}: {chat.title} ({chat.message_count} messages)")
```

### Create and Manage Server-Side Chats

```python
# Create a new server-side chat
chat_response = client.chats.create(
    module_id="chat",
    message="Welcome to my project discussion!"
)
chat_id = chat_response["chat_id"]
print(f"Created chat: {chat_id}")

# Get chat details (if supported by API)
try:
    chat_details = client.chats.get(chat_id)
    print(f"Chat: {chat_details.title} - {chat_details.message_count} messages")
except Exception as e:
    print(f"Could not retrieve chat details: {e}")

# Note: Update functionality depends on API endpoint availability
```

### Sync Local History with Server-Side Chats

```python
# Automatically sync local conversation history with server-side chats
sync_result = client.history.sync_with_server()
if sync_result["synced"]:
    print(f"Synced {sync_result['synced_count']} chats from server")
else:
    print(f"Sync failed: {sync_result['reason']}")

# Create server-side chat through history manager
server_chat_id = client.history.create_server_chat(
    module_id="chat",
    message="New server chat created via history manager"
)
```

### Integrated Conversation with Server-Side Chats

```python
# Create a server chat and use it for conversation
chat_response = client.chats.create(
    module_id="chat",
    message="Welcome to AI Assistant Chat!"
)
chat_id = chat_response["chat_id"]

# Send messages using the server chat ID
response = client.send_message(
    "Hello! This message will be stored server-side.",
    conversation_id=chat_id,
    model="wizard"
)

# Local history is automatically synced with the server chat
local_conv = client.get_conversation(chat_id)
print(f"Local conversation has {local_conv.message_count} messages")

# Export conversation (works with server-synced chats)
exported = client.export_conversation(chat_id, format="json")
```

### Async Server-Side Chat Management

```python
import asyncio
from tela import AsyncTela

async def async_chat_example():
    client = AsyncTela()

    # List chats asynchronously
    chats = await client.chats.list()

    # Create multiple chats concurrently
    tasks = [
        client.chats.create(module_id="chat", message=f"Async Chat {i} - Welcome!")
        for i in range(3)
    ]
    created_responses = await asyncio.gather(*tasks)

    # Extract chat IDs
    chat_ids = [response["chat_id"] for response in created_responses]

    # Get details for all chats concurrently (if endpoint available)
    detail_tasks = [
        client.chats.get(chat_id)
        for chat_id in chat_ids
    ]
    try:
        chat_details = await asyncio.gather(*detail_tasks)
    except Exception as e:
        print(f"Could not retrieve chat details: {e}")

    await client.close()

asyncio.run(async_chat_example())
```

## Audio Features

### Basic Audio Transcription

```python
# Transcribe an audio file
result = client.audio.transcriptions.create(
    file="audio.wav",
    model="fabric-voice-stt",
    response_format="verbose_json"
)

print(f"Transcribed text: {result.text}")
print(f"Language: {result.language}")
print(f"Duration: {result.duration:.2f} seconds")
print(f"Word count: {result.word_count}")

# Access detailed segments with timestamps
for segment in result.segments:
    print(f"[{segment.start:.2f}s - {segment.end:.2f}s]: {segment.text}")
```

### Advanced Transcription Options

```python
# With language hint and context
result = client.audio.transcriptions.create(
    file="meeting.m4a",
    model="fabric-voice-stt",
    language="pt",  # Portuguese
    prompt="Technical discussion about software development",
    temperature=0.0,  # Deterministic output
    response_format="verbose_json"
)

# Export as subtitles
srt_content = result.to_srt()
vtt_content = result.to_vtt()

# Save subtitle files
with open("subtitles.srt", "w") as f:
    f.write(srt_content)
```

### Async Audio Transcription

```python
import asyncio
from tela import AsyncTela

async def transcribe_multiple():
    client = AsyncTela()

    # Transcribe multiple files concurrently
    files = ["audio1.wav", "audio2.wav", "audio3.wav"]
    tasks = [
        client.audio.transcriptions.create(
            file=file,
            model="fabric-voice-stt"
        )
        for file in files
    ]

    results = await asyncio.gather(*tasks)

    for i, result in enumerate(results):
        print(f"File {i+1}: {result.text}")

    await client.close()

asyncio.run(transcribe_multiple())
```

### Text-to-Speech

```python
# List available voices
voices = client.audio.voices()
print(f"Available voices: {len(voices.voices)}")
for voice in voices.voices:
    print(f"- {voice.name} (ID: {voice.id})")

# Generate speech
response = client.audio.speech.create(
    model="fabric-voice-tts",
    input="Hello! This is a demonstration of text-to-speech.",
    voice=voices.voices[0].id,
    output_format="opus_48000_128"
)

# Save audio file
with open("output.opus", "wb") as f:
    f.write(response.content)

print(f"Generated {len(response.content)} bytes of audio")
print(f"Content type: {response.content_type}")
print(f"Format: {response.format}")
```

### Advanced TTS Options

```python
# Different output formats
formats = [
    "opus_48000_128",  # Opus 48kHz, 128kbps (recommended)
    "mp3_44100",       # MP3 44.1kHz
    "pcm_16000",       # PCM WAV 16kHz
    "pcm_44100",       # PCM WAV 44.1kHz
    "ulaw_8000",       # μ-law 8kHz
    "alaw_8000"        # A-law 8kHz
]

# Generate speech with specific format
response = client.audio.speech.create(
    model="fabric-voice-tts",
    input="This is a test with high-quality audio.",
    voice=voices.voices[0].id,
    output_format="pcm_44100"  # High-quality WAV
)
```

### Async Text-to-Speech

```python
import asyncio
from tela import AsyncTela

async def generate_multiple_speeches():
    client = AsyncTela()

    # Get voices
    voices = await client.audio.voices()

    # Generate multiple speeches with different voices
    texts = [
        "Welcome to our service!",
        "Thank you for your patience.",
        "Have a wonderful day!"
    ]

    tasks = [
        client.audio.speech.create(
            model="fabric-voice-tts",
            input=text,
            voice=voices.voices[i % len(voices.voices)].id,
            output_format="opus_48000_128"
        )
        for i, text in enumerate(texts)
    ]

    results = await asyncio.gather(*tasks)

    # Save all generated audio files
    for i, result in enumerate(results):
        with open(f"speech_{i+1}.opus", "wb") as f:
            f.write(result.content)
        print(f"Generated speech_{i+1}.opus ({len(result.content)} bytes)")

    await client.close()

asyncio.run(generate_multiple_speeches())
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
# Model discovery and information
models = client.get_models()
model_info = client.get_model_info("qwen3-max")
capabilities = client.get_model_capabilities("qwen3-max")
available_models = client.list_available_models()

# High-level conversation
response = client.send_message("Hello", conversation_id="chat-1")

# Manual conversation management
conv = client.create_conversation(conversation_id: str = None)
conv = client.get_conversation(conversation_id: str)
ids = client.list_conversations()
messages = client.get_conversation_context(conversation_id: str)

# Export conversations
data = client.export_conversation(conversation_id: str, format: str = "json")

# Server-side chat management
chats = client.chats.list(page: int = 1, page_size: int = 10)
chat = client.chats.get(chat_id: str)
chat_response = client.chats.create(module_id: str = "chat", message: str = "")
# Note: update and delete functionality depends on API availability

# Audio transcription
result = client.audio.transcriptions.create(file: str, model: str = "fabric-voice-stt")
segments = result.segments  # Detailed timestamps
subtitles = result.to_srt()  # Export as SRT
webvtt = result.to_vtt()     # Export as WebVTT

# History management and persistence
client.history.save()  # Save to configured persistence_file
client.history.delete_conversation("chat-1")
client.history.clear_all_conversations()
stats = client.history.get_stats()
sync_result = client.history.sync_with_server()
server_chat_id = client.history.create_server_chat(module_id: str = "chat", message: str = "")
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
- `chat_management_comprehensive.py` - Server-side chat management and synchronization
- `audio_transcription_test.py` - Audio transcription with Fabric Voice STT
- `text_to_speech_test.py` - Text-to-speech generation with Fabric Voice TTS
- `audio_nicegui_interface.py` - Complete audio interface with NiceGUI (transcription + TTS)
- `advanced_nicegui_test.py` - Comprehensive dashboard with chat, audio, and TTS features
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