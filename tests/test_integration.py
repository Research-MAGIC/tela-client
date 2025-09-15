"""
Integration tests for Tela client with real API calls
These tests require valid API credentials to be set in environment variables
"""

import os
import pytest
import asyncio
from typing import Dict, Any

from tela import Tela, AsyncTela
from tela._exceptions import AuthenticationError, APIError


# Skip integration tests if credentials are not available
skip_if_no_credentials = pytest.mark.skipif(
    not all([
        os.getenv("TELAOS_API_KEY") or os.getenv("TELAOS_ACCESS_TOKEN"),
        os.getenv("TELAOS_ORG_ID") or os.getenv("ORG_ID"),
        os.getenv("TELAOS_PROJECT_ID") or os.getenv("PROJ_ID")
    ]),
    reason="API credentials not available"
)


def get_test_credentials() -> Dict[str, str]:
    """Get test credentials from environment variables"""
    return {
        "api_key": os.getenv("TELAOS_API_KEY") or os.getenv("TELAOS_ACCESS_TOKEN"),
        "organization": os.getenv("TELAOS_ORG_ID") or os.getenv("ORG_ID"),
        "project": os.getenv("TELAOS_PROJECT_ID") or os.getenv("PROJ_ID")
    }


@skip_if_no_credentials
class TestRealAPIIntegration:
    """Integration tests with real API calls"""
    
    def test_client_authentication(self):
        """Test that client can authenticate with real credentials"""
        creds = get_test_credentials()
        
        client = Tela(
            api_key=creds["api_key"],
            organization=creds["organization"],
            project=creds["project"]
        )
        
        # Client should initialize without error
        assert client.api_key == creds["api_key"]
        assert client.organization == creds["organization"]
        assert client.project == creds["project"]
    
    def test_simple_completion(self):
        """Test basic completion request"""
        creds = get_test_credentials()
        client = Tela(**creds)
        
        try:
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": "Say hello"}],
                max_tokens=50,
                temperature=0.7
            )
            
            assert response is not None
            assert hasattr(response, 'choices')
            assert len(response.choices) > 0
            assert hasattr(response.choices[0], 'message')
            assert response.choices[0].message.content is not None
            
            print(f"✅ Completion response: {response.choices[0].message.content[:100]}...")
            
        except Exception as e:
            pytest.fail(f"Completion request failed: {e}")
    
    def test_conversation_with_history(self):
        """Test conversation with history tracking"""
        creds = get_test_credentials()
        client = Tela(**creds, enable_history=True)
        
        try:
            # Send first message
            response1 = client.send_message("My name is Alice. Remember this.")
            assert response1 is not None
            print(f"✅ Response 1: {response1[:100]}...")
            
            # Send follow-up that requires memory
            response2 = client.send_message("What's my name?")
            assert response2 is not None
            assert "alice" in response2.lower() or "Alice" in response2
            print(f"✅ Response 2: {response2[:100]}...")
            
            # Check conversation was saved
            conversations = client.list_conversations()
            assert len(conversations) > 0
            
            # Check conversation content
            conv = client.get_conversation(conversations[0])
            assert conv.message_count >= 4  # 2 user + 2 assistant messages
            
        except Exception as e:
            pytest.fail(f"Conversation with history failed: {e}")
    
    def test_streaming_completion(self):
        """Test streaming completion"""
        creds = get_test_credentials()
        client = Tela(**creds)
        
        try:
            stream = client.chat.completions.create(
                messages=[{"role": "user", "content": "Count from 1 to 5"}],
                stream=True,
                temperature=0.1
            )
            
            chunks = []
            content_pieces = []
            
            for chunk in stream:
                chunks.append(chunk)
                if hasattr(chunk, 'choices') and chunk.choices:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta') and choice.delta and choice.delta.content:
                        content_pieces.append(choice.delta.content)
            
            assert len(chunks) > 0
            assert len(content_pieces) > 0
            
            full_content = "".join(content_pieces)
            print(f"✅ Streaming content: {full_content[:100]}...")
            
        except Exception as e:
            pytest.fail(f"Streaming completion failed: {e}")
    
    def test_conversation_export(self):
        """Test conversation export functionality"""
        creds = get_test_credentials()
        client = Tela(**creds, enable_history=True)
        
        try:
            # Create a conversation
            conv_id = "export-test"
            conv = client.create_conversation(conv_id)
            
            # Add some messages
            client.send_message("Hello", conversation_id=conv_id)
            client.send_message("How are you?", conversation_id=conv_id)
            
            # Test different export formats
            formats = ["json", "text", "markdown", "messages"]
            
            for format_type in formats:
                exported = client.export_conversation(conv_id, format=format_type)
                assert exported is not None
                print(f"✅ Export format {format_type}: {str(exported)[:100]}...")
                
        except Exception as e:
            pytest.fail(f"Conversation export failed: {e}")
    
    def test_error_handling(self):
        """Test error handling with invalid requests"""
        creds = get_test_credentials()
        client = Tela(**creds)
        
        try:
            # Test with empty messages (should handle gracefully or error appropriately)
            with pytest.raises((ValueError, APIError)):
                client.chat.completions.create(messages=[])
            
            # Test with invalid model (should handle appropriately)
            try:
                response = client.chat.completions.create(
                    messages=[{"role": "user", "content": "test"}],
                    model="invalid-model-name"
                )
                # If this doesn't raise an error, that's also valid
            except Exception as e:
                # Expected for invalid model
                print(f"✅ Expected error for invalid model: {type(e).__name__}")
                
        except Exception as e:
            pytest.fail(f"Error handling test failed: {e}")


