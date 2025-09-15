#!/usr/bin/env python3
"""
Tool Calling CLI Example

Interactive CLI demonstration of function calling capabilities with the Tela SDK.
Shows how to define, register, and execute tools with typed parameters.
"""

import asyncio
import json
import os
import random
import time
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from tela import AsyncTela


class ToolRegistry:
    """Registry for managing available tools and their execution"""

    def __init__(self):
        self.tools = {}
        self.register_default_tools()

    def register_tool(self, name: str, func: callable, description: str, parameters: dict):
        """Register a new tool with its function and schema"""
        self.tools[name] = {
            "function": func,
            "description": description,
            "parameters": parameters
        }

    def register_default_tools(self):
        """Register the default set of tools"""

        # Weather tool
        self.register_tool(
            name="get_weather",
            func=self.get_weather,
            description="Get current weather information for a city",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The city name"},
                    "units": {
                        "type": "string",
                        "enum": ["metric", "imperial"],
                        "default": "metric",
                        "description": "Temperature units"
                    }
                },
                "required": ["city"]
            }
        )

        # Document search tool
        self.register_tool(
            name="search_docs",
            func=self.search_docs,
            description="Search through documentation and knowledge base",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 20,
                        "default": 5,
                        "description": "Number of results to return"
                    }
                },
                "required": ["query"]
            }
        )

        # Calculator tool
        self.register_tool(
            name="calculate",
            func=self.calculate,
            description="Perform mathematical calculations",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Mathematical expression to evaluate"},
                    "precision": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 10,
                        "default": 2,
                        "description": "Decimal places for the result"
                    }
                },
                "required": ["expression"]
            }
        )

        # Time tool
        self.register_tool(
            name="get_time",
            func=self.get_time,
            description="Get current time in different timezones",
            parameters={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "default": "UTC",
                        "description": "Timezone (UTC, EST, PST, etc.)"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["12h", "24h", "iso"],
                        "default": "24h",
                        "description": "Time format"
                    }
                },
                "required": []
            }
        )

    async def get_weather(self, city: str, units: str = "metric") -> Dict[str, Any]:
        """Simulate weather API call"""
        # Simulate API delay
        await asyncio.sleep(0.5)

        # Mock weather data
        weather_data = {
            "metric": {
                "temp": random.randint(15, 35),
                "feels_like": random.randint(15, 35),
                "unit": "°C"
            },
            "imperial": {
                "temp": random.randint(59, 95),
                "feels_like": random.randint(59, 95),
                "unit": "°F"
            }
        }

        conditions = ["sunny", "partly cloudy", "cloudy", "rainy", "windy"]
        condition = random.choice(conditions)

        data = weather_data[units]

        return {
            "city": city,
            "temperature": data["temp"],
            "feels_like": data["feels_like"],
            "unit": data["unit"],
            "condition": condition,
            "humidity": random.randint(30, 90),
            "wind_speed": random.randint(5, 25),
            "timestamp": datetime.now().isoformat()
        }

    async def search_docs(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Simulate document search"""
        await asyncio.sleep(0.3)

        # Mock search results
        mock_docs = [
            {"title": "Getting Started Guide", "content": "Basic setup and installation instructions"},
            {"title": "API Reference", "content": "Complete API documentation and examples"},
            {"title": "Tool Calling Tutorial", "content": "How to implement function calling"},
            {"title": "Streaming Responses", "content": "Working with real-time streaming"},
            {"title": "Error Handling", "content": "Best practices for error management"},
            {"title": "Authentication", "content": "API key and token management"},
            {"title": "Rate Limiting", "content": "Understanding API rate limits"},
            {"title": "Conversation History", "content": "Managing chat conversations"}
        ]

        # Simple mock search - return random subset
        results = random.sample(mock_docs, min(top_k, len(mock_docs)))

        return {
            "query": query,
            "results_count": len(results),
            "results": results,
            "search_time_ms": random.randint(50, 200)
        }

    async def calculate(self, expression: str, precision: int = 2) -> Dict[str, Any]:
        """Safe calculator implementation"""
        try:
            # Simple whitelist of allowed operations
            allowed_chars = "0123456789+-*/.() "
            if not all(c in allowed_chars for c in expression):
                raise ValueError("Invalid characters in expression")

            # Evaluate safely
            result = eval(expression)
            formatted_result = round(result, precision)

            return {
                "expression": expression,
                "result": formatted_result,
                "precision": precision,
                "type": type(result).__name__
            }
        except Exception as e:
            return {
                "expression": expression,
                "error": str(e),
                "result": None
            }

    async def get_time(self, timezone: str = "UTC", format: str = "24h") -> Dict[str, Any]:
        """Get current time information"""
        now = datetime.now()

        # Simple timezone simulation (not comprehensive)
        timezone_offsets = {
            "UTC": 0, "EST": -5, "PST": -8, "CET": 1, "JST": 9
        }

        if format == "12h":
            time_str = now.strftime("%I:%M:%S %p")
        elif format == "iso":
            time_str = now.isoformat()
        else:  # 24h
            time_str = now.strftime("%H:%M:%S")

        return {
            "timezone": timezone,
            "format": format,
            "time": time_str,
            "date": now.strftime("%Y-%m-%d"),
            "weekday": now.strftime("%A"),
            "timestamp": now.timestamp()
        }

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get OpenAI-compatible tool definitions"""
        definitions = []
        for name, tool in self.tools.items():
            definitions.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            })
        return definitions

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name with given arguments"""
        if name not in self.tools:
            return {"error": f"Tool '{name}' not found"}

        try:
            tool_func = self.tools[name]["function"]
            result = await tool_func(**arguments)
            return result
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}


class ToolCallingCLI:
    """Interactive CLI for demonstrating tool calling"""

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

    def display_header(self):
        """Display application header"""
        print("=" * 70)
        print("[TOOLS] TELA SDK - TOOL CALLING INTERACTIVE DEMO")
        print("=" * 70)
        print(f"Model: {self.model_name}")
        print(f"Available Tools: {len(self.tool_registry.tools)}")
        print("\nThis demo shows how to use function calling with the Tela SDK.")
        print("Try asking questions that would benefit from tool usage!")
        print("-" * 70)

    def display_available_tools(self):
        """Display available tools and their descriptions"""
        print("\n[TOOLS] AVAILABLE TOOLS:")
        print("-" * 40)
        for name, tool in self.tool_registry.tools.items():
            print(f"• {name}: {tool['description']}")
        print()

    def display_examples(self):
        """Display example queries"""
        print("[EXAMPLES] EXAMPLE QUERIES:")
        print("-" * 30)
        examples = [
            "What's the weather like in Paris?",
            "Search for documentation about streaming",
            "Calculate 15 * 7 + 23",
            "What time is it in Tokyo?",
            "Find docs about error handling and tell me the weather in London"
        ]
        for i, example in enumerate(examples, 1):
            print(f"{i}. {example}")
        print()

    async def process_user_input(self, user_input: str) -> None:
        """Process user input and handle tool calling flow"""
        print(f"\n[USER] {user_input}")
        print("[ASSISTANT] ", end="", flush=True)

        # Get current conversation messages
        messages = self.conversation.get_messages() + [
            {"role": "user", "content": user_input}
        ]

        try:
            # Step 1: Make initial request with tools
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

            # Check if the model wants to use tools
            if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                print("[Requesting tool execution...]")

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

                # Execute each tool call
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
                        # Parse arguments
                        arguments = json.loads(arguments_str)
                        print(f"\n[EXEC] Executing {tool_name}({', '.join(f'{k}={v}' for k, v in arguments.items())})")

                        # Execute tool
                        tool_result = await self.tool_registry.execute_tool(tool_name, arguments)

                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": tool_name,
                            "content": json.dumps(tool_result)
                        })

                        print(f"[OK] {tool_name} completed successfully")

                    except json.JSONDecodeError as e:
                        error_result = {"error": f"Invalid JSON arguments: {str(e)}"}
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": tool_name,
                            "content": json.dumps(error_result)
                        })
                        print(f"[ERROR] {tool_name} failed: Invalid arguments")

                # Step 2: Get final response with tool results
                print("\n[ASSISTANT] ", end="", flush=True)
                final_response = await self.client.chat.completions.create(
                    messages=messages,
                    conversation_id=self.conversation.id,
                    model=self.model_name,
                    temperature=0.3
                )

                final_content = final_response.choices[0].message.content
                print(final_content)

                # Update conversation
                self.conversation.add_message("user", user_input)
                self.conversation.add_message("assistant", final_content)

            else:
                # No tools needed, direct response
                content = assistant_message.content
                print(content)

                # Update conversation
                self.conversation.add_message("user", user_input)
                self.conversation.add_message("assistant", content)

        except Exception as e:
            print(f"[ERROR] Error: {str(e)}")

    async def run_interactive_mode(self):
        """Run the interactive CLI"""
        self.display_header()
        self.display_available_tools()
        self.display_examples()

        # Initialize conversation
        self.conversation = self.client.create_conversation("tool-calling-demo")

        print("Type 'quit' to exit, 'tools' to see available tools, 'examples' for example queries")
        print("=" * 70)

        while True:
            try:
                user_input = input("\n[CHAT] Enter your question: ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n[BYE] Thanks for using the Tool Calling Demo!")
                    break
                elif user_input.lower() == 'tools':
                    self.display_available_tools()
                    continue
                elif user_input.lower() == 'examples':
                    self.display_examples()
                    continue
                elif not user_input:
                    continue

                await self.process_user_input(user_input)

            except KeyboardInterrupt:
                print("\n\n[BYE] Exiting...")
                break
            except Exception as e:
                print(f"\n[ERROR] Unexpected error: {str(e)}")


async def demo_mode():
    """Run a demonstration of tool calling capabilities"""
    print("\n[DEMO] DEMO MODE - Automated Tool Calling Examples")
    print("=" * 60)

    cli = ToolCallingCLI()
    cli.conversation = cli.client.create_conversation("tool-demo")

    demo_queries = [
        "What's the weather like in Tokyo?",
        "Calculate the result of 25 * 4 + 17",
        "Search for information about API authentication",
        "What time is it right now?"
    ]

    for i, query in enumerate(demo_queries, 1):
        print(f"\n--- Demo {i}/{len(demo_queries)} ---")
        await cli.process_user_input(query)
        await asyncio.sleep(1)  # Brief pause between demos

    print("\n[OK] Demo completed!")


async def main():
    """Main application entry point"""
    if not all([
        os.getenv("TELAOS_API_KEY"),
        os.getenv("TELAOS_ORG_ID"),
        os.getenv("TELAOS_PROJECT_ID")
    ]):
        print("[ERROR] Missing required environment variables:")
        print("   - TELAOS_API_KEY")
        print("   - TELAOS_ORG_ID")
        print("   - TELAOS_PROJECT_ID")
        print("\nPlease set these in your .env file")
        return

    print("[TOOLS] Tela SDK Tool Calling Examples")
    print("\nChoose mode:")
    print("1. Interactive Mode (recommended)")
    print("2. Demo Mode (automated examples)")
    print("3. Quit")

    while True:
        try:
            choice = input("\nEnter choice (1-3): ").strip()

            if choice == "1":
                cli = ToolCallingCLI()
                await cli.run_interactive_mode()
                break
            elif choice == "2":
                await demo_mode()
                break
            elif choice == "3":
                print("[BYE] Goodbye!")
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")

        except KeyboardInterrupt:
            print("\n[BYE] Goodbye!")
            break


if __name__ == "__main__":
    asyncio.run(main())