# Tool Calling Examples

Interactive examples demonstrating function calling capabilities with the Tela SDK.

## Files

### `tool_calling_cli.py`
Interactive CLI application for testing tool calling functionality.

**Features:**
- 4 built-in tools: weather, document search, calculator, and time
- Interactive mode with conversation history
- Demo mode with automated examples
- Comprehensive error handling and retry logic
- Windows-compatible output (no Unicode emojis)

**Usage:**
```bash
python examples/tool_calling_cli.py
```

Choose between:
1. Interactive Mode - Chat interface with tool calling
2. Demo Mode - Automated examples
3. Quit

### `tool_calling_nicegui.py`
Web-based interface for tool calling with real-time visualization.

**Features:**
- Interactive chat interface with tool execution visualization
- Real-time tool execution log
- Example query buttons for quick testing
- Simple demo mode for rapid testing
- Visual display of tool results and execution status

**Usage:**
```bash
python examples/tool_calling_nicegui.py
```

Runs on http://localhost:8081

### `test_tool_calling.py`
Automated test script to verify tool calling functionality.

**Features:**
- Tests tool calling with model requests
- Direct tool execution testing
- Comprehensive error checking
- No interactive input required

**Usage:**
```bash
python examples/test_tool_calling.py
```

## Available Tools

### 1. Weather Tool (`get_weather`)
Simulates weather API calls.

**Parameters:**
- `city` (required): City name
- `units` (optional): "metric" or "imperial" (default: "metric")

**Example:** "What's the weather like in Paris?"

### 2. Document Search (`search_docs`)
Simulates searching through documentation.

**Parameters:**
- `query` (required): Search query string
- `top_k` (optional): Number of results (1-20, default: 5)

**Example:** "Search for API documentation"

### 3. Calculator (`calculate`)
Performs mathematical calculations.

**Parameters:**
- `expression` (required): Mathematical expression
- `precision` (optional): Decimal places (0-10, default: 2)

**Example:** "Calculate 15 * 7 + 23"

### 4. Time Tool (`get_time`)
Gets current time information.

**Parameters:**
- `timezone` (optional): Timezone (UTC, EST, PST, etc., default: "UTC")
- `format` (optional): "12h", "24h", or "iso" (default: "24h")

**Example:** "What time is it in Tokyo?"

## Tool Calling Flow

The examples demonstrate the standard OpenAI-compatible tool calling pattern:

1. **Send request** with user query and available tools
2. **Model decides** whether to use tools based on the query
3. **Execute tools** if requested by the model
4. **Send results** back to model as tool messages
5. **Get final response** incorporating tool results

## Implementation Details

### Tool Registry
The `ToolRegistry` class manages available tools:
- Registers tools with their functions and JSON schemas
- Provides OpenAI-compatible tool definitions
- Executes tools with proper error handling

### Response Format Handling
The examples handle both object and dictionary formats for tool calls:
- Supports `tool_call.function.name` (object format)
- Supports `tool_call['function']['name']` (dictionary format)
- Maintains compatibility across different SDK versions

### Error Handling
Comprehensive error handling includes:
- JSON parsing errors for tool arguments
- Tool execution failures
- API communication errors
- Network timeouts and server errors

## Environment Setup

Required environment variables:
```
TELAOS_API_KEY=your_api_key
TELAOS_ORG_ID=your_org_id
TELAOS_PROJECT_ID=your_project_id
```

## Testing

Run the test script to verify everything works:
```bash
python examples/test_tool_calling.py
```

This will test:
- Tool calling with model requests
- Direct tool execution
- Error handling
- All 4 available tools

## Model Compatibility

Tool calling requires models that support function calling. The examples use `qwen3-max` by default, which supports:
- Function calling with typed parameters
- Multiple tool calls in single request
- Proper tool result integration

## Example Queries

Try these queries to see tool calling in action:

**Single Tool:**
- "What's the weather like in London?"
- "Calculate 42 * 17 + 89"
- "What time is it right now?"
- "Search for authentication documentation"

**Multiple Tools:**
- "Check the weather in Paris and calculate 15 + 25"
- "Find docs about streaming and tell me the time in Tokyo"
- "What's the weather in Berlin and search for API examples"

The model will automatically determine which tools to use based on your query!