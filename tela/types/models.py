from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel

__all__ = [
    "Model",
    "ModelList", 
    "ModelCapabilities",
    "UsageInfo",
]


class Model(BaseModel):
    """Represents a model available on the API"""
    id: str
    object: str = "model"
    created: int
    owned_by: str
    
    model_config = {"extra": "allow"}


class ModelList(BaseModel):
    """List of available models"""
    object: str = "list"
    data: List[Model]
    
    model_config = {"extra": "allow"}


class ModelCapabilities(BaseModel):
    """Model capabilities and supported parameters"""
    model_id: str
    supports_streaming: bool = True
    supports_tools: bool = True
    supports_json_mode: bool = True
    supports_vision: bool = False
    supports_audio: bool = False
    max_context_length: Optional[int] = None
    max_output_tokens: Optional[int] = None
    
    # Parameter ranges and defaults
    temperature_range: tuple[float, float] = (0.0, 2.0)
    top_p_range: tuple[float, float] = (0.0, 1.0)
    presence_penalty_range: tuple[float, float] = (-2.0, 2.0)
    frequency_penalty_range: tuple[float, float] = (-2.0, 2.0)
    
    # Default values
    default_temperature: float = 1.0
    default_top_p: float = 1.0
    default_max_tokens: Optional[int] = None
    
    model_config = {"extra": "allow"}
    
    @classmethod
    def from_model_id(cls, model_id: str) -> "ModelCapabilities":
        """Create capabilities info based on model ID patterns"""
        capabilities = cls(model_id=model_id)
        
        # Detect capabilities based on model name patterns
        model_lower = model_id.lower()
        
        # Vision models
        if any(vision_keyword in model_lower for vision_keyword in 
               ['vision', 'llava', 'multimodal', 'visual']):
            capabilities.supports_vision = True
        
        # Audio/TTS/STT models
        if any(audio_keyword in model_lower for audio_keyword in 
               ['voice', 'tts', 'stt', 'audio', 'speech']):
            capabilities.supports_audio = True
            # Audio models typically don't support standard text generation features
            capabilities.supports_streaming = False
            capabilities.supports_tools = False
            capabilities.supports_json_mode = False
        
        # Coding-specific models might have different defaults
        if any(code_keyword in model_lower for code_keyword in 
               ['coder', 'code', 'programming']):
            capabilities.default_temperature = 0.2  # Lower temperature for coding
        
        # Reasoning/thinking models
        if any(reasoning_keyword in model_lower for reasoning_keyword in 
               ['thinking', 'reasoning', 'r1']):
            capabilities.default_temperature = 0.7
            
        # Large models typically have higher context lengths
        if any(size_indicator in model_lower for size_indicator in 
               ['405b', '235b', '120b', '80b']):
            capabilities.max_context_length = 32768
        elif any(size_indicator in model_lower for size_indicator in 
                 ['70b', '30b', '27b']):
            capabilities.max_context_length = 16384
        else:
            capabilities.max_context_length = 8192
            
        return capabilities


class UsageInfo(BaseModel):
    """Usage information from API response"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_tokens_details: Optional[Dict[str, Any]] = None
    completion_tokens_details: Optional[Dict[str, Any]] = None
    
    model_config = {"extra": "allow"}
    
    @property
    def cost_estimate(self) -> Optional[float]:
        """Estimate cost based on token usage (placeholder - would need real pricing data)"""
        # This is a placeholder - in a real implementation you'd have pricing per model
        # For now, return None to indicate pricing isn't available
        return None
    
    @property
    def efficiency_ratio(self) -> float:
        """Ratio of completion tokens to total tokens"""
        if self.total_tokens == 0:
            return 0.0
        return self.completion_tokens / self.total_tokens


class ParameterInfo(BaseModel):
    """Information about supported parameters for completions"""
    
    # Required parameters
    messages: str = "List of conversation messages (required)"
    
    # Optional parameters with descriptions and ranges
    model: str = "Model ID to use (default: 'wizard')"
    max_tokens: str = "Maximum tokens to generate (int, model-dependent limit)"
    temperature: str = "Sampling temperature 0.0-2.0 (higher = more creative)"
    top_p: str = "Nucleus sampling 0.0-1.0 (alternative to temperature)"
    presence_penalty: str = "Penalize new concepts -2.0 to 2.0"
    frequency_penalty: str = "Penalize repetition -2.0 to 2.0" 
    n: str = "Number of alternative completions (int)"
    stop: str = "Stop sequences (string or array, max 4 sequences)"
    stream: str = "Enable streaming with Server-Sent Events (bool)"
    logprobs: str = "Return log probabilities (bool)"
    top_logprobs: str = "Number of most likely tokens to return probs for (int)"
    response_format: str = "Response format - use {\"type\": \"json_object\"} for JSON mode"
    seed: str = "Deterministic sampling seed (int)"
    user: str = "End-user identifier for abuse monitoring (string)"
    tools: str = "Available functions/tools the model can call (array)"
    tool_choice: str = "Tool usage: 'auto', 'none', or specific function"
    logit_bias: str = "Bias specific tokens by ID (advanced, map<int,float>)"
    
    model_config = {"extra": "allow"}
    
    def get_parameter_help(self, parameter: str = None) -> str | Dict[str, str]:
        """Get help for a specific parameter or all parameters"""
        params_dict = {
            "messages": self.messages,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature, 
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "n": self.n,
            "stop": self.stop,
            "stream": self.stream,
            "logprobs": self.logprobs,
            "top_logprobs": self.top_logprobs,
            "response_format": self.response_format,
            "seed": self.seed,
            "user": self.user,
            "tools": self.tools,
            "tool_choice": self.tool_choice,
            "logit_bias": self.logit_bias,
        }
        
        if parameter:
            return params_dict.get(parameter, f"Parameter '{parameter}' not found")
        return params_dict