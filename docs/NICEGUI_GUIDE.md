# Tela API + NiceGUI Complete Integration Guide

This guide shows you how to use the Tela endpoint information functionality with NiceGUI to create powerful interactive applications with full parameter control and output selection.

## Quick Start

### 1. Install Dependencies
```bash
pip install nicegui
pip install python-dotenv
```

### 2. Set Up Credentials
Create a `.env` file:
```bash
TELAOS_API_KEY=your_token_here
TELAOS_ORG_ID=your_org_id_here  
TELAOS_PROJECT_ID=your_project_id_here
```

### 3. Run the Dashboard
```bash
python examples/final_dashboard.py
```
Then open: http://localhost:8080

## Core Features

### Complete Parameter Control
The dashboard provides full control over all API parameters:

- **Temperature** (0.0-2.0): Controls randomness/creativity
- **Max Tokens**: Limits response length
- **Top P** (0.0-1.0): Nucleus sampling threshold
- **Presence Penalty** (-2.0 to 2.0): Reduces repetition
- **Frequency Penalty** (-2.0 to 2.0): Discourages frequent tokens
- **Streaming**: Enable/disable real-time streaming
- **Seed**: For reproducible outputs
- **Stop Sequences**: Custom stopping points

### Output Display Options
Choose exactly what information to display:

- **Show Response**: The AI's actual response
- **Show Usage Stats**: Token counts and efficiency
- **Show Model Info**: Current model capabilities
- **Show Parameters Used**: Exact API parameters
- **Show Timing Info**: Response time metrics
- **Show Raw JSON**: Full API response data
- **Use Conversation History**: Maintain context

### Model Management
- **Dynamic Model Selection**: Choose from 30+ available models
- **Category Filtering**: Filter by Coding, Vision, Large models
- **Capability Display**: See what each model supports
- **Smart Defaults**: Parameters adjust to model capabilities

## Implementation Patterns

### 1. Basic Dashboard Structure
```python
from nicegui import ui
from tela import AsyncTela
import asyncio

class ComprehensiveDashboard:
    def __init__(self):
        load_dotenv()
        self.client = AsyncTela()
        self.models = []
        self.conversation_history = []
        self.session_stats = {
            'total_tokens': 0,
            'total_requests': 0
        }
        
    async def initialize(self):
        """Load available models"""
        models_response = await self.client.get_models()
        self.models = [model.id for model in models_response.data]
        return True
```

### 2. Model Selection with Filtering
```python
# Model selector with categories
model_select = ui.select(
    options=dashboard.models,
    value=dashboard.current_model,
    label='Choose Model'
).classes('w-full')

# Category filter buttons
with ui.row().classes('gap-2'):
    ui.button('All', on_click=lambda: filter_models(None))
    ui.button('Coding', on_click=lambda: filter_models('coding'))
    ui.button('Vision', on_click=lambda: filter_models('vision'))
    ui.button('Large', on_click=lambda: filter_models('large'))

async def filter_models(category):
    """Filter models by category"""
    filtered = await dashboard.get_filtered_models(category)
    model_select.options = filtered
    if filtered:
        model_select.value = filtered[0]
```

### 3. Parameter Controls
```python
# Core parameters
temp_slider = ui.slider(min=0.0, max=2.0, step=0.01, value=0.7).props('label-always')
ui.label('Higher = more creative').classes('text-caption')

max_tokens = ui.number(value=150, min=1, max=4000).classes('w-full')

top_p = ui.slider(min=0.0, max=1.0, step=0.01, value=1.0).props('label-always')

# Advanced parameters in expansion
with ui.expansion('Advanced Parameters').classes('w-full'):
    presence_penalty = ui.slider(min=-2.0, max=2.0, step=0.1, value=0.0)
    frequency_penalty = ui.slider(min=-2.0, max=2.0, step=0.1, value=0.0)
    stream_toggle = ui.switch('Enable Streaming', value=False)
    seed_input = ui.number(placeholder='Random seed')
    stop_input = ui.input(placeholder='Comma-separated')
```

