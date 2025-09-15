"""
Tests for endpoint information and model capabilities functionality
"""

import pytest
from unittest.mock import Mock
from typing import List

from tela import Tela, AsyncTela
from tela import Model, ModelList, ModelCapabilities, UsageInfo, ParameterInfo


def get_test_credentials():
    """Get test credentials from environment"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    return {
        "api_key": os.getenv("TELAOS_API_KEY"),
        "organization": os.getenv("TELAOS_ORG_ID"),
        "project": os.getenv("TELAOS_PROJECT_ID")
    }


class TestModelInformation:
    """Test model information retrieval"""
    
    def test_get_models(self):
        """Test retrieving list of available models"""
        creds = get_test_credentials()
        client = Tela(**creds)
        
        models = client.get_models()
        
        assert isinstance(models, ModelList)
        assert len(models.data) > 0
        assert all(isinstance(model, Model) for model in models.data)
        
        # Check first model has required fields
        first_model = models.data[0]
        assert hasattr(first_model, 'id')
        assert hasattr(first_model, 'owned_by')
        assert hasattr(first_model, 'created')
        print(f"✅ Found {len(models.data)} models")
    
    def test_get_model_info(self):
        """Test getting specific model information"""
        creds = get_test_credentials()
        client = Tela(**creds)
        
        # First get available models
        models = client.get_models()
        test_model_id = models.data[0].id
        
        model_info = client.get_model_info(test_model_id)
        
        assert isinstance(model_info, Model)
        assert model_info.id == test_model_id
        assert model_info.owned_by is not None
        print(f"✅ Retrieved info for model: {model_info.id}")
    
    def test_get_model_info_invalid_model(self):
        """Test error handling for invalid model ID"""
        creds = get_test_credentials()
        client = Tela(**creds)
        
        with pytest.raises(ValueError, match="Model 'invalid-model' not found"):
            client.get_model_info("invalid-model")
    
    def test_get_model_capabilities(self):
        """Test model capabilities detection"""
        creds = get_test_credentials()
        client = Tela(**creds)
        
        # Test coding model capabilities
        caps = client.get_model_capabilities('qwen3-coder')
        
        assert isinstance(caps, ModelCapabilities)
        assert caps.model_id == 'qwen3-coder'
        assert caps.supports_streaming is True
        assert caps.supports_tools is True
        assert caps.default_temperature == 0.2  # Coding models should have lower temp
        print(f"✅ Coding model capabilities: temp={caps.default_temperature}")
        
        # Test reasoning model capabilities  
        caps = client.get_model_capabilities('deepseek-r1')
        assert caps.default_temperature == 0.7  # Reasoning models
        print(f"✅ Reasoning model capabilities: temp={caps.default_temperature}")
    
    def test_list_available_models(self):
        """Test listing models by category"""
        creds = get_test_credentials()
        client = Tela(**creds)
        
        # Test all models
        all_models = client.list_available_models()
        assert isinstance(all_models, list)
        assert len(all_models) > 0
        assert all(isinstance(model_id, str) for model_id in all_models)
        print(f"✅ All models: {len(all_models)} found")
        
        # Test coding models
        coding_models = client.list_available_models('coding')
        assert isinstance(coding_models, list)
        assert all('coder' in model.lower() or 'code' in model.lower() for model in coding_models)
        print(f"✅ Coding models: {coding_models}")
        
        # Test large models
        large_models = client.list_available_models('large')
        assert isinstance(large_models, list)
        if large_models:  # May not have large models
            assert any('235b' in model.lower() or '405b' in model.lower() or '120b' in model.lower() 
                      for model in large_models)
            print(f"✅ Large models: {large_models}")


class TestParameterInformation:
    """Test parameter information and help"""
    
    def test_get_parameter_info(self):
        """Test parameter information retrieval"""
        client = Tela(api_key="test", organization="test", project="test")
        
        param_info = client.get_parameter_info()
        
        assert isinstance(param_info, ParameterInfo)
        
        # Test specific parameter help
        temp_help = param_info.get_parameter_help('temperature')
        assert 'temperature' in temp_help.lower()
        assert '0.0-2.0' in temp_help
        
        # Test all parameters help
        all_help = param_info.get_parameter_help()
        assert isinstance(all_help, dict)
        assert 'temperature' in all_help
        assert 'max_tokens' in all_help
        assert 'messages' in all_help
        print(f"✅ Parameter info available for: {list(all_help.keys())}")
    
    def test_parameter_help_invalid_param(self):
        """Test help for invalid parameter"""
        client = Tela(api_key="test", organization="test", project="test")
        param_info = client.get_parameter_info()
        
        help_text = param_info.get_parameter_help('invalid_param')
        assert "not found" in help_text


class TestUsageInformation:
    """Test usage information extraction and analysis"""
    
    def test_get_usage_from_response(self):
        """Test extracting usage info from API response"""
        creds = get_test_credentials()
        client = Tela(**creds)
        
        # Make a request
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10,
            model="qwen3-coder"
        )
        
        # Extract usage information
        usage_info = client.get_usage_from_response(response)
        
        assert usage_info is not None
        assert isinstance(usage_info, UsageInfo)
        assert usage_info.prompt_tokens > 0
        assert usage_info.completion_tokens > 0
        assert usage_info.total_tokens > 0
        assert usage_info.total_tokens == usage_info.prompt_tokens + usage_info.completion_tokens
        
        # Test efficiency ratio
        ratio = usage_info.efficiency_ratio
        assert 0 <= ratio <= 1
        print(f"✅ Usage: {usage_info.prompt_tokens} + {usage_info.completion_tokens} = {usage_info.total_tokens} tokens")
        print(f"✅ Efficiency ratio: {ratio:.2f}")
    
    def test_get_usage_from_response_no_usage(self):
        """Test handling response without usage information"""
        client = Tela(api_key="test", organization="test", project="test")
        
        # Mock response without usage
        mock_response = Mock()
        mock_response.usage = None
        
        usage_info = client.get_usage_from_response(mock_response)
        assert usage_info is None


class TestAsyncModelInformation:
    """Test async model information functionality"""
    
    @pytest.mark.asyncio
    async def test_async_get_models(self):
        """Test async model retrieval"""
        creds = get_test_credentials()
        client = AsyncTela(**creds)
        
        try:
            models = await client.get_models()
            
            assert isinstance(models, ModelList)
            assert len(models.data) > 0
            print(f"✅ Async: Found {len(models.data)} models")
            
        finally:
            await client.close()
    
    @pytest.mark.asyncio
    async def test_async_get_model_info(self):
        """Test async model info retrieval"""
        creds = get_test_credentials()
        client = AsyncTela(**creds)
        
        try:
            models = await client.get_models()
            test_model_id = models.data[0].id
            
            model_info = await client.get_model_info(test_model_id)
            
            assert isinstance(model_info, Model)
            assert model_info.id == test_model_id
            print(f"✅ Async: Retrieved info for model: {model_info.id}")
            
        finally:
            await client.close()
    
    @pytest.mark.asyncio
    async def test_async_list_available_models(self):
        """Test async model listing"""
        creds = get_test_credentials()
        client = AsyncTela(**creds)
        
        try:
            all_models = await client.list_available_models()
            assert isinstance(all_models, list)
            assert len(all_models) > 0
            
            coding_models = await client.list_available_models('coding')
            assert isinstance(coding_models, list)
            print(f"✅ Async: Found {len(all_models)} total, {len(coding_models)} coding models")
            
        finally:
            await client.close()


class TestModelCapabilities:
    """Test model capabilities detection logic"""
    
    def test_vision_model_detection(self):
        """Test vision model capability detection"""
        client = Tela(api_key="test", organization="test", project="test")
        
        caps = client.get_model_capabilities('llava:13b-v1.5')
        assert caps.supports_vision is True
        print("✅ Vision model detected correctly")
    
    def test_audio_model_detection(self):
        """Test audio model capability detection"""
        client = Tela(api_key="test", organization="test", project="test")
        
        caps = client.get_model_capabilities('fabric-voice-tts')
        assert caps.supports_audio is True
        assert caps.supports_streaming is False  # Audio models typically don't stream
        assert caps.supports_tools is False  # Audio models typically don't use tools
        print("✅ Audio model detected correctly")
    
    def test_large_model_context_length(self):
        """Test large model context length detection"""
        client = Tela(api_key="test", organization="test", project="test")
        
        caps = client.get_model_capabilities('qwen3-235b-a22b')
        assert caps.max_context_length >= 16384  # Large models should have high context
        print(f"✅ Large model context length: {caps.max_context_length}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])