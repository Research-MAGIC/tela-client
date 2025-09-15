"""
Simple NiceGUI test to demonstrate Tela API endpoint functionality
"""

import asyncio
import sys
import os
from typing import List
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from nicegui import ui
    from tela import AsyncTela
except ImportError:
    print("Missing dependencies. Please install: pip install nicegui")
    exit(1)


class SimpleDemo:
    def __init__(self):
        load_dotenv()
        self.client = AsyncTela()
        self.models: List[str] = []
        
    async def initialize(self):
        try:
            models_response = await self.client.get_models()
            self.models = [model.id for model in models_response.data]
            print(f"Loaded {len(self.models)} models successfully!")
            return True
        except Exception as e:
            print(f"Failed to initialize: {e}")
            return False

    async def test_chat(self, message: str, model: str, temperature: float):
        """Test chat with parameters"""
        try:
            response = await self.client.chat.completions.create(
                messages=[{"role": "user", "content": message}],
                model=model,
                temperature=temperature,
                max_tokens=100
            )
            
            content = response.choices[0].message.content
            usage = self.client.get_usage_from_response(response)
            
            return {
                "content": content,
                "usage": usage
            }
        except Exception as e:
            return {"error": str(e)}

# Global demo instance
demo = None

async def setup():
    global demo
    if demo is None:
        demo = SimpleDemo()
        success = await demo.initialize()
        if not success:
            return False
    return True

@ui.page('/')
async def main_page():
    """Main demo page"""
    if not await setup():
        ui.label("❌ Failed to initialize. Check your .env file with Tela API credentials.")
        return
    
    ui.label("🤖 Tela API Simple Test").style('font-size: 24px; font-weight: bold; margin-bottom: 20px;')
    
    with ui.column().style('max-width: 800px; margin: 0 auto; padding: 20px;'):
        
        # Model selection
        ui.label("Select Model:").style('font-weight: bold; margin-top: 20px;')
        model_select = ui.select(
            options=demo.models,
            value=demo.models[0] if demo.models else None
        ).style('width: 300px;')
        
        # Temperature control  
        ui.label("Temperature:").style('font-weight: bold; margin-top: 20px;')
        temp_slider = ui.slider(min=0.0, max=2.0, value=0.7, step=0.1).props('label-always').style('width: 300px;')
        
        # Message input
        ui.label("Message:").style('font-weight: bold; margin-top: 20px;')
        message_input = ui.input(placeholder='Enter your message...').style('width: 100%;')

        # Results area
        results_area = ui.column().style('margin-top: 20px; min-height: 200px;')

        # Initialize button variable
        send_btn = None

        async def send_message():
            """Send message and display results"""
            message = message_input.value.strip()
            if not message:
                ui.notify('Please enter a message', type='warning')
                return

            if not model_select.value:
                ui.notify('Please select a model', type='warning')
                return

            # Disable button during processing if it exists
            if send_btn:
                send_btn.disable()
            
            # Clear results and show loading
            results_area.clear()
            with results_area:
                ui.spinner().style('margin: 20px;')
                ui.label("Sending request...")

            # Force UI update
            ui.update()
            await asyncio.sleep(0.1)
            
            try:
                # Send request
                result = await demo.test_chat(
                    message=message,
                    model=model_select.value,
                    temperature=temp_slider.value
                )

                # Display results
                results_area.clear()
                with results_area:
                    if 'error' in result:
                        ui.label(f"❌ Error: {result['error']}").style('color: red;')
                    else:
                        ui.label("✅ Response:").style('font-weight: bold; color: green;')
                        ui.markdown(result['content']).style('background: #f5f5f5; padding: 10px; border-radius: 5px; margin: 10px 0;')

                        if result['usage']:
                            usage = result['usage']
                            ui.label("📊 Usage Statistics:").style('font-weight: bold; margin-top: 15px;')
                            ui.label(f"• Prompt tokens: {usage.prompt_tokens}")
                            ui.label(f"• Completion tokens: {usage.completion_tokens}")
                            ui.label(f"• Total tokens: {usage.total_tokens}")
                            ui.label(f"• Efficiency: {usage.efficiency_ratio:.1%}")

                # Clear the input field after successful send
                message_input.value = ''
                ui.notify('Response generated!', type='positive')

            except Exception as e:
                # Handle any unexpected errors
                results_area.clear()
                with results_area:
                    ui.label(f"❌ Unexpected Error: {str(e)}").style('color: red;')
                ui.notify('Error occurred!', type='negative')

            finally:
                # Always re-enable button if it exists
                if send_btn:
                    send_btn.enable()

        # Create button and input handlers after function is defined
        send_btn = ui.button('Send Message', on_click=send_message)
        message_input.on('keydown.enter', send_message)
        
        # Show model info
        ui.label("📋 Available Features:").style('font-weight: bold; margin-top: 30px;')
        ui.label(f"• {len(demo.models)} models available")
        ui.label("• Real-time parameter adjustment")
        ui.label("• Usage statistics tracking")  
        ui.label("• Interactive chat interface")
        
        # Quick test buttons
        ui.label("🎯 Quick Tests:").style('font-weight: bold; margin-top: 20px;')
        
        with ui.row().style('gap: 10px; flex-wrap: wrap;'):
            ui.button('Test Creativity (temp=1.5)', 
                     on_click=lambda: (
                         temp_slider.set_value(1.5),
                         message_input.set_value('Write a creative story about a robot'),
                         None
                     ))
            ui.button('Test Precision (temp=0.1)',
                     on_click=lambda: (
                         temp_slider.set_value(0.1), 
                         message_input.set_value('What is 25 * 4?'),
                         None
                     ))
            ui.button('Test Coding',
                     on_click=lambda: (
                         temp_slider.set_value(0.3),
                         message_input.set_value('Write a Python function to reverse a string'),
                         None
                     ))

if __name__ in {"__main__", "__mp_main__"}:
    print("Starting Simple Tela API NiceGUI Demo...")
    print("Make sure your .env file has the required credentials")
    print("Opening browser at http://localhost:8080")
    
    ui.run(
        port=8080,
        title='Tela API Simple Demo',
        show=True
    )