### 4. Handling Streaming vs Non-Streaming
```python
async def send_chat_message(self, message: str, parameters: Dict[str, Any]):
    """Send message with proper streaming handling"""
    
    # Check if streaming is enabled
    is_streaming = parameters.get('stream', False)
    
    # Make API call
    response = await self.client.chat.completions.create(
        messages=messages,
        model=self.current_model,
        **parameters
    )
    
    # Handle response based on type
    if is_streaming:
        # Streaming response is an AsyncStream
        response_content = ""
        async for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    response_content += delta.content
        usage = None  # No usage stats for streaming
    else:
        # Non-streaming response has choices directly
        response_content = response.choices[0].message.content
        usage = self.client.get_usage_from_response(response)
    
    return {
        'response_content': response_content,
        'usage': usage
    }
```

### 5. Tabbed Results Interface
```python
# Create tabs for different views
with ui.tabs() as tabs:
    response_tab = ui.tab('Response')
    analytics_tab = ui.tab('Analytics')
    raw_tab = ui.tab('Raw Data')
    session_tab = ui.tab('Session')

with ui.tab_panels(tabs, value=response_tab):
    # Response panel
    with ui.tab_panel(response_tab):
        response_container = ui.column()
    
    # Analytics panel
    with ui.tab_panel(analytics_tab):
        analytics_container = ui.column()
    
    # Raw data panel
    with ui.tab_panel(raw_tab):
        raw_container = ui.column()
    
    # Session history panel
    with ui.tab_panel(session_tab):
        session_container = ui.column()
```

### 6. Usage Analytics Display
```python
# Token usage cards
with ui.row().classes('gap-4 w-full'):
    with ui.card().classes('text-center'):
        with ui.card_section():
            ui.label('Prompt').classes('text-caption')
            ui.label(str(usage.prompt_tokens)).classes('text-h4')
    
    with ui.card().classes('text-center'):
        with ui.card_section():
            ui.label('Completion').classes('text-caption')
            ui.label(str(usage.completion_tokens)).classes('text-h4')
    
    with ui.card().classes('text-center'):
        with ui.card_section():
            ui.label('Total').classes('text-caption')
            ui.label(str(usage.total_tokens)).classes('text-h4')

# Efficiency meter
efficiency = usage.efficiency_ratio
ui.linear_progress(value=efficiency, color='positive')
ui.label(f'Efficiency Ratio: {efficiency:.1%}')
```

### 7. Event Handler Patterns
```python
# Properly handle NiceGUI events
def on_model_change(e):
    # Extract string value from event
    model_id = e.value if hasattr(e, 'value') else model_select.value
    if model_id:
        asyncio.create_task(update_model_caps(model_id))

model_select.on('update:model-value', on_model_change)

# Handle textarea value properly
async def send_message():
    # Get text value from textarea
    message_value = message_input.value
    if isinstance(message_value, dict):
        message = message_value.get('value', '')
    else:
        message = str(message_value) if message_value else ''
    
    message = message.strip()
    # Process message...
```

## Complete Working Example

