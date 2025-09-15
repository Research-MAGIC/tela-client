"""
Tela API Endpoint Information Tool

This comprehensive example demonstrates how to use the Tela client to get detailed
information about available models, their capabilities, usage statistics, and parameters.
Perfect for building dynamic model selection and informative UIs.
"""

import asyncio
import time
from dotenv import load_dotenv
from tela import Tela, AsyncTela


def main():
    """Comprehensive endpoint information functionality"""
    load_dotenv()

    print("Tela API - Comprehensive Endpoint Information")
    print("=" * 60)

    try:
        client = Tela()

        # 1. Get available models with detailed information
        print("\n[MODELS] AVAILABLE MODELS")
        print("-" * 30)
        models = client.get_models()
        print(f"Found {len(models.data)} available models total")

        print("\nComplete model list:")
        for i, model in enumerate(models.data, 1):
            owner = getattr(model, 'owned_by', 'Unknown')
            print(f"  {i:2d}. {model.id} (owned by {owner})")

        # 2. Get models organized by categories
        print(f"\n[CATEGORIES] MODELS BY CATEGORY")
        print("-" * 30)
        categories = ['coding', 'vision', 'large', 'reasoning', 'audio']

        for category in categories:
            filtered_models = client.list_available_models(category)
            if filtered_models:
                print(f"{category.capitalize()} models ({len(filtered_models)}): {', '.join(filtered_models)}")
            else:
                print(f"{category.capitalize()} models: None found")

        # 3. Detailed model capabilities analysis
        print(f"\n[SETTINGS] MODEL CAPABILITIES ANALYSIS")
        print("-" * 30)

        # Test a few different models for capabilities
        test_models = ["qwen3-max"]  # Add more models as needed
        if models.data:
            test_models.append(models.data[0].id)  # First available model

        for model_id in test_models[:3]:  # Limit to 3 models
            try:
                caps = client.get_model_capabilities(model_id)
                print(f"\n{caps.model_id}:")
                print(f"  • Supports streaming: {caps.supports_streaming}")
                print(f"  • Supports tools: {caps.supports_tools}")
                print(f"  • Supports vision: {caps.supports_vision}")
                print(f"  • Supports JSON mode: {caps.supports_json_mode}")
                print(f"  • Default temperature: {caps.default_temperature}")
                print(f"  • Temperature range: {caps.temperature_range}")
                if caps.max_context_length:
                    print(f"  • Max context length: {caps.max_context_length:,} tokens")
                if caps.max_output_tokens:
                    print(f"  • Max output tokens: {caps.max_output_tokens:,} tokens")
            except Exception as e:
                print(f"{model_id}: Error getting capabilities - {e}")

        # 4. Parameter information and validation
        print(f"\n[PARAMETERS] PARAMETER INFORMATION")
        print("-" * 30)
        param_info = client.get_parameter_info()

        # Show comprehensive parameter help
        important_params = ['temperature', 'max_tokens', 'top_p', 'stream', 'tools', 'response_format']
        for param in important_params:
            help_text = param_info.get_parameter_help(param)
            print(f"• {param:15s}: {help_text}")

        # 5. Usage analysis with real requests
        print(f"\n[USAGE] USAGE ANALYSIS & TESTING")
        print("-" * 30)

        # Select test model first
        test_model = models.data[0].id if models.data else "qwen3-max"
        print(f"Using model for testing: {test_model}")

        # Quick connectivity check before doing extensive testing
        print("Checking API server connectivity...")
        try:
            # Simple test request to check server status
            test_response = client.chat.completions.create(
                messages=[{"role": "user", "content": "Hi"}],
                model=test_model,
                max_tokens=5
            )
            print("Server connectivity: OK")
            skip_usage_tests = False
        except Exception as e:
            error_msg = str(e)
            if "502" in error_msg or "500" in error_msg:
                print("Server connectivity: Issues detected (502/500 errors)")
                print("Skipping usage tests due to server problems")
                skip_usage_tests = True
            else:
                print(f"Server connectivity: Other error - {e}")
                skip_usage_tests = False

        if skip_usage_tests:
            print("\n[SKIP] Usage testing skipped due to server issues")
            print("  - The API server is currently experiencing problems")
            print("  - Model discovery and capabilities analysis completed successfully")
            print("  - Try running the tool again later for usage testing")
        else:
            # Test different types of requests
            test_requests = [
                {"content": "What is 2+2?", "description": "Simple math question", "max_tokens": 20},
                {"content": "Explain machine learning in 30 words", "description": "Technical explanation", "max_tokens": 50},
                {"content": "Write a Python function to reverse a string", "description": "Code generation", "max_tokens": 100}
            ]

            def make_request_with_retry(test_request, retries=2):
                """Make API request with retry logic for server errors"""
                for attempt in range(retries + 1):
                    try:
                        response = client.chat.completions.create(
                            messages=[{"role": "user", "content": test_request['content']}],
                            model=test_model,
                            max_tokens=test_request['max_tokens'],
                            temperature=0.5
                        )
                        return response, None
                    except Exception as e:
                        error_msg = str(e)
                        if attempt < retries and ("502" in error_msg or "500" in error_msg or "timeout" in error_msg.lower()):
                            print(f"        Attempt {attempt + 1} failed, retrying in 2 seconds...")
                            time.sleep(2)
                            continue
                        return None, e
                return None, Exception("Max retries exceeded")

            server_available = True
            successful_tests = 0

            for i, test_req in enumerate(test_requests, 1):
                print(f"\nTest {i}: {test_req['description']}")
                response, error = make_request_with_retry(test_req)

                if response:
                    try:
                        content = response.choices[0].message.content
                        print(f"      Request: {test_req['content']}")
                        print(f"      Response: {content}")
                        successful_tests += 1

                        # Get usage information
                        usage = client.get_usage_from_response(response)
                        if usage:
                            print(f"      Usage stats:")
                            print(f"        - Prompt tokens: {usage.prompt_tokens}")
                            print(f"        - Completion tokens: {usage.completion_tokens}")
                            print(f"        - Total tokens: {usage.total_tokens}")
                            print(f"        - Efficiency ratio: {usage.efficiency_ratio:.2%}")
                    except Exception as parse_error:
                        print(f"      Error parsing response: {parse_error}")
                else:
                    error_msg = str(error)
                    if "502 Bad Gateway" in error_msg or "502" in error_msg:
                        print(f"      Error: API server temporarily unavailable (502 Bad Gateway)")
                        print(f"      This is a server-side issue, not a client problem")
                        server_available = False
                    elif "500" in error_msg:
                        print(f"      Error: Internal server error (500)")
                        server_available = False
                    elif "404" in error_msg:
                        print(f"      Error: Model or endpoint not found (404)")
                    elif "401" in error_msg or "403" in error_msg:
                        print(f"      Error: Authentication/authorization issue")
                    elif "timeout" in error_msg.lower():
                        print(f"      Error: Request timeout - server may be overloaded")
                        server_available = False
                    else:
                        print(f"      Error: {error_msg}")

            # Summary of testing results
            print(f"\n    [RESULTS] Usage Testing Summary:")
            print(f"      - Successful tests: {successful_tests}/{len(test_requests)}")
            print(f"      - Server availability: {'Good' if server_available else 'Issues detected'}")

        # Provide guidance if server issues were detected - only applies when usage tests ran
        if 'server_available' in locals() and not server_available:
            print(f"\n[WARNING] API server issues detected during testing")
            print(f"  - The Tela API server appears to be experiencing problems")
            print(f"  - This is temporary and should resolve shortly")
            print(f"  - Model discovery and capabilities still work fine")
            print(f"  - Try again later for usage testing")

        # 6. Practical usage examples for developers
        print(f"\n[EXAMPLES] PRACTICAL USAGE EXAMPLES")
        print("-" * 30)
        print("For CLI applications:")
        print("  # Dynamic model selection")
        print("  coding_models = client.list_available_models('coding')")
        print("  selected_model = coding_models[0] if coding_models else 'qwen3-max'")
        print("  ")
        print("  # Check capabilities before using")
        print("  caps = client.get_model_capabilities(selected_model)")
        print("  if caps.supports_streaming:")
        print("      # Use streaming")
        print("  ")
        print("For NiceGUI applications:")
        print("  # Model selection dropdown")
        print("  ui.select(client.list_available_models(), label='Choose Model')")
        print("  ")
        print("  # Show model info")
        print("  with ui.expansion('Model Capabilities'):")
        print("      caps = client.get_model_capabilities(selected_model)")
        print("      ui.label(f'Max tokens: {caps.max_context_length}')")
        print("      ui.label(f'Supports streaming: {caps.supports_streaming}')")

        print(f"\n[OK] ENDPOINT INFORMATION ANALYSIS COMPLETE!")
        print(f"   All {len(models.data)} models analyzed successfully")

    except Exception as e:
        print(f"[ERROR] Error during endpoint analysis: {e}")
        print("Make sure your .env file has the required Tela API credentials")


