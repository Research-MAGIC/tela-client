#!/usr/bin/env python3
"""
Example: Streaming chat completions in NiceGUI applications

This example demonstrates how to use the Tela client for streaming
responses in NiceGUI web interfaces with real-time updates.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from nicegui import ui, app
    NICEGUI_AVAILABLE = True
except ImportError:
    print("NiceGUI is not installed. Install with: pip install nicegui")
    NICEGUI_AVAILABLE = False
    sys.exit(1)

from tela import AsyncTela
from tela._streaming_utils import (
    NiceGUIStreamHandler,
    StreamingDisplay,
    stream_to_nicegui_chat,
    create_nicegui_stream_handler
)


class StreamingChatApp:
    """A complete streaming chat application using NiceGUI"""

    def __init__(self):
        self.client = AsyncTela(
            api_key=os.getenv("TELAOS_API_KEY"),
            organization=os.getenv("TELAOS_ORG_ID"),
            project=os.getenv("TELAOS_PROJECT_ID"),
            enable_history=True
        )
        self.conversation = None
        self.messages_container = None
        self.input_field = None
        self.is_streaming = False
        self.model_name = "qwen3-max"  # Default model
        # Avatar URLs
        self.user_avatar = "https://robohash.org/user?set=set2&size=40x40"
        self.bot_avatar = "https://robohash.org/bot?set=set1&size=40x40"
    
    def setup_ui(self):
        """Setup the main UI components"""
        ui.page_title("Tela Streaming Chat Demo")

        with ui.column().classes('w-full max-w-4xl mx-auto p-4'):
            # Header
            ui.markdown("# Tela Streaming Chat Demo")
            ui.markdown(f"**Model:** {self.model_name}")
            ui.separator()
            
            # Chat messages container
            with ui.scroll_area().classes('w-full h-96 border rounded p-4'):
                self.messages_container = ui.column().classes('w-full')
            
            # Input area
            with ui.row().classes('w-full mt-4'):
                self.input_field = ui.input(
                    placeholder="Type your message...",
                    on_change=lambda: None
                ).classes('flex-grow')
                
                ui.button(
                    "Send",
                    on_click=self.send_message
                ).classes('ml-2')
            
            # Controls
            with ui.row().classes('w-full mt-4'):
                ui.button(
                    "Clear Chat",
                    on_click=self.clear_chat
                ).classes('mr-2')
                
                ui.button(
                    "New Conversation",
                    on_click=self.new_conversation
                ).classes('mr-2')
        
        # Initialize conversation
        self.new_conversation()
    
    async def send_message(self):
        """Send a message and stream the response"""
        if self.is_streaming or not self.input_field.value.strip():
            return
        
        user_message = self.input_field.value.strip()
        self.input_field.value = ""
        
        # Add user message to UI
        with self.messages_container:
            with ui.chat_message(name="You", avatar=self.user_avatar):
                ui.markdown(user_message)
        
        # Add user message to conversation history
        messages = self.conversation.get_messages() + [
            {"role": "user", "content": user_message}
        ]
        
        self.is_streaming = True
        
        try:
            # Create assistant message container
            with self.messages_container:
                with ui.chat_message(name="Assistant", avatar=self.bot_avatar):
                    response_element = ui.markdown("")
            
            # Stream the response
            stream = await self.client.chat.completions.create(
                messages=messages,
                conversation_id=self.conversation.id,
                model=self.model_name,
                stream=True,
                temperature=0.5
            )
            
            accumulated_response = ""
            async for chunk in stream:
                if hasattr(chunk, 'choices') and chunk.choices:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta') and choice.delta and choice.delta.content:
                        content = choice.delta.content
                        accumulated_response += content
                        response_element.content = accumulated_response
                        # Small delay for smoother typing effect
                        await asyncio.sleep(0.02)
            
            # Update conversation history
            self.conversation.add_message("user", user_message)
            self.conversation.add_message("assistant", accumulated_response)
            
        except Exception as e:
            with self.messages_container:
                with ui.chat_message(name="Error", avatar="https://robohash.org/error?set=set3&size=40x40"):
                    ui.markdown(f"Error: {str(e)}")
        
        finally:
            self.is_streaming = False
    
    def clear_chat(self):
        """Clear the chat interface"""
        self.messages_container.clear()
        if self.conversation:
            self.conversation.clear_messages()
    
    def new_conversation(self):
        """Start a new conversation"""
        self.conversation = self.client.create_conversation()
        self.clear_chat()
        
        # Add welcome message
        with self.messages_container:
            with ui.chat_message(name="Assistant", avatar="https://robohash.org/bot?set=set1&size=40x40"):
                ui.markdown("Hello! I'm ready to help. Ask me anything!")


class SimpleStreamingDemo:
    """Simple streaming demo with basic UI elements"""

    def __init__(self):
        self.client = AsyncTela(
            api_key=os.getenv("TELAOS_API_KEY"),
            organization=os.getenv("TELAOS_ORG_ID"),
            project=os.getenv("TELAOS_PROJECT_ID")
        )
        self.output_element = None
        self.model_name = "qwen3-max"  # Default model
        self.is_streaming = False
        self.current_task = None
    
    def setup_ui(self):
        """Setup simple demo UI"""
        ui.markdown("## Simple Streaming Demo")
        ui.markdown(f"**Model:** {self.model_name}")

        # Predefined questions
        questions = [
            "What is machine learning?",
            "Explain quantum computing",
            "How does blockchain work?",
            "What is artificial intelligence?"
        ]

        with ui.row():
            for question in questions:
                ui.button(
                    question,
                    on_click=lambda q=question: asyncio.create_task(self.ask_question(q))
                ).classes('m-1')

        # Control buttons
        with ui.row().classes('mt-2'):
            self.stop_button = ui.button(
                "Stop",
                on_click=self.stop_streaming,
                color='red'
            ).classes('m-1')
            self.stop_button.disable()

        ui.separator()

        # Output area
        self.output_element = ui.markdown("").classes('border rounded p-4 min-h-32')
    
    async def ask_question(self, question: str):
        """Ask a question and stream the response"""
        if self.is_streaming:
            return

        self.is_streaming = True
        self.stop_button.enable()
        self.output_element.content = f"**Question:** {question}\n\n**Answer:** "

        messages = [{"role": "user", "content": question}]

        try:
            stream = await self.client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                stream=True,
                temperature=0.5
            )

            accumulated = f"**Question:** {question}\n\n**Answer:** "
            async for chunk in stream:
                if not self.is_streaming:  # Check if stopped
                    break

                if hasattr(chunk, 'choices') and chunk.choices:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta') and choice.delta and choice.delta.content:
                        accumulated += choice.delta.content
                        self.output_element.content = accumulated
                        await asyncio.sleep(0.03)

        except Exception as e:
            self.output_element.content += f"\n\n**Error:** {str(e)}"

        finally:
            self.is_streaming = False
            self.stop_button.disable()

    def stop_streaming(self):
        """Stop the current streaming operation"""
        self.is_streaming = False
        self.stop_button.disable()


class AdvancedStreamingDemo:
    """Advanced streaming demo with multiple UI components"""

    def __init__(self):
        self.client = AsyncTela(
            api_key=os.getenv("TELAOS_API_KEY"),
            organization=os.getenv("TELAOS_ORG_ID"),
            project=os.getenv("TELAOS_PROJECT_ID"),
            enable_history=True
        )
        self.conversation = None
        self.status_label = None
        self.progress_bar = None
        self.metrics_card = None
        self.model_name = "qwen3-max"  # Default model
    
    def setup_ui(self):
        """Setup advanced demo UI"""
        ui.markdown("## Advanced Streaming Demo")
        ui.markdown(f"**Model:** {self.model_name}")
        
        with ui.row().classes('w-full'):
            # Left column - Input and controls
            with ui.column().classes('w-1/3'):
                ui.markdown("### Controls")
                
                self.prompt_input = ui.textarea(
                    label="Enter your prompt",
                    placeholder="Ask anything..."
                ).classes('w-full')
                
                with ui.row():
                    ui.button("Stream Response", on_click=self.stream_response)
                    ui.button("Clear", on_click=self.clear_output)
                
                # Settings
                ui.separator()
                ui.markdown("### Settings")
                
                self.temperature_slider = ui.slider(
                    min=0, max=2, value=0.5, step=0.1
                ).props('label-always')
                ui.label().bind_text_from(self.temperature_slider, 'value',
                                        lambda v: f'Temperature: {v:.1f}')
                
                self.max_tokens_input = ui.number(
                    label="Max Tokens", value=5000
                ).classes('w-full')
            
            # Right column - Output and metrics
            with ui.column().classes('w-2/3 pl-4'):
                ui.markdown("### Response")
                
                # Status and progress
                self.status_label = ui.label("Ready").classes('text-blue-600')
                self.progress_bar = ui.linear_progress(value=0).classes('w-full')
                
                # Output area with typing indicator
                with ui.scroll_area().classes('w-full h-64 border rounded'):
                    self.output_area = ui.column().classes('p-4')
                
                # Metrics
                self.metrics_card = ui.card().classes('w-full mt-4')
                with self.metrics_card:
                    ui.markdown("### Streaming Metrics")
                    self.metrics_content = ui.column()
        
        # Initialize
        self.conversation = self.client.create_conversation("advanced-demo")
        self.update_metrics(0, 0, 0)
    
    async def stream_response(self):
        """Stream a response with advanced metrics"""
        if not self.prompt_input.value.strip():
            return
        
        prompt = self.prompt_input.value.strip()
        self.prompt_input.value = ""
        
        # Clear output and setup
        self.output_area.clear()
        self.status_label.text = "Streaming..."
        self.progress_bar.value = 0
        
        # Create response container
        with self.output_area:
            ui.markdown(f"**Prompt:** {prompt}")
            ui.separator()
            response_markdown = ui.markdown("**Response:**")
        
        # Prepare request
        messages = self.conversation.get_messages() + [
            {"role": "user", "content": prompt}
        ]
        
        try:
            stream = await self.client.chat.completions.create(
                messages=messages,
                conversation_id=self.conversation.id,
                model=self.model_name,
                stream=True,
                temperature=self.temperature_slider.value,
                max_tokens=int(self.max_tokens_input.value) if self.max_tokens_input.value else None
            )
            
            # Streaming metrics
            start_time = asyncio.get_event_loop().time()
            chunk_count = 0
            accumulated_response = "**Response:**\n\n"
            
            async for chunk in stream:
                chunk_count += 1
                
                if hasattr(chunk, 'choices') and chunk.choices:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta') and choice.delta and choice.delta.content:
                        content = choice.delta.content
                        accumulated_response += content
                        response_markdown.content = accumulated_response
                        
                        # Update progress (simulated)
                        progress = min(chunk_count / 50, 1.0)
                        self.progress_bar.value = progress
                        
                        # Update metrics in real-time
                        elapsed = asyncio.get_event_loop().time() - start_time
                        self.update_metrics(chunk_count, len(accumulated_response), elapsed)
                        
                        await asyncio.sleep(0.02)
            
            # Finalize
            self.status_label.text = "Complete"
            self.progress_bar.value = 1.0
            
            # Update conversation
            self.conversation.add_message("user", prompt)
            self.conversation.add_message("assistant", accumulated_response.replace("**Response:**\n\n", ""))
            
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"
            with self.output_area:
                ui.markdown(f"**Error:** {str(e)}")
    
    def update_metrics(self, chunks: int, chars: int, elapsed: float):
        """Update streaming metrics display"""
        self.metrics_content.clear()
        with self.metrics_content:
            ui.label(f"Chunks received: {chunks}")
            ui.label(f"Characters: {chars}")
            ui.label(f"Elapsed time: {elapsed:.2f}s")
            if elapsed > 0:
                ui.label(f"Rate: {chunks/elapsed:.1f} chunks/sec")
    
    def clear_output(self):
        """Clear the output area"""
        self.output_area.clear()
        self.status_label.text = "Ready"
        self.progress_bar.value = 0
        self.update_metrics(0, 0, 0)


def create_main_app():
    """Create the main application with multiple demos"""
    
    # Check for API credentials
    if not all([
        os.getenv("TELAOS_API_KEY"),
        os.getenv("TELAOS_ORG_ID"),
        os.getenv("TELAOS_PROJECT_ID")
    ]):
        ui.markdown("## ⚠️ Configuration Required")
        ui.markdown("Set the following environment variables:")
        ui.markdown("- `TELAOS_API_KEY`")
        ui.markdown("- `TELAOS_ORG_ID`") 
        ui.markdown("- `TELAOS_PROJECT_ID`")
        return
    
    # Tab container for different demos
    with ui.tabs().classes('w-full') as tabs:
        chat_tab = ui.tab('Chat', icon='chat')
        simple_tab = ui.tab('Simple', icon='play_arrow')
        advanced_tab = ui.tab('Advanced', icon='settings')
    
    with ui.tab_panels(tabs, value=chat_tab).classes('w-full'):
        # Chat demo
        with ui.tab_panel(chat_tab):
            chat_app = StreamingChatApp()
            chat_app.setup_ui()
        
        # Simple demo
        with ui.tab_panel(simple_tab):
            simple_demo = SimpleStreamingDemo()
            simple_demo.setup_ui()
        
        # Advanced demo
        with ui.tab_panel(advanced_tab):
            advanced_demo = AdvancedStreamingDemo()
            advanced_demo.setup_ui()


def main():
    """Run the NiceGUI application"""
    if not NICEGUI_AVAILABLE:
        return
    
    ui.page_title("Tela Streaming Examples")
    
    create_main_app()
    
    # Run the app
    ui.run(
        title="Tela Streaming Examples",
        port=8080,
        show=True,
        reload=False
    )


if __name__ == "__main__":
    main()