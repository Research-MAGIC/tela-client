"""
Final Robust Tela API Dashboard - Compatible with NiceGUI 2.24.1

A comprehensive dashboard with all parameters, output selection, audio capabilities, and modern UI design.
"""

import asyncio
import sys
import os
import json
import io
import base64
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
            'transcriptions': 0,
            'tts_generations': 0,
            'start_time': datetime.now()
        }

        # Audio capabilities
        self.voices = []
        self.current_voice = None
        self.audio_history = []
        
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
            # Load models
            models_response = await self.client.get_models()
            self.models = [model.id for model in models_response.data]
            self.current_model = self.models[0] if self.models else None

            # Load voices for TTS
            try:
                voices_response = await self.client.audio.voices()
                self.voices = voices_response.voices
                self.current_voice = self.voices[0].id if self.voices else None
                print(f"Dashboard loaded with {len(self.models)} models and {len(self.voices)} voices")
            except Exception as e:
                print(f"Audio initialization failed: {e}")
                self.voices = []

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
            'top_p_range': caps.top_p_range,
            'context_window': f"{caps.max_context_length:,}" if caps.max_context_length else "Unknown",
            'model_family': self._get_model_family(model_id),
            'recommended_use': self._get_recommended_use(model_id)
        }

    def _get_model_family(self, model_id: str) -> str:
        """Determine model family based on model ID"""
        if 'claude' in model_id.lower():
            return 'Claude (Anthropic)'
        elif 'gpt' in model_id.lower():
            return 'GPT (OpenAI)'
        elif 'llama' in model_id.lower():
            return 'Llama (Meta)'
        elif 'gemini' in model_id.lower():
            return 'Gemini (Google)'
        else:
            return 'Other'

    def _get_recommended_use(self, model_id: str) -> str:
        """Get recommended use cases based on model characteristics"""
        caps = self.client.get_model_capabilities(model_id)
        uses = []

        if caps.supports_vision:
            uses.append('Image Analysis')
        if caps.supports_tools:
            uses.append('Function Calling')
        if caps.supports_json_mode:
            uses.append('Structured Output')
        if caps.max_context_length and caps.max_context_length > 100000:
            uses.append('Long Documents')
        if 'code' in model_id.lower() or 'coding' in model_id.lower():
            uses.append('Code Generation')

        return ', '.join(uses) if uses else 'General Purpose'
    
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

    async def transcribe_audio(self, audio_file: bytes, filename: str = "audio.wav",
                              language: Optional[str] = None, prompt: Optional[str] = None,
                              temperature: float = 0.0) -> Dict[str, Any]:
        """Transcribe audio data"""
        try:
            # Create a file-like object from bytes
            audio_io = io.BytesIO(audio_file)
            audio_io.name = filename

            result = await self.client.audio.transcriptions.create(
                file=audio_io,
                model="fabric-voice-stt",
                response_format="verbose_json",
                language=language,
                prompt=prompt,
                temperature=temperature
            )

            self.session_stats['transcriptions'] += 1
            self.audio_history.append({
                'type': 'transcription',
                'timestamp': datetime.now(),
                'input': f"Audio file ({len(audio_file)} bytes)",
                'output': result.text,
                'details': {
                    'language': result.language,
                    'duration': result.duration,
                    'segments': len(result.segments) if result.segments else 0
                }
            })

            return {
                'success': True,
                'text': result.text,
                'language': result.language,
                'duration': result.duration,
                'segments': result.segments,
                'word_count': result.word_count,
                'segment_count': result.segment_count
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def generate_speech(self, text: str, voice_id: str,
                            output_format: str = "opus_48000_128") -> Dict[str, Any]:
        """Generate speech from text"""
        try:
            result = await self.client.audio.speech.create(
                model="fabric-voice-tts",
                input=text,
                voice=voice_id,
                output_format=output_format
            )

            self.session_stats['tts_generations'] += 1
            self.audio_history.append({
                'type': 'tts',
                'timestamp': datetime.now(),
                'input': text[:100] + "..." if len(text) > 100 else text,
                'output': f"Audio ({len(result.content)} bytes)",
                'details': {
                    'voice_id': voice_id,
                    'output_format': output_format,
                    'content_type': result.content_type
                }
            })

            return {
                'success': True,
                'audio_data': result.content,
                'content_type': result.content_type,
                'format': result.format,
                'size': len(result.content)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Global dashboard and audio mappings
dashboard = None
tts_voice_id_map = {}
tts_format_map = {}

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
            ui.label('Chat • Audio • Text-to-Speech').classes('text-caption text-grey-6 ml-2')
        
        with ui.row().classes('items-center gap-4'):
            ui.badge(f'{len(dashboard.models)} Models Available', color='positive')
            ui.badge(f'{len(dashboard.voices)} Voices', color='secondary')
            ui.badge(f'Chat: {dashboard.session_stats["total_requests"]} requests', color='info')
            ui.badge(f'Audio: {dashboard.session_stats["transcriptions"]}T/{dashboard.session_stats["tts_generations"]}S', color='orange')
    
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
                    audio_tab = ui.tab('Audio', icon='audiotrack')
                    tts_tab = ui.tab('Text-to-Speech', icon='volume_up')
                
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

                    # Audio Panel
                    with ui.tab_panel(audio_tab):
                        audio_container = ui.column()

                    # Text-to-Speech Panel
                    with ui.tab_panel(tts_tab):
                        tts_container = ui.column()

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
            
            # Model details
            ui.separator().classes('my-2')
            ui.label(f"Family: {caps['model_family']}").classes('text-caption text-grey-7')
            ui.label(f"Context: {caps['context_window']} tokens").classes('text-caption text-grey-7')
            ui.label(f"Temperature: {caps['default_temperature']}").classes('text-caption text-grey-7')
            ui.label(f"Use cases: {caps['recommended_use']}").classes('text-caption text-grey-7')
    
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

                    with ui.row().classes('gap-2 flex-wrap mb-2'):
                        ui.chip(f"Model: {model_info['model_id']}", color='primary')
                        ui.chip(f"Family: {model_info['model_family']}", color='info')
                        ui.chip(f"Context: {model_info['context_window']}", color='orange')
                        ui.chip(f"Temp: {model_info['default_temperature']}", color='secondary')

                    ui.label(f"Recommended for: {model_info['recommended_use']}").classes('text-body2 text-grey-7 mb-2')
                
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

    # Audio interface initialization
    async def setup_audio_interface():
        """Setup audio interface panels"""
        # Audio transcription panel
        audio_container.clear()
        with audio_container:
            ui.label('Audio Transcription').classes('text-h6 font-weight-bold mb-4')

            # File upload for transcription
            upload_area = ui.upload(
                on_upload=lambda e: handle_audio_upload(e),
                max_file_size=10_000_000,  # 10MB
                multiple=False
            ).props('accept="audio/*"').classes('w-full mb-4')
            upload_area.props('label="Drop audio file here or click to select"')

            # Transcription options
            with ui.expansion('Transcription Options').classes('w-full mb-4'):
                global audio_language_select, audio_prompt_input, audio_temp_slider
                audio_language_select = ui.select(
                    options=['auto', 'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh'],
                    value='auto',
                    label='Language Hint'
                ).classes('w-full mb-2')

                audio_prompt_input = ui.input(
                    label='Context Prompt (Optional)',
                    placeholder='Provide context to improve accuracy'
                ).classes('w-full mb-2')

                audio_temp_slider = ui.slider(
                    min=0.0, max=1.0, value=0.0, step=0.1
                ).props('label-always').classes('w-full')
                ui.label('Temperature (0 = focused, 1 = creative)').classes('text-caption text-grey-6')

            # Results area
            global audio_results_area
            audio_results_area = ui.column().classes('w-full')
            with audio_results_area:
                ui.label('Upload an audio file to see transcription results').classes('text-center text-grey-6 p-8')

        # Text-to-Speech panel
        tts_container.clear()
        with tts_container:
            ui.label('Text-to-Speech Generation').classes('text-h6 font-weight-bold mb-4')

            # Text input
            global tts_text_input
            tts_text_input = ui.textarea(
                label='Enter text to convert to speech',
                placeholder='Type or paste your text here...',
                value='Hello! This is a demonstration of the Fabric Voice text-to-speech API.'
            ).classes('w-full mb-4').props('rows=4')

            # Voice and format selection
            with ui.row().classes('w-full gap-4 mb-4'):
                global tts_voice_select, tts_format_select, tts_voice_id_map, tts_format_map

                # Voice selection
                tts_voice_select = ui.select(
                    options=[],
                    label='Choose Voice'
                ).classes('flex-grow')

                # Populate voice options - USING SIMPLE STRING FORMAT LIKE WORKING VERSION
                voice_options = []

                if dashboard.voices:
                    for i, voice in enumerate(dashboard.voices):
                        # Use the exact format that worked: "Voice X - shortID"
                        option_str = f"Voice {i+1} - {voice.id[:8]}"
                        voice_options.append(option_str)
                        tts_voice_id_map[option_str] = voice.id
                        print(f"[VOICE] Created: '{option_str}' -> '{voice.id}'")

                if not voice_options:
                    voice_options = ['No voices available']
                    default_voice = 'No voices available'
                else:
                    default_voice = voice_options[0]

                tts_voice_select.options = voice_options
                tts_voice_select.value = default_voice

                print(f"[VOICE] Final TTS options: {voice_options}")

                # Output format - USING SIMPLE STRING FORMAT LIKE WORKING VERSION
                format_options = ['Opus 48kHz', 'MP3 44.1kHz', 'WAV 16kHz']
                tts_format_map.update({
                    'Opus 48kHz': 'opus_48000_128',
                    'MP3 44.1kHz': 'mp3_44100',
                    'WAV 16kHz': 'pcm_16000'
                })

                tts_format_select = ui.select(
                    options=format_options,
                    value='Opus 48kHz',
                    label='Audio Format'
                ).classes('flex-grow')

            # Generate button
            generate_button = ui.button(
                'Generate Speech',
                color='primary',
                icon='volume_up'
            ).classes('w-full mb-4')

            # TTS Results area
            global tts_results_area
            tts_results_area = ui.column().classes('w-full')
            with tts_results_area:
                ui.label('Enter text and click Generate to create audio').classes('text-center text-grey-6 p-8')

            # Connect TTS button - FIXED: Don't use asyncio.create_task
            generate_button.on_click(generate_speech)

    # Audio event handlers
    async def handle_audio_upload(e):
        """Handle audio file upload and transcription"""
        try:
            print(f"[UPLOAD DEBUG] Event received: {type(e)}")
            print(f"[UPLOAD DEBUG] File name: {e.name}")
            print(f"[UPLOAD DEBUG] Content type: {type(e.content)}")

            # Use the proven working method from audio_nicegui_interface.py
            e.content.seek(0)
            audio_bytes = e.content.read()
            print(f"[UPLOAD] Successfully read {len(audio_bytes)} bytes from {e.name}")

            if not audio_bytes:
                print("[UPLOAD DEBUG] No bytes obtained")
                ui.notify('No file content received', type='warning')
                return

            # Clear results and show loading
            audio_results_area.clear()
            with audio_results_area:
                ui.spinner().classes('mr-4')
                ui.label('Processing audio file...').classes('text-h6')

            # Prepare parameters
            language = audio_language_select.value if audio_language_select.value != 'auto' else None
            prompt = audio_prompt_input.value.strip() if audio_prompt_input.value else None
            temperature = audio_temp_slider.value

            # Transcribe audio using bytes instead of file object
            result = await dashboard.transcribe_audio(
                audio_file=audio_bytes,
                filename=e.name,
                language=language,
                prompt=prompt,
                temperature=temperature
            )

            # Display results
            audio_results_area.clear()
            with audio_results_area:
                if result['success']:
                    ui.label('Transcription Results').classes('text-h6 font-weight-bold mb-3')

                    # Main transcription
                    with ui.card().classes('bg-grey-1 mb-4'):
                        with ui.card_section():
                            ui.label('Transcribed Text').classes('text-subtitle1 font-weight-medium mb-2')
                            ui.label(result['text']).classes('whitespace-pre-wrap text-body1')

                    # Metadata
                    if result['language']:
                        ui.label(f"Detected Language: {result['language']}").classes('text-body2 mb-1')
                    if result['duration']:
                        ui.label(f"Duration: {result['duration']:.2f} seconds").classes('text-body2 mb-1')
                    ui.label(f"Word Count: {result['word_count']}").classes('text-body2 mb-1')
                    ui.label(f"Segments: {result['segment_count']}").classes('text-body2')
                else:
                    ui.icon('error', color='negative').classes('mr-2')
                    ui.label(f'Transcription failed: {result["error"]}').classes('text-negative')

            ui.notify('Transcription completed!' if result['success'] else 'Transcription failed',
                     type='positive' if result['success'] else 'negative')

        except Exception as e:
            audio_results_area.clear()
            with audio_results_area:
                ui.icon('error', color='negative').classes('mr-2')
                ui.label(f'Upload error: {str(e)}').classes('text-negative')
            ui.notify('Upload failed', type='negative')

    async def generate_speech():
        """Generate speech from text"""
        try:
            global tts_voice_id_map, tts_format_map

            print(f"[TTS DEBUG] Starting TTS generation...")
            print(f"[TTS DEBUG] tts_voice_id_map: {tts_voice_id_map}")
            print(f"[TTS DEBUG] tts_format_map: {tts_format_map}")

            text = tts_text_input.value.strip()
            print(f"[TTS DEBUG] Text: '{text[:50]}...' ({len(text)} chars)")
            if not text:
                print("[TTS DEBUG] No text provided")
                ui.notify('Please enter text to convert', type='warning')
                return

            selected_voice = tts_voice_select.value
            print(f"[TTS DEBUG] Selected voice: '{selected_voice}'")
            if not selected_voice:
                print("[TTS DEBUG] No voice selected")
                ui.notify('Please select a voice', type='warning')
                return

            if selected_voice == 'No voices available':
                print("[TTS DEBUG] No voices available")
                ui.notify('No voices available', type='warning')
                return

            # Convert selected voice string to actual voice ID
            voice_id = tts_voice_id_map.get(selected_voice)
            print(f"[TTS DEBUG] Mapped voice_id: '{voice_id}'")
            if not voice_id:
                print(f"[TTS DEBUG] Voice mapping failed for '{selected_voice}'")
                ui.notify('Invalid voice selection', type='warning')
                return

            # Convert selected format to actual format code
            selected_format = tts_format_select.value
            output_format = tts_format_map.get(selected_format, 'opus_48000_128')
            print(f"[TTS DEBUG] Selected format: '{selected_format}' -> '{output_format}'")

            print(f"[TTS] Using voice_id: {voice_id}, format: {output_format}")

            # Clear results and show loading
            tts_results_area.clear()
            with tts_results_area:
                ui.spinner().classes('mr-4')
                ui.label('Generating speech...').classes('text-h6')

            # Generate speech
            print(f"[TTS DEBUG] About to call dashboard.generate_speech...")
            result = await dashboard.generate_speech(
                text=text,
                voice_id=voice_id,
                output_format=output_format
            )
            print(f"[TTS DEBUG] API call result: {result}")

            # Display results
            tts_results_area.clear()
            with tts_results_area:
                if result['success']:
                    ui.label('Speech Generated').classes('text-h6 font-weight-bold mb-3')

                    # Audio player
                    audio_data_b64 = base64.b64encode(result['audio_data']).decode()
                    audio_url = f"data:{result['content_type']};base64,{audio_data_b64}"

                    ui.audio(audio_url).props('controls').classes('w-full mb-4')

                    # Metadata
                    ui.label(f"Format: {result['format']}").classes('text-body2 mb-1')
                    ui.label(f"Size: {result['size']:,} bytes").classes('text-body2 mb-1')

                    # Download button
                    download_filename = f"tts_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    extension = 'opus' if 'opus' in result['format'] else 'mp3' if 'mp3' in result['format'] else 'wav'

                    ui.button(
                        f'Download {extension.upper()}',
                        icon='download',
                        color='secondary'
                    ).props(f'href="{audio_url}" download="{download_filename}.{extension}"')
                else:
                    ui.icon('error', color='negative').classes('mr-2')
                    ui.label(f'Speech generation failed: {result["error"]}').classes('text-negative')

            ui.notify('Speech generated!' if result['success'] else 'Generation failed',
                     type='positive' if result['success'] else 'negative')

        except Exception as e:
            tts_results_area.clear()
            with tts_results_area:
                ui.icon('error', color='negative').classes('mr-2')
                ui.label(f'Generation error: {str(e)}').classes('text-negative')
            ui.notify('Generation failed', type='negative')

    # Setup audio interface
    await setup_audio_interface()

    # Initialize
    if dashboard.current_model:
        await update_model_caps(dashboard.current_model)


if __name__ in {"__main__", "__mp_main__"}:
    print("Starting Comprehensive Tela API Dashboard...")
    print("Features: Chat, Audio Transcription, Text-to-Speech, All parameters, Modern UI")
    print("Opening at http://localhost:8080")
    print("Press Ctrl+C to stop")
    
    ui.run(
        port=8080,
        title='Tela API Comprehensive Dashboard',
        show=True
    )