```python
"""
Comprehensive Tela API Dashboard with NiceGUI
Full parameter control and output selection
"""

from nicegui import ui
from tela import AsyncTela
from datetime import datetime
from dotenv import load_dotenv
import asyncio

class TelaDashboard:
    def __init__(self):
        load_dotenv()
        self.client = AsyncTela()
        self.models = []
        self.current_model = None
        self.conversation_history = []
        
    async def initialize(self):
        models_response = await self.client.get_models()
        self.models = [model.id for model in models_response.data]
        self.current_model = self.models[0] if self.models else None
        return True
    
    async def send_message(self, message, params):
        # Handle streaming
        is_streaming = params.get('stream', False)
        
        response = await self.client.chat.completions.create(
            messages=[{"role": "user", "content": message}],
            model=self.current_model,
            **params
        )
        
        if is_streaming:
            content = ""
            async for chunk in response:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        content += delta.content
            return content, None
        else:
            content = response.choices[0].message.content
            usage = self.client.get_usage_from_response(response)
            return content, usage

@ui.page('/')
async def dashboard():
    dash = TelaDashboard()
    await dash.initialize()
    
    with ui.header():
        ui.label('Tela API Dashboard').classes('text-h4')
    
    with ui.row().classes('w-full p-4'):
        # Controls
        with ui.column().classes('w-1/3'):
            model_select = ui.select(
                options=dash.models,
                value=dash.current_model,
                label='Model'
            )
            
            temp = ui.slider(min=0, max=2, value=0.7)
            ui.label('Temperature')
            
            streaming = ui.switch('Enable Streaming')
        
        # Chat interface
        with ui.column().classes('flex-grow'):
            chat_area = ui.column()
            
            message_input = ui.input('Enter message')
            send_btn = ui.button('Send')
            
            async def send():
                msg = message_input.value
                params = {
                    'temperature': temp.value,
                    'stream': streaming.value
                }
                
                content, usage = await dash.send_message(msg, params)
                
                with chat_area:
                    ui.label(f"You: {msg}")
                    ui.label(f"AI: {content}")
                    if usage:
                        ui.label(f"Tokens: {usage.total_tokens}")
            
            send_btn.on_click(send)

if __name__ == '__main__':
    ui.run(port=8080)
```

## Troubleshooting

### Streaming Issues
If streaming hangs at "Generating response...":

1. **Check the response type**: Streaming returns an `AsyncStream` object
2. **Iterate properly**: Must use `async for chunk in response`
3. **Extract content correctly**: Access `chunk.choices[0].delta.content`
4. **No usage stats**: Streaming doesn't provide token counts

### Common Errors

**"'AsyncStream' object has no attribute 'choices'"**
- This happens when trying to access `.choices` on a streaming response
- Solution: Check if streaming is enabled before accessing response attributes

**"'dict' object has no attribute 'strip'"**
- NiceGUI events sometimes pass dict objects instead of values
- Solution: Extract the actual value from the event object

**UI elements not updating**
- Use `set_value()` instead of direct assignment for inputs
- Call `clear()` on containers before updating content

## Advanced Features

### Session Statistics
Track usage across the entire session:
```python
self.session_stats = {
    'total_tokens': 0,
    'total_requests': 0,
    'start_time': datetime.now()
}

# Update after each request
self.session_stats['total_requests'] += 1
if usage:
    self.session_stats['total_tokens'] += usage.total_tokens
```

### Model Capabilities Detection
```python
def get_model_capabilities(model_id):
    caps = client.get_model_capabilities(model_id)
    return {
        'supports_streaming': caps.supports_streaming,
        'supports_tools': caps.supports_tools,
        'supports_vision': caps.supports_vision,
        'max_context': caps.max_context_length,
        'default_temp': caps.default_temperature
    }
```

### Conversation History
Maintain context across messages:
```python
# Include previous messages
messages = []
for msg in self.conversation_history[-10:]:
    messages.append(msg)
messages.append({"role": "user", "content": new_message})

# Update history after response
self.conversation_history.append({"role": "user", "content": new_message})
self.conversation_history.append({"role": "assistant", "content": response})
```

## Running Your Dashboard

### Development
```bash
python examples/final_dashboard.py
```

### With Auto-reload
```bash
python examples/final_dashboard.py --reload
```

### Custom Port
```bash
python examples/final_dashboard.py --port 8081
```

### Network Access
```bash
python examples/final_dashboard.py --host 0.0.0.0
```

## Key Features You Get

✅ **30+ Models Available**: Dynamic model selection with categories  
✅ **Full Parameter Control**: All OpenAI-compatible parameters  
✅ **Output Selection**: Choose what data to display  
✅ **Streaming Support**: Real-time responses with proper handling  
✅ **Usage Analytics**: Token counting and efficiency metrics  
✅ **Session Tracking**: Monitor usage over time  
✅ **Conversation History**: Automatic context management  
✅ **Error Handling**: Graceful failure with user feedback  
✅ **Modern UI**: Tabs, cards, expansions, and responsive design  
✅ **Debug Support**: Console logging for troubleshooting  

This comprehensive dashboard gives you everything needed to fully test and interact with the Tela API, with complete control over all parameters and visibility into all response data!