@skip_if_no_credentials
class TestAsyncAPIIntegration:
    """Integration tests for async client"""
    
    @pytest.mark.asyncio
    async def test_async_completion(self):
        """Test async completion"""
        creds = get_test_credentials()
        client = AsyncTela(**creds)
        
        try:
            response = await client.chat.completions.create(
                messages=[{"role": "user", "content": "Say hello async"}],
                max_tokens=50,
                temperature=0.7
            )
            
            assert response is not None
            assert hasattr(response, 'choices')
            assert len(response.choices) > 0
            assert response.choices[0].message.content is not None
            
            print(f"✅ Async completion: {response.choices[0].message.content[:100]}...")
            
        finally:
            await client.close()
    
    @pytest.mark.asyncio
    async def test_async_conversation(self):
        """Test async conversation with history"""
        creds = get_test_credentials()
        client = AsyncTela(**creds, enable_history=True)
        
        try:
            # Send async messages with history
            response1 = await client.send_message("I like pizza")
            assert response1 is not None
            
            response2 = await client.send_message("What do I like?")
            assert response2 is not None
            assert "pizza" in response2.lower()
            
            print(f"✅ Async conversation with memory working")
            
        finally:
            await client.close()
    
    @pytest.mark.asyncio
    async def test_async_streaming(self):
        """Test async streaming"""
        creds = get_test_credentials()
        client = AsyncTela(**creds)
        
        try:
            stream = await client.chat.completions.create(
                messages=[{"role": "user", "content": "Count from 1 to 3"}],
                stream=True,
                temperature=0.1
            )
            
            chunks = []
            async for chunk in stream:
                chunks.append(chunk)
                if len(chunks) >= 10:  # Limit for test
                    break
            
            assert len(chunks) > 0
            print(f"✅ Async streaming received {len(chunks)} chunks")
            
        finally:
            await client.close()


@skip_if_no_credentials
class TestPerformanceAndLimits:
    """Test performance and API limits"""
    
    def test_context_length_handling(self):
        """Test handling of long context"""
        creds = get_test_credentials()
        client = Tela(**creds, enable_history=True)
        
        try:
            # Create conversation with many messages
            conv_id = "long-context"
            conv = client.create_conversation(conv_id)
            
            # Add many message pairs
            for i in range(20):
                conv.add_message("user", f"Message number {i}")
                conv.add_message("assistant", f"Response to message {i}")
            
            # Test with context limit
            response = client.send_message(
                "Summarize our conversation",
                conversation_id=conv_id,
                max_history=10  # Limit context
            )
            
            assert response is not None
            print(f"✅ Long context handled with limit")
            
        except Exception as e:
            pytest.fail(f"Context length test failed: {e}")
    
    def test_rapid_requests(self):
        """Test handling rapid sequential requests"""
        creds = get_test_credentials()
        client = Tela(**creds)
        
        try:
            responses = []
            
            # Send multiple rapid requests
            for i in range(3):  # Limited to avoid rate limiting
                response = client.chat.completions.create(
                    messages=[{"role": "user", "content": f"Quick test {i}"}],
                    max_tokens=10
                )
                responses.append(response)
            
            assert len(responses) == 3
            assert all(r is not None for r in responses)
            print(f"✅ Rapid requests handled successfully")
            
        except Exception as e:
            # Rate limiting is expected
            if "rate" in str(e).lower():
                print(f"✅ Rate limiting working as expected: {e}")
            else:
                pytest.fail(f"Rapid requests test failed: {e}")


class TestCredentialValidation:
    """Test credential validation without API calls"""
    
    def test_invalid_credentials_format(self):
        """Test handling of invalid credential formats"""
        with pytest.raises(AuthenticationError):
            Tela(api_key="", organization="org", project="proj")
        
        with pytest.raises(AuthenticationError):
            Tela(api_key="key", organization="", project="proj")
        
        with pytest.raises(AuthenticationError):
            Tela(api_key="key", organization="org", project="")
    
    def test_missing_credentials(self):
        """Test handling of missing credentials"""
        # Clear environment variables for this test
        import os
        old_key = os.environ.get("TELAOS_API_KEY")
        old_token = os.environ.get("TELAOS_ACCESS_TOKEN") 
        old_org = os.environ.get("TELAOS_ORG_ID")
        old_proj = os.environ.get("TELAOS_PROJECT_ID")
        
        try:
            # Clear all relevant env vars
            for key in ["TELAOS_API_KEY", "TELAOS_ACCESS_TOKEN", "TELAOS_ORG_ID", "ORG_ID", "TELAOS_PROJECT_ID", "PROJ_ID"]:
                if key in os.environ:
                    del os.environ[key]
            
            with pytest.raises(AuthenticationError):
                Tela()
                
        finally:
            # Restore environment variables
            if old_key:
                os.environ["TELAOS_API_KEY"] = old_key
            if old_token:
                os.environ["TELAOS_ACCESS_TOKEN"] = old_token
            if old_org:
                os.environ["TELAOS_ORG_ID"] = old_org
            if old_proj:
                os.environ["TELAOS_PROJECT_ID"] = old_proj


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s"])