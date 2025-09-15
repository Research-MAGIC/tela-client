"""
Final Robust Tela API Dashboard - Compatible with NiceGUI 2.24.1

A comprehensive dashboard with all parameters, output selection, and modern UI design.
"""

import asyncio
import sys
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from nicegui import ui
    from tela import AsyncTela
except ImportError:
    print("Missing dependencies. Please install: pip install nicegui")
    exit(1)


class ComprehensiveDashboard:
    def __init__(self):
        load_dotenv()
        self.client = AsyncTela()
        self.models: List[str] = []
        self.conversation_history = []
        self.session_stats = {
            'total_tokens': 0,
            'total_requests': 0,
            'start_time': datetime.now()
        }
        
        # Output display toggles
        self.output_settings = {
            'show_response': True,
            'show_usage_stats': True,
            'show_model_info': True,
            'show_parameters': True,
            'show_timing': True,
            'show_raw_json': False,
            'show_conversation': True
        }
        
        self.current_model = None
        self.last_response = None
        self.last_result = None
        
    async def initialize(self):
        """Initialize dashboard"""
        try:
            models_response = await self.client.get_models()
            self.models = [model.id for model in models_response.data]
            self.current_model = self.models[0] if self.models else None
            print(f"Dashboard loaded with {len(self.models)} models")
            return True
        except Exception as e:
            print(f"Failed to initialize: {e}")
            return False
    
    async def get_filtered_models(self, category: Optional[str] = None) -> List[str]:
        """Get models by category"""
        if category:
            return await self.client.list_available_models(category)
        return self.models
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get comprehensive model information"""
        caps = self.client.get_model_capabilities(model_id)
        return {
            'model_id': caps.model_id,
            'supports_streaming': caps.supports_streaming,
            'supports_tools': caps.supports_tools,
            'supports_vision': caps.supports_vision,
            'supports_json_mode': caps.supports_json_mode,
            'supports_audio': caps.supports_audio,
            'default_temperature': caps.default_temperature,
            'max_context_length': caps.max_context_length,
            'temperature_range': caps.temperature_range,
            'top_p_range': caps.top_p_range
        }
    
    async def send_chat_message(self, message: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Send message with comprehensive tracking"""
        start_time = datetime.now()
        
        try:
            # Prepare messages
            messages = []
            if self.output_settings['show_conversation']:
                for msg in self.conversation_history[-8:]:  # Last 4 exchanges
                    messages.append(msg)
            
            messages.append({"role": "user", "content": message})
            
            # Clean parameters
            clean_params = {k: v for k, v in parameters.items() if v is not None and v != ""}
            clean_params['model'] = self.current_model
            clean_params['messages'] = messages
            
            # Check if streaming is enabled BEFORE making the call
            is_streaming = clean_params.get('stream', False)
            print(f"DEBUG: Streaming enabled: {is_streaming}")
            print(f"DEBUG: Model: {self.current_model}")
            
            # Make API call
            response = await self.client.chat.completions.create(**clean_params)
            end_time = datetime.now()
            print(f"DEBUG: Response type: {type(response)}")
            
            # Handle streaming vs non-streaming responses
            if is_streaming:
                print("DEBUG: Handling streaming response...")
                # For streaming, response is an AsyncStream object
                # We need to collect all chunks
                response_content = ""
                chunk_count = 0
                
                try:
                    # Iterate through the stream
                    async for chunk in response:
                        chunk_count += 1
                        # Extract content from chunk
                        if chunk.choices and len(chunk.choices) > 0:
                            delta = chunk.choices[0].delta
                            if delta.content:
                                response_content += delta.content
                    
                    print(f"DEBUG: Collected {chunk_count} chunks, total content: {len(response_content)} chars")
                    
                except Exception as e:
                    print(f"ERROR in streaming: {e}")
                    response_content = f"Streaming error: {str(e)}"
                
                # No usage stats for streaming
                usage = None
                # Set response to None for streaming
                response = None
                
                if not response_content:
                    response_content = "No content received from stream"
            else:
                # Non-streaming response - response has choices attribute directly
                response_content = response.choices[0].message.content
                # Get usage for non-streaming
                usage = self.client.get_usage_from_response(response)
            
            # Update conversation
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": response_content})
            
            # Update session stats
            self.session_stats['total_requests'] += 1
            if usage:
                self.session_stats['total_tokens'] += usage.total_tokens
            
            # Prepare comprehensive result
            result = {
                'response_content': response_content,
                'usage': usage,
                'full_response': response if not is_streaming else None,
                'parameters_used': clean_params,
                'model_info': self.get_model_info(self.current_model),
                'timing': {
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_ms': (end_time - start_time).total_seconds() * 1000
                },
                'raw_json': response.model_dump() if hasattr(response, 'model_dump') and not is_streaming else {'message': 'Streaming response - raw chunks not displayed', 'content': response_content, 'streaming': True}
            }
            
            self.last_response = response
            self.last_result = result
            
            return result
            
        except Exception as e:
            return {'error': str(e), 'error_type': type(e).__name__}