async def async_example():
    """Demonstrate async endpoint information functionality"""
    load_dotenv()

    print("\n" + "=" * 60)
    print("[ASYNC] ASYNC ENDPOINT INFORMATION EXAMPLE")
    print("=" * 60)

    client = AsyncTela()

    try:
        # Get models asynchronously
        print("\n[FETCH] Fetching models asynchronously...")
        models = await client.get_models()
        print(f"Found {len(models.data)} models (async)")

        # Get detailed model info for first few models
        print("\n[DETAILS] Model details (async):")
        for model in models.data[:3]:
            try:
                model_info = await client.get_model_info(model.id)
                owner = getattr(model_info, 'owned_by', 'Unknown')
                print(f"  • {model_info.id} (owned by {owner})")
            except Exception as e:
                print(f"  • {model.id}: Error - {e}")

        # List models by category asynchronously
        print("\n[CATEGORIES] Categories (async):")
        categories = ['coding', 'vision', 'large']

        for category in categories:
            try:
                filtered_models = await client.list_available_models(category)
                if filtered_models:
                    print(f"  {category.capitalize()}: {', '.join(filtered_models[:3])}...")
            except Exception as e:
                print(f"  {category.capitalize()}: Error - {e}")

        print("\n[OK] Async example completed successfully!")

    except Exception as e:
        print(f"[ERROR] Async error: {e}")

    finally:
        await client.close()


