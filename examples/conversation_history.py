#!/usr/bin/env python3
"""
Example: Conversation history management with Tela client

This example demonstrates how to properly manage conversation history
and send messages with context aggregation using 2025 best practices.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from tela import Tela, AsyncTela
import asyncio

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def basic_conversation_example():
    """Basic conversation with automatic history tracking"""
    print("=" * 60)
    print("BASIC CONVERSATION WITH HISTORY")
    print("=" * 60)
    
    client = Tela(
        api_key=os.getenv("TELAOS_API_KEY"),
        organization=os.getenv("TELAOS_ORG_ID"),
        project=os.getenv("TELAOS_PROJECT_ID"),
        enable_history=True
    )
    
    print("\n[OK] Creating a new conversation...")
    
    try:
        # Method 1: Using send_message (recommended)
        response1 = client.send_message("What is the capital of France?")
        print(f"Q: What is the capital of France?")
        print(f"A: {response1}")
        
        # Follow-up question with context
        response2 = client.send_message(
            "What's the population of that city?",
            conversation_id="demo-conversation"
        )
        print(f"Q: What's the population of that city?")
        print(f"A: {response2}")
        
        # Another follow-up
        response3 = client.send_message(
            "What are some famous landmarks there?",
            conversation_id="demo-conversation"
        )
        print(f"Q: What are some famous landmarks there?")
        print(f"A: {response3}")
        
    except Exception as e:
        print(f"Configure API credentials to see actual conversation")
        print("Example flow:")
        print("Q: What is the capital of France?")
        print("A: The capital of France is Paris.")
        print("Q: What's the population of that city?") 
        print("A: Paris has a population of about 2.2 million people...")
        print("Q: What are some famous landmarks there?")
        print("A: Paris has many famous landmarks including the Eiffel Tower...")


def conversation_context_management():
    """Demonstrate conversation context management"""
    print("\n" + "=" * 60)
    print("CONVERSATION CONTEXT MANAGEMENT")
    print("=" * 60)
    
    client = Tela(
        api_key=os.getenv("TELAOS_API_KEY"),
        organization=os.getenv("TELAOS_ORG_ID"),
        project=os.getenv("TELAOS_PROJECT_ID"),
        enable_history=True
    )
    
    print("\n[CONTEXT] Building conversation context...")
    
    # Create a conversation with specific ID
    conversation_id = f"context-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    conv = client.create_conversation(conversation_id)
    
    # Simulate a longer conversation
    exchanges = [
        ("My name is John Smith", "Nice to meet you, John! How can I help you today?"),
        ("I'm 25 years old", "Thank you for sharing that information, John."),
        ("I live in New York", "New York is a great city! Are you looking for something specific?"),
        ("I need help with Python programming", "I'd be happy to help you with Python programming, John!"),
        ("How do I create a list?", "In Python, you create a list using square brackets: my_list = [1, 2, 3]"),
    ]
    
    print(f"Adding {len(exchanges)} message pairs to conversation...")
    for user_msg, assistant_msg in exchanges:
        conv.add_message("user", user_msg)
        conv.add_message("assistant", assistant_msg)
    
    print(f"[OK] Conversation has {conv.message_count} messages")
    
    # Get conversation context
    print("\n[CONTEXT] Getting conversation context...")
    
    # Get all context
    full_context = client.get_conversation_context(conversation_id=conversation_id)
    print(f"Full context: {len(full_context)} messages")
    
    # Get limited context (last 4 messages)
    limited_context = client.get_conversation_context(
        conversation_id=conversation_id,
        max_messages=4
    )
    print(f"Limited context: {len(limited_context)} messages")
    
    print("\nMessages in limited context:")
    for i, msg in enumerate(limited_context, 1):
        role = msg['role'].capitalize()
        content = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
        print(f"  {i}. {role}: {content}")
    
    # Continue conversation with context
    print("\n[CHAT] Continuing conversation with context...")
    try:
        response = client.send_message(
            "Can you remind me what we discussed about lists?",
            conversation_id=conversation_id,
            max_history=6  # Include last 6 messages as context
        )
        print(f"Q: Can you remind me what we discussed about lists?")
        print(f"A: {response}")
    except:
        print("Would continue with proper context including previous list discussion")


def export_conversation_history():
    """Demonstrate exporting conversation in different formats"""
    print("\n" + "=" * 60)
    print("CONVERSATION EXPORT")
    print("=" * 60)
    
    client = Tela(
        api_key=os.getenv("TELAOS_API_KEY"),
        organization=os.getenv("TELAOS_ORG_ID"),
        project=os.getenv("TELAOS_PROJECT_ID"),
        enable_history=True
    )
    
    # Create sample conversation
    conversation_id = "export-demo"
    conv = client.create_conversation(conversation_id)
    
    sample_messages = [
        ("user", "Hello, I need help with my account"),
        ("assistant", "I'd be happy to help with your account. What specific issue are you experiencing?"),
        ("user", "I can't log in. It says my password is incorrect"),
        ("assistant", "I can help you reset your password. What's the email address associated with your account?"),
        ("user", "user@example.com"),
        ("assistant", "I've sent a password reset link to user@example.com. Please check your email and follow the instructions."),
    ]
    
    for role, content in sample_messages:
        conv.add_message(role, content)
    
    print(f"[OK] Created sample conversation with {conv.message_count} messages")
    
    # Export in different formats
    formats = ["text", "json", "markdown", "messages"]
    
    for format_type in formats:
        print(f"\n[EXPORT] Export format: {format_type}")
        print("-" * 40)
        
        try:
            exported = client.export_conversation(conversation_id, format=format_type)
            
            if format_type == "json":
                print("JSON structure with metadata and message history")
                if isinstance(exported, dict):
                    print(f"  - ID: {exported.get('id', 'N/A')}")
                    print(f"  - Messages: {exported.get('message_count', 'N/A')}")
                    print(f"  - Created: {exported.get('created_at', 'N/A')}")
            elif format_type == "messages":
                print("Raw messages for model context:")
                if isinstance(exported, list):
                    for i, msg in enumerate(exported[:2], 1):  # Show first 2
                        print(f"  {i}. {msg['role']}: {msg['content'][:50]}...")
                    if len(exported) > 2:
                        print(f"  ... and {len(exported) - 2} more messages")
            else:
                # Text or markdown
                content_preview = str(exported)[:200] + "..." if len(str(exported)) > 200 else str(exported)
                print(content_preview)
                
        except Exception as e:
            print(f"Export format '{format_type}' example structure shown above")


async def async_conversation_example():
    """Demonstrate async conversation handling"""
    print("\n" + "=" * 60)
    print("ASYNC CONVERSATION EXAMPLE")
    print("=" * 60)
    
    client = AsyncTela(
        api_key=os.getenv("TELAOS_API_KEY"),
        organization=os.getenv("TELAOS_ORG_ID"),
        project=os.getenv("TELAOS_PROJECT_ID"),
        enable_history=True
    )
    
    conversation_id = "async-demo"
    
    try:
        print("[ASYNC] Sending async messages...")
        
        # Send multiple messages in sequence with history
        response1 = await client.send_message(
            "What is machine learning?",
            conversation_id=conversation_id
        )
        print("Q: What is machine learning?")
        print(f"A: {response1[:300]}...")
        
        response2 = await client.send_message(
            "Can you give me a simple example?",
            conversation_id=conversation_id
        )
        print("Q: Can you give me a simple example?")
        print(f"A: {response2[:300]}...")
        
        # Get conversation stats
        conv = await client.get_conversation(conversation_id)
        if conv:
            print(f"\n[OK] Conversation has {conv.message_count} messages")
        
    except Exception as e:
        print("Configure API to see async conversation flow")
        print("Would maintain full conversation context across async calls")
    
    finally:
        await client.close()


def streaming_with_history():
    """Demonstrate streaming responses with history tracking"""
    print("\n" + "=" * 60)
    print("STREAMING WITH HISTORY")
    print("=" * 60)
    
    client = Tela(
        api_key=os.getenv("TELAOS_API_KEY"),
        organization=os.getenv("TELAOS_ORG_ID"),
        project=os.getenv("TELAOS_PROJECT_ID"),
        enable_history=True
    )
    
    conversation_id = "streaming-demo"
    conv = client.create_conversation(conversation_id)
    
    # Add some context
    conv.add_message("user", "I'm learning about Python")
    conv.add_message("assistant", "That's great! Python is a wonderful language to learn.")
    
    print("[STREAM] Sending message with streaming response...")
    
    try:
        # Get context and send streaming request
        context_messages = client.get_conversation_context(conversation_id=conversation_id)
        context_messages.append({"role": "user", "content": "Can you explain loops in Python?"})
        
        stream = client.chat.completions.create(
            messages=context_messages,
            conversation_id=conversation_id,
            stream=True,
            temperature=0.5
        )
        
        print("Q: Can you explain loops in Python?")
        print("A: ", end="", flush=True)
        
        # Stream the response
        full_response = stream.print_stream()
        
        # Add to history
        conv.add_message("user", "Can you explain loops in Python?")
        conv.add_message("assistant", full_response)
        
        print(f"\n[OK] Conversation now has {conv.message_count} messages")
        
    except Exception as e:
        print("Configure API to see streaming with history")


def save_and_view_conversation_json():
    """Demonstrate saving and viewing conversation history as JSON files"""
    print("\n" + "=" * 60)
    print("SAVE & VIEW CONVERSATION JSON FILES")
    print("=" * 60)

    client = Tela(
        api_key=os.getenv("TELAOS_API_KEY"),
        organization=os.getenv("TELAOS_ORG_ID"),
        project=os.getenv("TELAOS_PROJECT_ID"),
        enable_history=True
    )

    # Create a comprehensive conversation example
    conversation_id = f"json-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    conv = client.create_conversation(conversation_id)

    print(f"[CREATE] Creating conversation: {conversation_id}")

    # Add system prompt
    conv.add_message("system", "You are a helpful AI assistant that specializes in Python programming. Always provide clear, practical examples with your explanations.")

    # Sample conversation with various message types
    sample_conversation = [
        ("user", "Hello! I'm new to Python and need help getting started."),
        ("assistant", "Hello! Welcome to Python programming! I'd be happy to help you get started. Python is a beginner-friendly language that's great for learning programming concepts. What specific area would you like to begin with - basic syntax, data types, or something else?"),
        ("user", "Can you show me how to create and use variables?"),
        ("assistant", "Absolutely! Variables in Python are simple to create and use. Here are some examples:\n\n```python\n# Creating variables\nname = \"Alice\"\nage = 25\nheight = 5.6\nis_student = True\n\n# Using variables\nprint(f\"Hello, {name}!\")\nprint(f\"You are {age} years old\")\nprint(f\"Height: {height} feet\")\nprint(f\"Student status: {is_student}\")\n```\n\nPython automatically determines the variable type based on the value you assign!"),
        ("user", "That's helpful! How about lists? Can you show me some list operations?"),
        ("assistant", "Great question! Lists are one of Python's most useful data structures. Here are key operations:\n\n```python\n# Creating lists\nfruits = ['apple', 'banana', 'orange']\nnumbers = [1, 2, 3, 4, 5]\n\n# Adding items\nfruits.append('grape')  # Add to end\nfruits.insert(1, 'kiwi')  # Insert at position 1\n\n# Accessing items\nfirst_fruit = fruits[0]  # 'apple'\nlast_fruit = fruits[-1]  # Last item\n\n# List operations\nprint(len(fruits))  # Length\nprint('apple' in fruits)  # Check if item exists\n```\n\nLists are mutable, meaning you can change them after creation!")
    ]

    # Add all messages to conversation
    for role, content in sample_conversation:
        conv.add_message(role, content)

    print(f"[OK] Added {len(sample_conversation)} message exchanges")
    print(f"[STATS] Total messages in conversation: {conv.message_count}")

    # Create conversations directory if it doesn't exist
    conversations_dir = Path("conversations")
    conversations_dir.mkdir(exist_ok=True)

    try:
        # Export conversation as JSON
        json_data = client.export_conversation(conversation_id, format="json")

        # Enhanced JSON structure with metadata
        enhanced_json = {
            "conversation_id": conversation_id,
            "created_at": datetime.now().isoformat(),
            "total_messages": conv.message_count,
            "export_timestamp": datetime.now().isoformat(),
            "format_version": "1.0",
            "conversation_data": json_data if isinstance(json_data, dict) else {
                "messages": json_data if isinstance(json_data, list) else []
            }
        }

        # Save to file
        json_filename = conversations_dir / f"{conversation_id}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(enhanced_json, f, indent=2, ensure_ascii=False)

        print(f"\n[SAVED] Saved conversation to: {json_filename}")
        print(f"[SIZE] File size: {json_filename.stat().st_size:,} bytes")

        # Display JSON structure
        print(f"\n[JSON] JSON Structure Preview:")
        print(f"  - conversation_id: {enhanced_json['conversation_id']}")
        print(f"  - total_messages: {enhanced_json['total_messages']}")
        print(f"  - created_at: {enhanced_json['created_at']}")
        print(f"  - format_version: {enhanced_json['format_version']}")

        # Show sample messages
        messages = enhanced_json.get('conversation_data', {}).get('messages', [])
        if isinstance(messages, list) and messages:
            print(f"\n[MESSAGES] Sample Messages (first 3):")
            for i, msg in enumerate(messages[:3], 1):
                role = msg.get('role', 'unknown').capitalize()
                content = msg.get('content', '')[:80] + "..." if len(msg.get('content', '')) > 80 else msg.get('content', '')
                print(f"  {i}. {role}: {content}")

            if len(messages) > 3:
                print(f"  ... and {len(messages) - 3} more messages")

        # Offer to display full JSON
        print(f"\n[VIEW] View Options:")
        print(f"  1. View full JSON content")
        print(f"  2. View messages only")
        print(f"  3. View conversation summary")

        # Interactive viewing (simplified for demo)
        print(f"\n[CONTENT] Full JSON Content (first 500 chars):")
        json_str = json.dumps(enhanced_json, indent=2)
        print(json_str[:500] + "..." if len(json_str) > 500 else json_str)

        # Additional export formats
        print(f"\n[EXPORT] Additional Export Options:")

        # Save as messages-only JSON (for model consumption)
        messages_filename = conversations_dir / f"{conversation_id}_messages.json"
        messages_only = client.export_conversation(conversation_id, format="messages")
        with open(messages_filename, 'w', encoding='utf-8') as f:
            json.dump(messages_only, f, indent=2, ensure_ascii=False)
        print(f"  [JSON] Messages-only JSON: {messages_filename}")

        # Save as readable text
        text_filename = conversations_dir / f"{conversation_id}.txt"
        text_export = client.export_conversation(conversation_id, format="text")
        with open(text_filename, 'w', encoding='utf-8') as f:
            f.write(f"Conversation: {conversation_id}\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Messages: {conv.message_count}\n")
            f.write("=" * 50 + "\n\n")
            f.write(str(text_export))
        print(f"  [TXT] Readable text: {text_filename}")

        # Save as markdown
        md_filename = conversations_dir / f"{conversation_id}.md"
        md_export = client.export_conversation(conversation_id, format="markdown")
        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(f"# Conversation: {conversation_id}\n\n")
            f.write(f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
            f.write(f"**Total Messages:** {conv.message_count}  \n\n")
            f.write("---\n\n")
            f.write(str(md_export))
        print(f"  [MD] Markdown: {md_filename}")

        print(f"\n[SUCCESS] All conversation files saved to '{conversations_dir}' directory")

        # Show how to load and use the JSON
        print(f"\n[USAGE] Loading Saved Conversation:")
        print(f"```python")
        print(f"import json")
        print(f"")
        print(f"# Load conversation")
        print(f"with open('{json_filename}', 'r') as f:")
        print(f"    conversation = json.load(f)")
        print(f"")
        print(f"# Access messages")
        print(f"messages = conversation['conversation_data']['messages']")
        print(f"print(f'Loaded {{len(messages)}} messages')")
        print(f"")
        print(f"# Use in API call")
        print(f"response = client.chat.completions.create(")
        print(f"    messages=messages,")
        print(f"    model='your-model'")
        print(f")")
        print(f"```")

    except Exception as e:
        print(f"[DEMO] Demo of JSON conversation export (API not configured)")
        print(f"Would create:")
        print(f"  - conversations/{conversation_id}.json (full conversation)")
        print(f"  - conversations/{conversation_id}_messages.json (messages only)")
        print(f"  - conversations/{conversation_id}.txt (readable text)")
        print(f"  - conversations/{conversation_id}.md (markdown format)")


def conversation_best_practices():
    """Demonstrate best practices for conversation handling"""
    print("\n" + "=" * 60)
    print("CONVERSATION BEST PRACTICES")
    print("=" * 60)
    
    client = Tela(
        api_key=os.getenv("TELAOS_API_KEY"),
        organization=os.getenv("TELAOS_ORG_ID"),
        project=os.getenv("TELAOS_PROJECT_ID"),
        enable_history=True
    )
    
    print("""
