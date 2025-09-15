#!/usr/bin/env python3
"""
Example: Streaming chat completions in CLI applications

This example demonstrates how to use the Tela client for streaming
responses in command-line interfaces with various display options.
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

from tela import Tela, AsyncTela
from tela._streaming_utils import StreamingDisplay, stream_to_cli, create_cli_stream_handler


def basic_streaming_example():
    """Basic streaming example with simple output"""
    print("=== Basic Streaming Example ===")
    
    client = Tela(
        api_key=os.getenv("TELAOS_API_KEY"),
        organization=os.getenv("TELAOS_ORG_ID"),  
        project=os.getenv("TELAOS_PROJECT_ID")
    )
    
    messages = [
        {"role": "user", "content": "Write a short poem about streaming data"}
    ]
    
    print("User: Write a short poem about streaming data")
    print("Assistant: ", end="", flush=True)
    
    # Simple streaming with print_stream method
    stream = client.chat.completions.create(
        messages=messages,
        stream=True,
        temperature=0.5
    )
    
    response = stream.print_stream()
    print(f"\n[Complete response length: {len(response)} characters]")


def enhanced_streaming_example():
    """Enhanced streaming with callbacks and display utilities"""
    print("\n=== Enhanced Streaming Example ===")
    
    client = Tela(
        api_key=os.getenv("TELAOS_API_KEY"),
        organization=os.getenv("TELAOS_ORG_ID"),
        project=os.getenv("TELAOS_PROJECT_ID")
    )
    
    messages = [
        {"role": "user", "content": "Explain how streaming works in real-time applications"}
    ]
    
    print("User: Explain how streaming works in real-time applications")
    print("Assistant: ", end="", flush=True)
    
    # Track streaming metrics
    chunk_count = 0
    total_content = ""
    
    def on_chunk(chunk):
        nonlocal chunk_count
        chunk_count += 1
    
    def on_content(content):
        nonlocal total_content
        total_content += content
        print(content, end="", flush=True)
    
    def on_complete(full_content):
        print(f"\n[Streaming complete: {chunk_count} chunks, {len(full_content)} characters]")
    
    # Create stream with callbacks
    stream = client.chat.completions.create(
        messages=messages,
        stream=True,
        temperature=0.5
    )
    
    # Configure stream with callbacks
    stream.on_chunk = on_chunk
    stream.on_content = on_content
    stream.on_complete = on_complete
    
    # Consume the stream
    chunks = list(stream)


def streaming_display_example():
    """Example using StreamingDisplay utility"""
    print("\n=== Streaming Display Example ===")
    
    client = Tela(
        api_key=os.getenv("TELAOS_API_KEY"),
        organization=os.getenv("TELAOS_ORG_ID"),
        project=os.getenv("TELAOS_PROJECT_ID")
    )
    
    messages = [
        {"role": "user", "content": "Create a step-by-step guide for implementing streaming"}
    ]
    
    print("User: Create a step-by-step guide for implementing streaming")
    print("Assistant: ")
    
    # Use StreamingDisplay utility
    display = StreamingDisplay(output_type="cli")
    
    stream = client.chat.completions.create(
        messages=messages,
        stream=True,
        temperature=0.5
    )
    
    for chunk in stream:
        if hasattr(chunk, 'choices') and chunk.choices:
            choice = chunk.choices[0]
            if hasattr(choice, 'delta') and choice.delta and choice.delta.content:
                display.update_content(choice.delta.content)
    
    final_content = display.finalize()
    print(f"[Final content length: {len(final_content)} characters]")


async def async_streaming_example():
    """Async streaming example"""
    print("\n=== Async Streaming Example ===")
    
    client = AsyncTela(
        api_key=os.getenv("TELAOS_API_KEY"),
        organization=os.getenv("TELAOS_ORG_ID"),
        project=os.getenv("TELAOS_PROJECT_ID")
    )
    
    messages = [
        {"role": "user", "content": "What are the benefits of async streaming?"}
    ]
    
    print("User: What are the benefits of async streaming?")
    print("Assistant: ", end="", flush=True)
    
    # Async streaming with callbacks
    chunk_count = 0
    
    def on_content(content):
        nonlocal chunk_count
        chunk_count += 1
        print(content, end="", flush=True)
    
    stream = await client.chat.completions.create(
        messages=messages,
        stream=True,
        temperature=0.5
    )
    
    # Configure callbacks
    stream.on_content = on_content
    
    # Consume async stream
    content, chunks = await stream.collect()
    print(f"\n[Async streaming complete: {len(chunks)} chunks]")
    
    await client.close()


def conversation_streaming_example():
    """Example with conversation history and streaming"""
    print("\n=== Conversation Streaming Example ===")
    
    client = Tela(
        api_key=os.getenv("TELAOS_API_KEY"),
        organization=os.getenv("TELAOS_ORG_ID"),
        project=os.getenv("TELAOS_PROJECT_ID"),
        enable_history=True
    )
    
    # Create a conversation
    conversation = client.create_conversation("streaming-demo")
    
    questions = [
        "What is streaming?",
        "How does it differ from batch processing?",
        "Can you give me a practical example?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n--- Question {i} ---")
        print(f"User: {question}")
        print("Assistant: ", end="", flush=True)
        
        messages = conversation.get_messages() + [
            {"role": "user", "content": question}
        ]
        
        stream = client.chat.completions.create(
            messages=messages,
            conversation_id=conversation.id,
            stream=True,
            temperature=0.5
        )
        
        response = stream.print_stream()
        
        # Add messages to conversation history
        conversation.add_message("user", question)
        conversation.add_message("assistant", response)
    
    print(f"\n[Conversation has {conversation.message_count} messages]")


def interactive_streaming_demo():
    """Interactive streaming demo with user input"""
    print("\n=== Interactive Streaming Demo ===")
    print("Type your questions (or 'quit' to exit)")
    
    client = Tela(
        api_key=os.getenv("TELAOS_API_KEY"),
        organization=os.getenv("TELAOS_ORG_ID"),
        project=os.getenv("TELAOS_PROJECT_ID"),
        enable_history=True
    )
    
    conversation = client.create_conversation("interactive-demo")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ('quit', 'exit', 'q'):
                break
            
            if not user_input:
                continue
            
            print("Assistant: ", end="", flush=True)
            
            messages = conversation.get_messages() + [
                {"role": "user", "content": user_input}
            ]
            
            stream = client.chat.completions.create(
                messages=messages,
                conversation_id=conversation.id,
                stream=True,
                temperature=0.5
            )
            
            response = stream.print_stream()
            
            # Update conversation
            conversation.add_message("user", user_input)
            conversation.add_message("assistant", response)
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")
    
    print(f"\nSession complete. Total messages: {conversation.message_count}")


def main():
    """Run all streaming examples"""
    print("Tela Streaming Examples for CLI Applications")
    print("=" * 50)
    
    # Check for API credentials
    if not all([
        os.getenv("TELAOS_API_KEY"),
        os.getenv("TELAOS_ORG_ID"), 
        os.getenv("TELAOS_PROJECT_ID")
    ]):
        print("Warning: Set TELAOS_API_KEY, TELAOS_ORG_ID, and TELAOS_PROJECT_ID environment variables")
        print("Using placeholder values - requests will fail")
        print()
    
    try:
        # Run sync examples
        basic_streaming_example()
        enhanced_streaming_example() 
        streaming_display_example()
        conversation_streaming_example()
        
        # Run async example
        asyncio.run(async_streaming_example())
        
        # Interactive demo (uncomment to enable)
        # interactive_streaming_demo()
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure your API credentials are set correctly")


if __name__ == "__main__":
    main()