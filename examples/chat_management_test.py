#!/usr/bin/env python3
"""
Comprehensive Chat Management Example

Demonstrates all server-side chat management capabilities including:
- Listing server-side chats with pagination
- Creating and managing server chats
- Syncing local conversation history with server
- Graceful degradation when endpoints are unavailable
- Integrated conversation management with server sync
- Both synchronous and asynchronous operations
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tela import Tela, AsyncTela
from tela._exceptions import APIError, NotFoundError, BadRequestError


def sync_chat_management_example():
    """Example of synchronous chat management operations with graceful degradation"""
    print("=== Synchronous Chat Management Example ===\n")

    client = Tela(enable_history=True)

    try:
        # 1. List existing chats
        print("1. Listing existing chats...")
        chats = client.chats.list(page=1, page_size=10)

        if chats.total == 0 and not chats.data:
            print("   [INFO] Chat endpoints appear unavailable (graceful degradation active)")
            print(f"   [OK] Returned empty list with proper pagination structure")
            print(f"   [OK] Page: {chats.page}, Size: {chats.page_size}, Total: {chats.total}")
        else:
            print(f"   [OK] Found {len(chats.data)} chats on page {chats.page}")
            for chat in chats.data:
                print(f"   - {chat.id}: {chat.title or 'Untitled'} ({chat.message_count} messages)")
        print()

        # 2. Create a new chat
        print("2. Creating a new chat...")
        new_chat_response = client.chats.create(
            module_id="chat",
            message="Welcome to Chat Management Demo!"
        )
        chat_id = new_chat_response.get("chat_id")

        if chat_id and chat_id.startswith("local_"):
            print(f"   [INFO] Generated local fallback chat ID (server endpoint unavailable)")
            print(f"   [OK] Chat ID: {chat_id}")
        else:
            print(f"   [OK] Created server chat: {chat_id}")
        print()

        # 3. Get the created chat details
        print("3. Getting chat details...")
        try:
            chat_details = client.chats.get(chat_id)

            if hasattr(chat_details, 'metadata') and chat_details.metadata.get('local'):
                print(f"   [INFO] Returned mock chat object (graceful degradation)")
            else:
                print(f"   [OK] Retrieved server chat")

            print(f"   Chat ID: {chat_details.id}")
            print(f"   Title: {chat_details.title}")
            print(f"   Created: {chat_details.created_at}")
            print(f"   Updated: {chat_details.updated_at}")
            print(f"   Message count: {chat_details.message_count}")

            if chat_details.metadata:
                print(f"   Metadata: {chat_details.metadata}")
        except Exception as e:
            print(f"   [ERROR] Could not get chat details: {e}")
        print()

        # 4. Update chat (with graceful handling)
        print("4. Testing chat update...")
        try:
            updated = client.chats.update(
                chat_id,
                name="Updated Chat Name"
            )
            if hasattr(updated, 'metadata') and updated.metadata.get('local'):
                print(f"   [INFO] Update simulated locally (server endpoint unavailable)")
            else:
                print(f"   [OK] Chat updated on server")
            print(f"   Updated chat: {updated.id}")
            print(f"   New title: {updated.title}")
        except BadRequestError:
            print(f"   [INFO] Update endpoint not available (graceful degradation)")
        except ValueError as e:
            print(f"   [ERROR] {e}")
        print()

        # 5. Delete chat (with graceful handling)
        print("5. Testing chat deletion...")
        deleted = client.chats.delete(chat_id)
        if deleted:
            print(f"   [OK] Chat deleted successfully")
        else:
            print(f"   [INFO] Delete operation returned false (endpoint may be unavailable)")
        print()

        # 6. Sync with local history
        print("6. Syncing server chats with local history...")
        sync_result = client.history.sync_with_server()

        if sync_result["synced"]:
            print(f"   [OK] Sync completed successfully")
            print(f"   Synced count: {sync_result.get('synced_count', 0)}")
            print(f"   Total server chats: {sync_result.get('total_server_chats', 0)}")

            if sync_result.get("note"):
                print(f"   [INFO] {sync_result['note']}")
            if sync_result.get("errors"):
                for error in sync_result["errors"]:
                    print(f"   [WARNING] {error}")
        else:
            print(f"   [ERROR] Sync failed: {sync_result.get('reason', 'unknown')}")
        print()

        # 7. Show local conversation statistics
        print("7. Local conversation statistics...")
        stats = client.history.get_stats()
        print(f"   Local conversations: {stats['total_conversations']}")
        print(f"   Total messages: {stats['total_messages']}")
        print(f"   Server sync enabled: {stats['server_sync']}")
        print(f"   Persistence enabled: {stats['persistence_enabled']}")
        print()

        # 8. Create a server chat using history manager
        print("8. Creating server chat via history manager...")
        server_chat_id = client.history.create_server_chat(
            module_id="chat",
            message="Chat created via history manager"
        )
        if server_chat_id:
            if server_chat_id.startswith("local_"):
                print(f"   [INFO] Created local fallback chat: {server_chat_id}")
            else:
                print(f"   [OK] Created server chat: {server_chat_id}")
        else:
            print("   [ERROR] Failed to create chat via history manager")
        print()

    except APIError as e:
        print(f"[ERROR] API Error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")


async def async_chat_management_example():
    """Example of asynchronous chat management operations with graceful degradation"""
    print("=== Asynchronous Chat Management Example ===\n")

    client = AsyncTela(enable_history=True)

    try:
        # 1. List existing chats asynchronously
        print("1. Listing existing chats (async)...")
        chats = await client.chats.list(page=1, page_size=5)

        if chats.total == 0 and not chats.data:
            print("   [INFO] Chat endpoints appear unavailable (graceful degradation active)")
            print(f"   [OK] Empty response: {len(chats.data)} chats")
        else:
            print(f"   [OK] Found {len(chats.data)} chats on page {chats.page}")
            for chat in chats.data:
                print(f"   - {chat.id}: {chat.title or 'Untitled'}")
        print()

        # 2. Create multiple chats concurrently
        print("2. Creating multiple chats concurrently...")

        async def create_demo_chat(suffix):
            return await client.chats.create(
                module_id="chat",
                message=f"Async Demo Chat {suffix} - Welcome!"
            )

        # Create 3 chats concurrently
        tasks = [create_demo_chat(i) for i in range(1, 4)]
        created_responses = await asyncio.gather(*tasks, return_exceptions=True)

        chat_ids = []
        for i, response in enumerate(created_responses, 1):
            if isinstance(response, Exception):
                print(f"   [ERROR] Chat {i}: {response}")
            else:
                chat_id = response.get("chat_id")
                chat_ids.append(chat_id)

                if chat_id and chat_id.startswith("local_"):
                    print(f"   [INFO] Chat {i}: Created local fallback {chat_id}")
                else:
                    print(f"   [OK] Chat {i}: Created {chat_id}")
        print()

        # 3. Get chat details concurrently
        if chat_ids:
            print("3. Getting chat details concurrently...")

            async def get_chat_details(chat_id):
                try:
                    return await client.chats.get(chat_id)
                except Exception as e:
                    return f"Error: {e}"

            detail_tasks = [get_chat_details(chat_id) for chat_id in chat_ids if chat_id]
            chat_details = await asyncio.gather(*detail_tasks)

            for i, details in enumerate(chat_details, 1):
                if isinstance(details, str):
                    print(f"   [ERROR] Chat {i}: {details}")
                else:
                    is_local = details.metadata.get('local', False) if details.metadata else False
                    status = "[INFO] Local mock" if is_local else "[OK] Server chat"
                    print(f"   {status} {i}: {details.id} - {details.title}")
            print()

        # 4. Test update operations
        if chat_ids and chat_ids[0]:
            print("4. Testing async update operation...")
            try:
                updated = await client.chats.update(
                    chat_ids[0],
                    name="Async Updated Name"
                )
                if hasattr(updated, 'metadata') and updated.metadata.get('local'):
                    print(f"   [INFO] Update simulated locally")
                else:
                    print(f"   [OK] Updated on server")
                print(f"   Chat: {updated.id}, New title: {updated.title}")
            except Exception as e:
                print(f"   [ERROR] Update failed: {e}")
            print()

    except APIError as e:
        print(f"[ERROR] API Error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
    finally:
        await client.close()


def pagination_example():
    """Example of handling paginated chat results with graceful degradation"""
    print("=== Pagination Example ===\n")

    client = Tela()

    try:
        page = 1
        page_size = 5
        total_chats = 0
        max_pages = 3  # Limit to prevent infinite loop

        while page <= max_pages:
            print(f"Fetching page {page}...")
            chats = client.chats.list(page=page, page_size=page_size)

            if not chats.data and page == 1:
                print("   [INFO] No chats available (server may be unavailable)")
                print("   [OK] Graceful degradation: returning empty list")
                break

            if not chats.data:
                print("   No more chats to fetch")
                break

            print(f"   Page {chats.page}: {len(chats.data)} chats")
            for chat in chats.data:
                print(f"   - {chat.id}: {chat.title or 'Untitled'}")
                total_chats += 1

            # Check if there are more pages
            if chats.has_next is False or len(chats.data) < page_size:
                print("   Reached last page")
                break

            page += 1
            print()

        print(f"\nTotal chats processed: {total_chats}")

    except APIError as e:
        print(f"[ERROR] API Error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")


def integrated_conversation_example():
    """Example of integrated conversation management with server sync"""
    print("=== Integrated Conversation Management Example ===\n")

    client = Tela(enable_history=True)

    try:
        # 1. Create a server chat and use it for conversation
        print("1. Creating chat for conversation...")
        server_chat_response = client.chats.create(
            module_id="chat",
            message="Welcome to integrated conversation demo!"
        )
        server_chat_id = server_chat_response.get("chat_id")

        if server_chat_id and server_chat_id.startswith("local_"):
            print(f"   [INFO] Using local fallback chat: {server_chat_id}")
        else:
            print(f"   [OK] Created server chat: {server_chat_id}")
        print()

        # 2. Create local conversation for history tracking
        print("2. Setting up local conversation history...")
        conv = client.create_conversation(server_chat_id)
        conv.add_message("system", "You are a helpful assistant in a chat management demo.")
        conv.add_message("user", "Hello! This is a test message in a managed chat.")
        print(f"   [OK] Local conversation initialized with {conv.message_count} messages")
        print()

        # 3. Use the chat for a conversation with send_message
        print("3. Starting conversation with server chat...")
        response = client.send_message(
            "Can you explain the benefits of server-side chat management?",
            conversation_id=server_chat_id,
            model="wizard",
            temperature=0.7
        )

        if response:
            print(f"   [OK] Assistant response received")
            print(f"   Response preview: {response[:100]}...")
        else:
            print(f"   [ERROR] No response received")
        print()

        # 4. Continue the conversation
        print("4. Continuing conversation...")
        response2 = client.send_message(
            "What about local conversation history?",
            conversation_id=server_chat_id,
            model="wizard"
        )

        if response2:
            print(f"   [OK] Second response received")
            print(f"   Response preview: {response2[:100]}...")
        print()

        # 5. Check local conversation history
        print("5. Checking local conversation history...")
        local_conv = client.get_conversation(server_chat_id)
        if local_conv:
            print(f"   [OK] Local conversation has {local_conv.message_count} messages")

            # Show last few messages
            messages = local_conv.get_messages()
            for i, msg in enumerate(messages[-3:], 1):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:50]
                print(f"   Recent message {i} ({role}): {content}...")
        else:
            print(f"   [ERROR] Could not retrieve local conversation")
        print()

        # 6. Export the conversation
        print("6. Exporting conversation...")
        try:
            exported_json = client.export_conversation(server_chat_id, format="json")
            exported_text = client.export_conversation(server_chat_id, format="text")

            print(f"   [OK] Exported JSON: {len(str(exported_json))} characters")
            print(f"   [OK] Exported text: {len(exported_text)} characters")
        except Exception as e:
            print(f"   [ERROR] Export failed: {e}")
        print()

        # 7. Demonstrate working chat completions
        print("7. Testing standard chat completions (always works)...")
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": "Say 'Chat completions work perfectly!'"}],
                model="wizard",
                max_tokens=20
            )
            print(f"   [OK] Response: {completion.choices[0].message.content}")
        except Exception as e:
            print(f"   [ERROR] Chat completion failed: {e}")

    except APIError as e:
        print(f"[ERROR] API Error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")


def main():
    """Main function to run all examples"""
    print("Comprehensive Chat Management Examples")
    print("======================================\n")

    print("NOTE: This example demonstrates both server-side chat management")
    print("and graceful degradation when endpoints are unavailable.\n")
    print("Current status: Chat management endpoints (/chats/*) may not be")
    print("available on the server yet, so the client uses local fallbacks.\n")
    print("=" * 60 + "\n")

    try:
        # Run synchronous examples
        sync_chat_management_example()
        print("\n" + "="*60 + "\n")

        # Pagination example
        pagination_example()
        print("\n" + "="*60 + "\n")

        # Integrated conversation example
        integrated_conversation_example()
        print("\n" + "="*60 + "\n")

        # Run asynchronous example
        asyncio.run(async_chat_management_example())

        # Summary
        print("\n" + "="*60)
        print("Summary:")
        print("- Chat management endpoints may not be available on server yet")
        print("- The package handles this gracefully with fallback responses")
        print("- Local conversation management works perfectly")
        print("- Standard chat completions (/chat/completions) work as expected")
        print("- The implementation is ready for when server endpoints become available")
        print("="*60)

    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"Failed to run examples: {e}")


if __name__ == "__main__":
    main()