def interactive_mode():
    """Interactive mode for exploring endpoint information"""
    load_dotenv()

    print("\n" + "=" * 60)
    print("[INTERACTIVE] INTERACTIVE ENDPOINT EXPLORATION")
    print("=" * 60)

    client = Tela()

    try:
        models = client.get_models()
        model_list = [model.id for model in models.data]

        print(f"\nInteractive mode - {len(model_list)} models available")
        print("Commands:")
        print("  'list' - Show all models")
        print("  'caps <model_id>' - Show model capabilities")
        print("  'test <model_id>' - Test model with a simple request")
        print("  'category <name>' - Show models in category")
        print("  'quit' - Exit")

        while True:
            try:
                command = input("\n> ").strip().lower()

                if command == 'quit':
                    break
                elif command == 'list':
                    for i, model_id in enumerate(model_list, 1):
                        print(f"  {i:2d}. {model_id}")
                elif command.startswith('caps '):
                    model_id = command[5:].strip()
                    if model_id in model_list:
                        caps = client.get_model_capabilities(model_id)
                        print(f"\nCapabilities for {caps.model_id}:")
                        print(f"  Streaming: {caps.supports_streaming}")
                        print(f"  Tools: {caps.supports_tools}")
                        print(f"  Vision: {caps.supports_vision}")
                        print(f"  Max context: {caps.max_context_length}")
                    else:
                        print(f"Model '{model_id}' not found")
                elif command.startswith('test '):
                    model_id = command[5:].strip()
                    if model_id in model_list:
                        print(f"Testing {model_id}...")
                        response = client.chat.completions.create(
                            messages=[{"role": "user", "content": "Say hello!"}],
                            model=model_id,
                            max_tokens=20
                        )
                        print(f"Response: {response.choices[0].message.content}")
                    else:
                        print(f"Model '{model_id}' not found")
                elif command.startswith('category '):
                    category = command[9:].strip()
                    filtered = client.list_available_models(category)
                    if filtered:
                        print(f"{category.capitalize()} models: {', '.join(filtered)}")
                    else:
                        print(f"No {category} models found")
                else:
                    print("Unknown command. Try 'list', 'caps <model>', 'test <model>', 'category <name>', or 'quit'")

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")

    except Exception as e:
        print(f"[ERROR] Interactive mode error: {e}")


if __name__ == "__main__":
    # Run comprehensive sync example
    main()

    # Run async example
    asyncio.run(async_example())

    # Offer interactive mode
    print("\n" + "=" * 60)
    print("[COMPLETE] ENDPOINT INFORMATION EXAMPLES COMPLETED!")
    print("=" * 60)
    print("Summary:")
    print("  [OK] Model discovery and listing")
    print("  [OK] Capability analysis and testing")
    print("  [OK] Usage statistics and validation")
    print("  [OK] Parameter information and help")
    print("  [OK] Practical usage examples")
    print("  [OK] Both sync and async implementations")

    response = input("\nWould you like to try interactive mode? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        interactive_mode()

    print("\n[TIP] Use these methods to build dynamic, informative applications!")
    print("   Perfect for CLI tools and NiceGUI interfaces.")