[DO] DO:
- Use client.send_message() for simple conversations
- Use conversation_id to maintain context across calls
- Set max_history to limit context size for long conversations
- Use get_conversation_context() to inspect what will be sent
- Export conversations for analysis or backup
- Use proper role attribution (user/assistant/system)

[DON'T] DON'T:
- Send assistant messages as user input
- Ignore conversation history limits
- Mix different conversation contexts
- Forget to handle conversation creation errors

[EXAMPLES] Best Practice Examples:
    """)
    
    # Example 1: Proper message sending
    print("1. Proper message sending with context limit:")
    print("""
    response = client.send_message(
        message="Your question here",
        conversation_id="my-conversation",
        max_history=10  # Include last 10 messages as context
    )
    """)
    
    # Example 2: Context inspection
    print("2. Inspecting context before sending:")
    print("""
    context = client.get_conversation_context(
        conversation_id="my-conversation",
        max_messages=5
    )
    print(f"Will send {len(context)} messages as context")
    """)
    
    # Example 3: Proper export
    print("3. Exporting for model consumption:")
    print("""
    # For sending to another model
    messages = client.export_conversation("my-conversation", format="messages")
    
    # For human reading
    text = client.export_conversation("my-conversation", format="markdown")
    """)


def main():
    """Run all conversation examples"""
    print("[START] " + "=" * 48 + " [START]")
    print("  TELA CLIENT CONVERSATION HISTORY EXAMPLES")
    print("[START] " + "=" * 48 + " [START]")
    
    print("""
This example demonstrates proper conversation history management
with the Tela client library using best practices.

Key Features:
- Automatic history tracking
- Context aggregation
- Message role preservation
- Streaming with history
- Multiple export formats
    """)
    
    # Run examples
    basic_conversation_example()
    conversation_context_management()
    export_conversation_history()
    save_and_view_conversation_json()
    streaming_with_history()
    conversation_best_practices()
    
    # Run async example
    print("\n[ASYNC] Running async example...")
    asyncio.run(async_conversation_example())
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("""
The Tela client provides robust conversation history management:

[CORE] Core Methods:
- send_message(): Send with automatic history
- get_conversation_context(): Inspect context
- export_conversation(): Export in multiple formats

[FEATURES] Key Features:
- Automatic conversation creation
- Context size limiting
- Proper message role handling
- Streaming support with history
- Persistent storage options

[FORMATS] Export Formats:
- 'messages': For model consumption
- 'json': Full metadata structure
- 'text': Simple human-readable
- 'markdown': Formatted documentation

The library handles message aggregation properly, maintaining
conversation context while following 2025 best practices.
    """)


if __name__ == "__main__":
    main()