#!/usr/bin/env python3
"""
Simple test script for tool calling functionality
"""

import asyncio
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from tela import AsyncTela
from tool_calling_cli import ToolRegistry


async def test_basic_tool_calling():
    """Test basic tool calling without interactive input"""
    print("[TEST] Testing Basic Tool Calling Functionality")
    print("=" * 50)

    # Check environment variables
    if not all([
        os.getenv("TELAOS_API_KEY"),
        os.getenv("TELAOS_ORG_ID"),
        os.getenv("TELAOS_PROJECT_ID")
    ]):
        print("[ERROR] Missing required environment variables:")
        print("   - TELAOS_API_KEY")
        print("   - TELAOS_ORG_ID")
        print("   - TELAOS_PROJECT_ID")
        return False

    try:
        # Initialize client and tools
        client = AsyncTela(
            api_key=os.getenv("TELAOS_API_KEY"),
            organization=os.getenv("TELAOS_ORG_ID"),
            project=os.getenv("TELAOS_PROJECT_ID")
        )

        tool_registry = ToolRegistry()
        model_name = "qwen3-max"

        print(f"[OK] Client initialized with {len(tool_registry.tools)} tools")
        print(f"[OK] Available tools: {', '.join(tool_registry.tools.keys())}")
        print()

        # Test 1: Weather tool
        print("[TEST 1] Testing weather tool...")
        test_query = "What's the weather like in Tokyo?"

        messages = [{"role": "user", "content": test_query}]

        response = await client.chat.completions.create(
            messages=messages,
            model=model_name,
            tools=tool_registry.get_tool_definitions(),
            tool_choice="auto",
            temperature=0.3
        )

        choice = response.choices[0]
        assistant_message = choice.message

        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            print("[OK] Model requested tool execution")
            print(f"[DEBUG] Tool calls type: {type(assistant_message.tool_calls)}")
            print(f"[DEBUG] First tool call: {assistant_message.tool_calls[0]}")

            # Execute tools
            for tool_call in assistant_message.tool_calls:
                print(f"[DEBUG] Tool call object: {tool_call}")
                print(f"[DEBUG] Tool call type: {type(tool_call)}")

                # Handle different tool call formats
                if hasattr(tool_call, 'function'):
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                elif isinstance(tool_call, dict):
                    tool_name = tool_call['function']['name']
                    arguments = json.loads(tool_call['function']['arguments'])
                else:
                    print(f"[ERROR] Unknown tool call format: {tool_call}")
                    continue

                print(f"[EXEC] {tool_name} with args: {arguments}")

                result = await tool_registry.execute_tool(tool_name, arguments)

                if "error" in result:
                    print(f"[ERROR] Tool failed: {result['error']}")
                else:
                    print(f"[OK] Tool completed successfully")

            print("[OK] Test 1 passed - Tool calling works")
        else:
            print("[WARN] Model didn't use tools for weather query")

        print()

        # Test 2: Calculator tool
        print("[TEST 2] Testing calculator tool...")
        test_query = "Calculate 15 * 7 + 23"

        messages = [{"role": "user", "content": test_query}]

        response = await client.chat.completions.create(
            messages=messages,
            model=model_name,
            tools=tool_registry.get_tool_definitions(),
            tool_choice="auto",
            temperature=0.3
        )

        choice = response.choices[0]
        assistant_message = choice.message

        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            print("[OK] Model requested tool execution")

            for tool_call in assistant_message.tool_calls:
                # Handle dict format
                if isinstance(tool_call, dict):
                    tool_name = tool_call['function']['name']
                    arguments = json.loads(tool_call['function']['arguments'])
                else:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)

                print(f"[EXEC] {tool_name} with args: {arguments}")

                result = await tool_registry.execute_tool(tool_name, arguments)

                if "error" in result:
                    print(f"[ERROR] Tool failed: {result['error']}")
                else:
                    print(f"[OK] Tool result: {result.get('result', 'N/A')}")

            print("[OK] Test 2 passed - Calculator works")
        else:
            print("[WARN] Model didn't use tools for math query")

        print()

        # Test 3: Direct tool execution
        print("[TEST 3] Testing direct tool execution...")

        # Test weather tool directly
        weather_result = await tool_registry.execute_tool("get_weather", {"city": "Paris", "units": "metric"})
        if "error" not in weather_result:
            print("[OK] Weather tool direct execution works")
        else:
            print(f"[ERROR] Weather tool failed: {weather_result['error']}")

        # Test calculator tool directly
        calc_result = await tool_registry.execute_tool("calculate", {"expression": "2 + 2", "precision": 1})
        if "error" not in calc_result:
            print(f"[OK] Calculator tool direct execution works: {calc_result.get('result', 'N/A')}")
        else:
            print(f"[ERROR] Calculator tool failed: {calc_result['error']}")

        # Test search tool directly
        search_result = await tool_registry.execute_tool("search_docs", {"query": "API", "top_k": 3})
        if "error" not in search_result:
            print(f"[OK] Search tool direct execution works: {len(search_result.get('results', []))} results")
        else:
            print(f"[ERROR] Search tool failed: {search_result['error']}")

        # Test time tool directly
        time_result = await tool_registry.execute_tool("get_time", {"timezone": "UTC", "format": "24h"})
        if "error" not in time_result:
            print(f"[OK] Time tool direct execution works: {time_result.get('time', 'N/A')}")
        else:
            print(f"[ERROR] Time tool failed: {time_result['error']}")

        print()
        print("[SUCCESS] All tool calling tests completed successfully!")
        print("[INFO] You can now run the interactive examples:")
        print("   - CLI: python examples/tool_calling_cli.py")
        print("   - NiceGUI: python examples/tool_calling_nicegui.py")

        return True

    except Exception as e:
        print(f"[ERROR] Test failed with exception: {str(e)}")
        return False


async def main():
    """Main test function"""
    success = await test_basic_tool_calling()
    if not success:
        print("\n[FAILED] Tool calling tests failed")
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)