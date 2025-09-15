# Running Tela Client Examples

## Environment Setup

Make sure you have your credentials in the `.env` file:

```bash
TELAOS_API_KEY=your_api_key_here
TELAOS_ORG_ID=your_org_id_here  
TELAOS_PROJECT_ID=your_project_id_here
```

## Examples that Work Out of the Box

These examples will automatically load your `.env` file:

```bash
# Basic API test
python examples/basic_test.py

# NiceGUI Interactive Dashboard (opens web interface at localhost:8080)
python examples/final_dashboard.py

# Endpoint Information
python examples/endpoint_information.py

# All NiceGUI examples
python examples/nicegui_simple_demo.py
python examples/robust_nicegui_dashboard.py
python examples/simple_nicegui_test.py
```

## Examples that Use Manual Credentials

These examples read environment variables directly and have fallback values:

```bash
# Streaming CLI examples
python examples/streaming_cli.py

# Conversation history examples  
python examples/conversation_history.py

# Streaming NiceGUI
python examples/streaming_nicegui.py
```

## Testing the Installation

Quick test to verify everything is working:

```bash
python examples/basic_test.py
```

Expected output:
```
Found 33 models
Using model: qwen3-max
Hello! How can I assist you today?
```

## More Comprehensive Tests

```bash
# Test all endpoint features
python examples/test_endpoint_info.py

# List all available models and their capabilities
python examples/list_models.py
```

## Common Issues

### Issue: "AuthenticationError: The api_key client option must be set"

**Solution 1:** Make sure your `.env` file is in the project root directory with the correct variable names:
- `TELAOS_API_KEY` (not `TELAOS_ACCESS_TOKEN`)
- `TELAOS_ORG_ID` (not `ORG_ID`)  
- `TELAOS_PROJECT_ID` (not `PROJ_ID`)

**Solution 2:** Set environment variables manually:
```bash
export TELAOS_API_KEY="your-key"
export TELAOS_ORG_ID="your-org" 
export TELAOS_PROJECT_ID="your-project"
```

### Issue: Unicode/Emoji encoding errors on Windows

This is a Windows console limitation. The examples will still work, just some output characters may be replaced with `?`.

## Available Models

Run this to see all available models:
```python
from dotenv import load_dotenv
from tela import Tela

load_dotenv()
client = Tela()
models = client.get_models()
for model in models.data:
    print(f"- {model.id}")
```

## Dashboard Features

The NiceGUI dashboard (`examples/final_dashboard.py`) includes:
- Model selection with filtering (Coding, Vision, Large models)
- All API parameters (temperature, max_tokens, etc.)
- Streaming support
- Token usage analytics
- Raw JSON output
- Conversation history
- Session statistics

Open http://localhost:8080 after running the dashboard.