# Global dashboard
dashboard = None

async def setup_dashboard():
    """Setup dashboard instance"""
    global dashboard
    if dashboard is None:
        dashboard = ComprehensiveDashboard()
        return await dashboard.initialize()
    return True


@ui.page('/')
async def main_app():
    """Main dashboard application"""
    if not await setup_dashboard():
        with ui.column().classes('items-center justify-center h-screen'):
            ui.icon('error').style('font-size: 4rem; color: red;')
            ui.label('Failed to initialize dashboard').classes('text-h5')
            ui.label('Please check your .env file with Tela API credentials').classes('text-body1')
        return
    
    # Header
    with ui.header(elevated=True).classes('items-center justify-between'):
        with ui.row().classes('items-center'):
            ui.icon('dashboard').style('font-size: 2rem; margin-right: 1rem;')
            ui.label('Tela API Comprehensive Dashboard').classes('text-h4 font-weight-bold')
        
        with ui.row().classes('items-center gap-4'):
            ui.badge(f'{len(dashboard.models)} Models Available', color='positive')
            ui.badge(f'Session: {dashboard.session_stats["total_requests"]} requests', color='info')
    
    # Main layout
    with ui.row().classes('w-full gap-4 p-4'):
        
        # Left Panel - Controls
        with ui.column().classes('w-1/3 gap-4'):
            
            # Model Selection
            with ui.card().tight():
                with ui.card_section():
                    ui.label('Model Selection').classes('text-h6 font-weight-bold')
                
                with ui.card_section():
                    model_select = ui.select(
                        options=dashboard.models,
                        value=dashboard.current_model,
                        label='Choose Model'
                    ).classes('w-full')
                    
                    # Filter buttons
                    with ui.row().classes('gap-2 mt-3'):
                        btn_all = ui.button('All', color='grey')
                        btn_coding = ui.button('Coding', color='blue')
                        btn_vision = ui.button('Vision', color='purple')  
                        btn_large = ui.button('Large', color='orange')
                    
                    # Model capabilities display
                    model_caps = ui.column().classes('mt-4')
            
            # Parameters Section
            with ui.card().tight():
                with ui.card_section():
                    ui.label('API Parameters').classes('text-h6 font-weight-bold')
                
                with ui.card_section():
                    # Core parameters
                    ui.label('Temperature').classes('font-weight-medium mb-1')
                    temp_slider = ui.slider(min=0.0, max=2.0, step=0.01, value=0.7).props('label-always')
                    ui.label('Higher = more creative').classes('text-caption text-grey-7 mb-3')
                    
                    ui.label('Max Tokens').classes('font-weight-medium mb-1')
                    max_tokens = ui.number(value=150, min=1, max=4000).classes('w-full mb-3')
                    
                    ui.label('Top P').classes('font-weight-medium mb-1') 
                    top_p = ui.slider(min=0.0, max=1.0, step=0.01, value=1.0).props('label-always')
                    ui.label('Nucleus sampling').classes('text-caption text-grey-7 mb-3')
                    
                    # Advanced parameters in expansion
                    with ui.expansion('Advanced Parameters').classes('w-full'):
                        ui.label('Presence Penalty').classes('font-weight-medium mb-1')
                        presence_penalty = ui.slider(min=-2.0, max=2.0, step=0.1, value=0.0).props('label-always')
                        
                        ui.label('Frequency Penalty').classes('font-weight-medium mb-1')
                        frequency_penalty = ui.slider(min=-2.0, max=2.0, step=0.1, value=0.0).props('label-always')
                        
                        stream_toggle = ui.switch('Enable Streaming', value=False)
                        
                        ui.label('Seed (Optional)').classes('font-weight-medium mb-1')
                        seed_input = ui.number(placeholder='Random seed').classes('w-full')
                        
                        ui.label('Stop Sequences').classes('font-weight-medium mb-1')
                        stop_input = ui.input(placeholder='Comma-separated').classes('w-full')
            
            # Output Options
            with ui.card().tight():
                with ui.card_section():
                    ui.label('Output Display Options').classes('text-h6 font-weight-bold')
                
                with ui.card_section():
                    response_toggle = ui.switch('Show Response', value=True)
                    usage_toggle = ui.switch('Show Usage Stats', value=True)
                    model_info_toggle = ui.switch('Show Model Info', value=True)
                    params_toggle = ui.switch('Show Parameters Used', value=True)
                    timing_toggle = ui.switch('Show Timing Info', value=True)
                    json_toggle = ui.switch('Show Raw JSON', value=False)
                    conversation_toggle = ui.switch('Use Conversation History', value=True)
        
        # Right Panel - Chat & Results
        with ui.column().classes('flex-grow gap-4'):
            
            # Input Section
            with ui.card().tight():
                with ui.card_section():
                    ui.label('Chat Interface').classes('text-h6 font-weight-bold')
                
                with ui.card_section():
                    message_input = ui.textarea(
                        label='Enter your message',
                        placeholder='Type your message here...'
                    ).classes('w-full')
                    
                    with ui.row().classes('w-full justify-between items-center mt-3'):
                        # Quick examples
                        example_dropdown = ui.select([
                            'Explain quantum computing simply',
                            'Write Python fibonacci function',
                            'Compare REST vs GraphQL', 
                            'Creative 50-word story',
                            'Debug this code',
                            'Latest AI trends'
                        ], label='Quick Examples').classes('flex-grow mr-4')
                        
                        send_button = ui.button('Send Message', color='primary', icon='send')
            
            # Results Tabbed Interface
            with ui.card().classes('w-full min-h-96').tight():
                with ui.tabs() as tabs:
                    response_tab = ui.tab('Response')
                    analytics_tab = ui.tab('Analytics')
                    raw_tab = ui.tab('Raw Data')
                    session_tab = ui.tab('Session')
                
                with ui.tab_panels(tabs, value=response_tab).classes('w-full p-4'):
                    
                    # Response Panel
                    with ui.tab_panel(response_tab):
                        response_container = ui.column()
                    
                    # Analytics Panel
                    with ui.tab_panel(analytics_tab):
                        analytics_container = ui.column()
                    
                    # Raw Data Panel
                    with ui.tab_panel(raw_tab):
                        raw_container = ui.column()
                    
                    # Session Panel
                    with ui.tab_panel(session_tab):
                        session_container = ui.column()
    
    # Event handlers
    async def update_model_caps(model_id: str):
        """Update model capabilities display"""
        if not model_id:
            return
            
        dashboard.current_model = model_id
        caps = dashboard.get_model_info(model_id)
        
        model_caps.clear()
        with model_caps:
            ui.label('Capabilities').classes('font-weight-medium mb-2')
            
            # Capability chips
            features = []
            if caps['supports_streaming']: features.append('Streaming')
            if caps['supports_tools']: features.append('Tools') 
            if caps['supports_vision']: features.append('Vision')
            if caps['supports_json_mode']: features.append('JSON')
            if caps['supports_audio']: features.append('Audio')
            
            if features:
                with ui.row().classes('gap-1 flex-wrap'):
                    for feature in features:
                        ui.chip(feature, color='positive')
            
            if caps['max_context_length']:
                ui.label(f"Context: {caps['max_context_length']:,} tokens").classes('text-caption mt-2')
            
            ui.label(f"Default Temperature: {caps['default_temperature']}").classes('text-caption')
    
    async def filter_models(category: Optional[str]):
        """Filter models by category"""
        try:
            filtered = await dashboard.get_filtered_models(category)
            model_select.options = filtered
            if filtered:
                model_select.value = filtered[0]
                await update_model_caps(filtered[0])
        except Exception as e:
            ui.notify(f'Filter error: {e}', type='negative')
    
    def set_example(example: str):
        """Set example message"""
        if example:
            message_input.set_value(example)
    
    async def send_message():
        """Handle message sending"""
        # Get the text value from the textarea
        message_value = message_input.value
        if isinstance(message_value, dict):
            message = message_value.get('value', '') if 'value' in message_value else str(message_value)
        else:
            message = str(message_value) if message_value else ''
        
        message = message.strip()
        if not message:
            ui.notify('Please enter a message', type='warning')
            return
        
        if not dashboard.current_model:
            ui.notify('Please select a model', type='warning')
            return
        
        # Update output settings
        dashboard.output_settings.update({
            'show_response': response_toggle.value,
            'show_usage_stats': usage_toggle.value,
            'show_model_info': model_info_toggle.value,
            'show_parameters': params_toggle.value,
            'show_timing': timing_toggle.value,
            'show_raw_json': json_toggle.value,
            'show_conversation': conversation_toggle.value
        })
        
        # Collect parameters
        params = {
            'temperature': temp_slider.value,
            'max_tokens': int(max_tokens.value) if max_tokens.value else None,
            'top_p': top_p.value,
            'presence_penalty': presence_penalty.value,
            'frequency_penalty': frequency_penalty.value,
            'stream': stream_toggle.value,
        }
        
        if seed_input.value:
            params['seed'] = int(seed_input.value)
        
        if stop_input.value:
            params['stop'] = [s.strip() for s in stop_input.value.split(',') if s.strip()]
        
        # Show loading
        send_button.props('loading')
        
        # Clear containers
        response_container.clear()
        analytics_container.clear() 
        raw_container.clear()
        
        with response_container:
            ui.spinner()
            ui.label('Generating response...').classes('ml-4')
        
        try:
            # Send message
            result = await dashboard.send_chat_message(message, params)
            
            if 'error' in result:
                # Handle error
                response_container.clear()
                with response_container:
                    ui.icon('error', color='negative').style('font-size: 2rem;')
                    ui.label(f'Error: {result["error"]}').classes('text-h6 text-negative ml-2')
                return
            
            # Update Response Panel
            response_container.clear()
            with response_container:
                if dashboard.output_settings['show_response']:
                    ui.label('Assistant Response').classes('text-h6 font-weight-bold mb-3')
                    with ui.card().classes('bg-grey-1'):
                        with ui.card_section():
                            ui.label(result['response_content']).classes('whitespace-pre-wrap')
                
                if dashboard.output_settings['show_model_info']:
                    ui.separator().classes('my-4')
                    ui.label('Model Information').classes('text-h6 font-weight-bold mb-2')
                    model_info = result['model_info']
                    
                    with ui.row().classes('gap-2 flex-wrap'):
                        ui.chip(f"Model: {model_info['model_id']}", color='primary')
                        ui.chip(f"Temp: {model_info['default_temperature']}", color='secondary')
                        if model_info['max_context_length']:
                            ui.chip(f"Context: {model_info['max_context_length']:,}", color='orange')
                
                if dashboard.output_settings['show_timing']:
                    ui.separator().classes('my-4')
                    ui.label('Performance').classes('text-h6 font-weight-bold mb-2')
                    timing = result['timing']
                    ui.label(f"Response time: {timing['duration_ms']:.0f}ms").classes('text-body1')
            
            # Update Analytics Panel
            analytics_container.clear()
            with analytics_container:
                # Check if streaming was used
                if params.get('stream', False):
                    ui.label('Streaming Mode').classes('text-h6 font-weight-bold mb-4')
                    ui.label('Token usage statistics are not available in streaming mode.').classes('text-body1 text-orange mb-4')
                    ui.icon('info', color='orange').classes('mr-2')
                
                if dashboard.output_settings['show_usage_stats'] and result.get('usage'):
                    usage = result['usage']
                    
                    ui.label('Token Usage Analysis').classes('text-h6 font-weight-bold mb-4')
                    
                    # Usage metrics in cards
                    with ui.row().classes('gap-4 w-full'):
                        with ui.card().classes('text-center'):
                            with ui.card_section():
                                ui.label('Prompt').classes('text-caption')
                                ui.label(str(usage.prompt_tokens)).classes('text-h4 text-primary')
                        
                        with ui.card().classes('text-center'):
                            with ui.card_section():
                                ui.label('Completion').classes('text-caption')
                                ui.label(str(usage.completion_tokens)).classes('text-h4 text-secondary')
                        
                        with ui.card().classes('text-center'):
                            with ui.card_section():
                                ui.label('Total').classes('text-caption')
                                ui.label(str(usage.total_tokens)).classes('text-h4 text-positive')
                    
                    # Efficiency metrics
                    ui.separator().classes('my-4')
                    ui.label('Efficiency Metrics').classes('text-h6 font-weight-bold mb-2')
                    
                    efficiency = usage.efficiency_ratio
                    ui.linear_progress(value=efficiency, color='positive').classes('mb-2')
                    ui.label(f'Efficiency Ratio: {efficiency:.1%}').classes('text-body1')
                
                # Session statistics
                ui.separator().classes('my-4')
                ui.label('Session Statistics').classes('text-h6 font-weight-bold mb-2')
                stats = dashboard.session_stats
                
                ui.label(f"Total Requests: {stats['total_requests']}").classes('text-body1')
                ui.label(f"Total Tokens: {stats['total_tokens']:,}").classes('text-body1')
                
                duration = datetime.now() - stats['start_time']
                minutes = int(duration.total_seconds() // 60)
                ui.label(f"Session Duration: {minutes}m").classes('text-body1')
            
            # Update Raw Data Panel
            if dashboard.output_settings['show_raw_json']:
                raw_container.clear()
                with raw_container:
                    if dashboard.output_settings['show_parameters']:
                        ui.label('Parameters Used').classes('text-h6 font-weight-bold mb-3')
                        ui.json_editor({
                            'content': {'json': result.get('parameters_used', {})}
                        }).props('readonly').classes('mb-4')
                    
                    ui.label('Full API Response').classes('text-h6 font-weight-bold mb-3')
                    ui.json_editor({
                        'content': {'json': result.get('raw_json', {})}
                    }).props('readonly')
            
            # Update Session Panel
            session_container.clear()
            with session_container:
                ui.label('Conversation History').classes('text-h6 font-weight-bold mb-3')
                
                # Show recent conversation
                for msg in dashboard.conversation_history[-6:]:
                    role_color = 'primary' if msg['role'] == 'user' else 'secondary'
                    role_icon = 'person' if msg['role'] == 'user' else 'smart_toy'
                    
                    with ui.card().classes('mb-2'):
                        with ui.card_section():
                            with ui.row().classes('items-center mb-2'):
                                ui.icon(role_icon, color=role_color)
                                ui.label(msg['role'].title()).classes('font-weight-bold ml-2')
                            ui.label(msg['content']).classes('whitespace-pre-wrap')
            
            ui.notify('Response generated successfully!', type='positive')
            message_input.set_value('')
            
        except Exception as e:
            response_container.clear()
            with response_container:
                ui.icon('error', color='negative').style('font-size: 2rem;')
                ui.label(f'Unexpected error: {str(e)}').classes('text-h6 text-negative ml-2')
        
        finally:
            send_button.props('loading=false')
    
    # Connect event handlers
    def on_model_change(e):
        # Extract the actual string value from the event
        model_id = e.value if hasattr(e, 'value') else model_select.value
        if model_id:
            asyncio.create_task(update_model_caps(model_id))
    
    def on_example_change(e):
        # Extract the actual example text
        example = e.value if hasattr(e, 'value') else example_dropdown.value
        if example:
            set_example(example)
    
    model_select.on('update:model-value', on_model_change)
    example_dropdown.on('update:model-value', on_example_change)
    send_button.on_click(send_message)
    
    # Filter button handlers
    btn_all.on_click(lambda: filter_models(None))
    btn_coding.on_click(lambda: filter_models('coding'))
    btn_vision.on_click(lambda: filter_models('vision'))
    btn_large.on_click(lambda: filter_models('large'))
    
    # Initialize
    if dashboard.current_model:
        await update_model_caps(dashboard.current_model)


if __name__ in {"__main__", "__mp_main__"}:
    print("Starting Comprehensive Tela API Dashboard...")
    print("Features: All parameters, output selection, modern UI")
    print("Opening at http://localhost:8080")
    print("Press Ctrl+C to stop")
    
    ui.run(
        port=8080,
        title='Tela API Comprehensive Dashboard',
        show=True
    )