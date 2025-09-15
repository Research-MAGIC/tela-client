#!/usr/bin/env python3
"""
Tool Calling NiceGUI Example

Interactive web interface for demonstrating function calling capabilities
with the Tela SDK. Features real-time tool execution and result visualization.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
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

# Import the tool registry from CLI example
from tool_calling_cli import ToolRegistry


class ToolCallingApp:
    """NiceGUI application for interactive tool calling"""

    def __init__(self):
        self.client = AsyncTela(
            api_key=os.getenv("TELAOS_API_KEY"),
            organization=os.getenv("TELAOS_ORG_ID"),
            project=os.getenv("TELAOS_PROJECT_ID"),
            enable_history=True
        )
        self.tool_registry = ToolRegistry()
        self.conversation = None
        self.model_name = "qwen3-max"

        # UI elements
        self.chat_container = None
        self.input_field = None
        self.tool_status = None
        self.tool_log = None
        self.send_button = None
        self.is_processing = False

        # Tool execution tracking
        self.execution_log = []

    def setup_ui(self):
        """Setup the main UI components"""
        ui.page_title("Tela SDK - Tool Calling Demo")

        # Add MathJax support for LaTeX rendering
        ui.add_head_html('''
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script type="text/javascript" id="MathJax-script" async
        src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js">
        </script>
        <script type="text/javascript">
        window.MathJax = {
          tex: {
            inlineMath: [['$', '$'], ['\\(', '\\)']],
            displayMath: [['$$', '$$'], ['\\[', '\\]']]
          },
          options: {
            renderActions: {
              addMenu: [0, '', '']
            }
          },
          startup: {
            ready: function () {
              MathJax.startup.defaultReady();

              // Auto-render new content
              const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                  if (mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach(function(node) {
                      if (node.nodeType === 1 && (node.textContent.includes('$') || node.textContent.includes('\\('))) {
                        MathJax.typesetPromise([node]).catch(function (err) {
                          console.log('MathJax typeset failed: ' + err.message);
                        });
                      }
                    });
                  }
                });
              });

              observer.observe(document.body, {
                childList: true,
                subtree: true
              });
            }
          }
        };
        </script>
        ''')

        with ui.column().classes('w-full max-w-6xl mx-auto p-4'):
            # Header
            with ui.card().classes('w-full mb-4'):
                ui.markdown("# [TOOLS] Tela SDK Tool Calling Demo")
                ui.markdown(f"**Model:** {self.model_name} | **Available Tools:** {len(self.tool_registry.tools)}")

                with ui.expansion("Available Tools", icon="build").classes('w-full'):
                    self.create_tools_display()

            # Main content area
            with ui.row().classes('w-full gap-4'):
                # Left side - Chat interface
                with ui.column().classes('w-2/3'):
                    ui.markdown("## 💬 Chat Interface")

                    # Chat messages
                    with ui.card().classes('w-full'):
                        with ui.scroll_area().classes('w-full h-96'):
                            self.chat_container = ui.column().classes('w-full p-2')

                    # Input area
                    with ui.card().classes('w-full mt-4'):
                        with ui.row().classes('w-full'):
                            self.input_field = ui.textarea(
                                placeholder="Ask me anything! I can use tools to help you...",
                                value=""
                            ).classes('flex-grow').style('min-height: 60px')

                            with ui.column().classes('ml-2'):
                                self.send_button = ui.button(
                                    "Send",
                                    on_click=self.send_message,
                                    icon="send"
                                ).classes('mb-2')

                                ui.button(
                                    "Clear",
                                    on_click=self.clear_chat,
                                    icon="clear_all",
                                    color="gray"
                                )

                # Right side - Tool execution panel
                with ui.column().classes('w-1/3'):
                    ui.markdown("## [TOOLS] Tool Execution")

                    # Tool status
                    with ui.card().classes('w-full mb-4'):
                        ui.markdown("### Status")
                        self.tool_status = ui.label("Ready").classes('text-green-600 font-bold')

                    # Tool execution log
                    with ui.card().classes('w-full'):
                        ui.markdown("### Execution Log")
                        with ui.scroll_area().classes('w-full h-64'):
                            self.tool_log = ui.column().classes('w-full p-2')

            # Example queries
            with ui.card().classes('w-full mt-4'):
                ui.markdown("## [EXAMPLES] Example Queries")
                with ui.row().classes('w-full flex-wrap'):
                    examples = [
                        "What's the weather like in Paris?",
                        "Calculate 15 * 7 + 23",
                        "Search for documentation about streaming",
                        "What time is it in Tokyo?",
                        "Find info about error handling and check weather in London"
                    ]

                    for example in examples:
                        ui.button(
                            example,
                            on_click=lambda e=example: self.set_input_and_send(e),
                            color="blue-grey"
                        ).classes('m-1 text-sm')

        # Initialize conversation
        self.new_conversation()


    def create_tools_display(self):
        """Create the tools information display"""
        for name, tool in self.tool_registry.tools.items():
            with ui.card().classes('mb-2'):
                ui.markdown(f"**{name}**: {tool['description']}")

                # Show parameters
                params = tool['parameters'].get('properties', {})
                if params:
                    param_list = []
                    required = tool['parameters'].get('required', [])

                    for param_name, param_info in params.items():
                        param_type = param_info.get('type', 'unknown')
                        is_required = param_name in required
                        req_text = " (required)" if is_required else " (optional)"
                        param_list.append(f"`{param_name}`: {param_type}{req_text}")

                    ui.markdown(f"Parameters: {', '.join(param_list)}")

    async def send_message(self):
        """Send a message and handle tool calling"""
        if self.is_processing or not self.input_field.value.strip():
            return

        user_message = self.input_field.value.strip()
        self.input_field.value = ""
        self.is_processing = True
        self.send_button.disable()
        self.tool_status.text = "Processing..."
        self.tool_status.classes("text-blue-600 font-bold")

        # Add user message to chat
        with self.chat_container:
            self.add_chat_message("user", user_message)

        try:
            # Get conversation messages
            messages = self.conversation.get_messages() + [
                {"role": "user", "content": user_message}
            ]

            # Step 1: Initial request with tools
            response = await self.client.chat.completions.create(
                messages=messages,
                conversation_id=self.conversation.id,
                model=self.model_name,
                tools=self.tool_registry.get_tool_definitions(),
                tool_choice="auto",
                temperature=0.3
            )

            choice = response.choices[0]
            assistant_message = choice.message

            # Check for tool calls
            if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                self.tool_status.text = "Executing tools..."

                # Add thinking message
                with self.chat_container:
                    thinking_msg = self.add_chat_message("assistant", "*Thinking... I need to use some tools to help you.*")

                # Add assistant message to conversation
                messages.append({
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tool_call['id'] if isinstance(tool_call, dict) else tool_call.id,
                            "type": tool_call['type'] if isinstance(tool_call, dict) else tool_call.type,
                            "function": {
                                "name": tool_call['function']['name'] if isinstance(tool_call, dict) else tool_call.function.name,
                                "arguments": tool_call['function']['arguments'] if isinstance(tool_call, dict) else tool_call.function.arguments
                            }
                        }
                        for tool_call in assistant_message.tool_calls
                    ]
                })

                # Execute tools
                tool_results = []
                for tool_call in assistant_message.tool_calls:
                    # Handle dict vs object format
                    if isinstance(tool_call, dict):
                        tool_name = tool_call['function']['name']
                        tool_call_id = tool_call['id']
                        arguments_str = tool_call['function']['arguments']
                    else:
                        tool_name = tool_call.function.name
                        tool_call_id = tool_call.id
                        arguments_str = tool_call.function.arguments

                    try:
                        arguments = json.loads(arguments_str)

                        # Log tool execution
                        self.log_tool_execution(tool_name, arguments, "executing")

                        # Execute tool
                        result = await self.tool_registry.execute_tool(tool_name, arguments)

                        # Add result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": tool_name,
                            "content": json.dumps(result)
                        })

                        # Log successful execution
                        self.log_tool_execution(tool_name, arguments, "success", result)
                        tool_results.append((tool_name, result))

                    except Exception as e:
                        error_result = {"error": str(e)}
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": tool_name,
                            "content": json.dumps(error_result)
                        })

                        # Log failed execution
                        self.log_tool_execution(tool_name, {}, "error", {"error": str(e)})

                # Update thinking message to show tool results
                thinking_msg.clear()
                with thinking_msg:
                    ui.markdown("**[TOOLS] Tool Execution Results:**")
                    for tool_name, result in tool_results:
                        with ui.expansion(f"[DATA] {tool_name}", icon="data_object").classes('w-full'):
                            if "error" in result:
                                ui.markdown(f"[ERROR] **Error:** {result['error']}")
                            else:
                                ui.code(json.dumps(result, indent=2)).classes('text-sm')

                # Step 2: Get final response
                self.tool_status.text = "Generating response..."
                final_response = await self.client.chat.completions.create(
                    messages=messages,
                    conversation_id=self.conversation.id,
                    model=self.model_name,
                    temperature=0.3
                )

                final_content = final_response.choices[0].message.content

                # Add final response to chat
                with self.chat_container:
                    self.add_chat_message("assistant", final_content)


                # Update conversation
                self.conversation.add_message("user", user_message)
                self.conversation.add_message("assistant", final_content)

            else:
                # No tools needed
                content = assistant_message.content

                with self.chat_container:
                    self.add_chat_message("assistant", content)


                self.conversation.add_message("user", user_message)
                self.conversation.add_message("assistant", content)

        except Exception as e:
            with self.chat_container:
                self.add_chat_message("system", f"[ERROR] Error: {str(e)}")

            self.log_tool_execution("system", {}, "error", {"error": str(e)})

        finally:
            self.is_processing = False
            self.send_button.enable()
            self.tool_status.text = "Ready"
            self.tool_status.classes("text-green-600 font-bold")

    def add_chat_message(self, role: str, content: str):
        """Add a message to the chat interface"""
        if role == "user":
            icon = "person"
            color = "blue"
            name = "You"
        elif role == "assistant":
            icon = "smart_toy"
            color = "green"
            name = "Assistant"
        else:
            icon = "info"
            color = "orange"
            name = "System"

        message_container = ui.column().classes('w-full mb-2')
        with message_container:
            with ui.row().classes('w-full items-start'):
                ui.icon(icon).classes(f'text-{color}-600 mt-1')
                with ui.column().classes('flex-grow ml-2'):
                    ui.label(name).classes(f'text-{color}-600 font-semibold text-sm')
                    ui.markdown(content).classes('mt-1')

        return message_container

    def log_tool_execution(self, tool_name: str, arguments: Dict[str, Any], status: str, result: Dict[str, Any] = None):
        """Log tool execution to the execution panel"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        with self.tool_log:
            with ui.card().classes('w-full mb-2'):
                # Header
                if status == "executing":
                    ui.markdown(f"**[EXEC] {timestamp}** - Executing `{tool_name}`")
                    if arguments:
                        ui.markdown(f"Arguments: `{json.dumps(arguments, indent=2)}`")
                elif status == "success":
                    ui.markdown(f"**[OK] {timestamp}** - `{tool_name}` completed")
                    if result and "error" not in result:
                        with ui.expansion("View Result", icon="visibility").classes('w-full'):
                            ui.code(json.dumps(result, indent=2)).classes('text-xs')
                elif status == "error":
                    ui.markdown(f"**[ERROR] {timestamp}** - `{tool_name}` failed")
                    if result:
                        ui.markdown(f"Error: `{result.get('error', 'Unknown error')}`")

    def set_input_and_send(self, text: str):
        """Set input field text and send message"""
        self.input_field.value = text
        asyncio.create_task(self.send_message())

    def clear_chat(self):
        """Clear the chat interface"""
        self.chat_container.clear()
        self.tool_log.clear()
        self.conversation.clear_messages()

        # Add welcome message
        with self.chat_container:
            self.add_chat_message("assistant", "Hello! I'm ready to help. I can use various tools to answer your questions. Try asking me about weather, calculations, documentation, or time!")

    def new_conversation(self):
        """Start a new conversation"""
        self.conversation = self.client.create_conversation("nicegui-tool-demo")
        self.clear_chat()


class SimpleToolDemo:
    """Simplified tool demo for quick testing"""

    def __init__(self):
        self.client = AsyncTela(
            api_key=os.getenv("TELAOS_API_KEY"),
            organization=os.getenv("TELAOS_ORG_ID"),
            project=os.getenv("TELAOS_PROJECT_ID")
        )
        self.tool_registry = ToolRegistry()
        self.model_name = "qwen3-max"
        self.result_area = None

    def setup_ui(self):
        """Setup simple demo UI"""
        ui.markdown("## [TOOLS] Simple Tool Calling Demo")
        ui.markdown(f"**Model:** {self.model_name}")

        # Quick test buttons
        with ui.row().classes('w-full mb-4'):
            ui.button(
                "Weather Test",
                on_click=lambda: asyncio.create_task(self.run_test("What's the weather in New York?")),
                icon="wb_sunny"
            ).classes('mr-2')

            ui.button(
                "Math Test",
                on_click=lambda: asyncio.create_task(self.run_test("Calculate 42 * 17 + 89")),
                icon="calculate"
            ).classes('mr-2')

            ui.button(
                "Search Test",
                on_click=lambda: asyncio.create_task(self.run_test("Search for API documentation")),
                icon="search"
            ).classes('mr-2')

            ui.button(
                "Time Test",
                on_click=lambda: asyncio.create_task(self.run_test("What time is it?")),
                icon="schedule"
            )

        # Custom query
        with ui.row().classes('w-full mb-4'):
            self.custom_input = ui.input(
                placeholder="Enter custom query...",
                on_change=lambda: None
            ).classes('flex-grow')

            ui.button(
                "Test",
                on_click=lambda: asyncio.create_task(self.run_test(self.custom_input.value)),
                icon="play_arrow"
            ).classes('ml-2')

        # Results area
        ui.separator()
        ui.markdown("### Results")
        self.result_area = ui.markdown("Click a test button to see tool calling in action!")

    async def run_test(self, query: str):
        """Run a test query"""
        if not query.strip():
            return

        self.result_area.content = f"**Query:** {query}\n\n*Processing...*"

        try:
            # Simple tool calling flow
            messages = [{"role": "user", "content": query}]

            response = await self.client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                tools=self.tool_registry.get_tool_definitions(),
                tool_choice="auto",
                temperature=0.3
            )

            choice = response.choices[0]
            assistant_message = choice.message

            if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                result_text = f"**Query:** {query}\n\n**Tools Used:**\n\n"

                # Execute tools
                messages.append({
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tc['id'] if isinstance(tc, dict) else tc.id,
                            "type": tc['type'] if isinstance(tc, dict) else tc.type,
                            "function": {
                                "name": tc['function']['name'] if isinstance(tc, dict) else tc.function.name,
                                "arguments": tc['function']['arguments'] if isinstance(tc, dict) else tc.function.arguments
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ]
                })

                for tool_call in assistant_message.tool_calls:
                    # Handle dict vs object format
                    if isinstance(tool_call, dict):
                        tool_name = tool_call['function']['name']
                        tool_call_id = tool_call['id']
                        arguments_str = tool_call['function']['arguments']
                    else:
                        tool_name = tool_call.function.name
                        tool_call_id = tool_call.id
                        arguments_str = tool_call.function.arguments

                    arguments = json.loads(arguments_str)

                    result_text += f"**{tool_name}** with args: `{arguments}`\n"

                    tool_result = await self.tool_registry.execute_tool(tool_name, arguments)

                    # Add tool result info to display
                    if "error" in tool_result:
                        result_text += f"  - **Error:** {tool_result['error']}\n\n"
                    else:
                        # Show key result fields
                        if "result" in tool_result:
                            result_text += f"  - **Result:** {tool_result['result']}\n\n"
                        elif "temperature" in tool_result:
                            result_text += f"  - **Temperature:** {tool_result['temperature']}{tool_result.get('unit', '')}\n"
                            result_text += f"  - **Condition:** {tool_result.get('condition', 'N/A')}\n\n"
                        elif "time" in tool_result:
                            result_text += f"  - **Time:** {tool_result['time']}\n"
                            result_text += f"  - **Date:** {tool_result.get('date', 'N/A')}\n\n"
                        elif "results" in tool_result:
                            result_text += f"  - **Found:** {len(tool_result['results'])} results\n\n"
                        else:
                            result_text += f"  - **Data:** {json.dumps(tool_result, indent=2)}\n\n"

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "name": tool_name,
                        "content": json.dumps(tool_result)
                    })

                # Get final response
                final_response = await self.client.chat.completions.create(
                    messages=messages,
                    model=self.model_name,
                    temperature=0.3
                )

                final_content = final_response.choices[0].message.content
                result_text += f"\n**Final Response:**\n{final_content}"

                self.result_area.content = result_text

            else:
                # No tools used
                content = assistant_message.content
                self.result_area.content = f"**Query:** {query}\n\n**Response (no tools used):**\n{content}"


        except Exception as e:
            self.result_area.content = f"**Query:** {query}\n\n**Error:** {str(e)}"


def create_main_app():
    """Create the main application"""
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
        interactive_tab = ui.tab('Interactive Demo', icon='chat')
        simple_tab = ui.tab('Simple Demo', icon='play_arrow')

    with ui.tab_panels(tabs, value=interactive_tab).classes('w-full'):
        # Interactive demo
        with ui.tab_panel(interactive_tab):
            app_demo = ToolCallingApp()
            app_demo.setup_ui()

        # Simple demo
        with ui.tab_panel(simple_tab):
            simple_demo = SimpleToolDemo()
            simple_demo.setup_ui()


def main():
    """Run the NiceGUI application"""
    if not NICEGUI_AVAILABLE:
        return

    ui.page_title("Tela SDK - Tool Calling Examples")

    create_main_app()

    # Run the app
    ui.run(
        title="Tela SDK Tool Calling Examples",
        port=8081,
        show=True,
        reload=False
    )


if __name__ == "__main__":
    main()