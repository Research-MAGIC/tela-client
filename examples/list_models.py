#!/usr/bin/env python3
"""
Example: List all available models and their capabilities
"""

from dotenv import load_dotenv
from tela import Tela

# Load environment variables from .env file
load_dotenv()

def main():
    client = Tela()
    
    print("Getting available models...")
    models = client.get_models()
    
    print(f"\nFound {len(models.data)} available models:\n")
    
    for i, model in enumerate(models.data):  # Show first 10 models
        print(f"{i+1:2d}. {model.id}")
        
        # Get capabilities for this model
        try:
            caps = client.get_model_capabilities(model.id)
            features = []
            if caps.supports_streaming:
                features.append("Streaming")
            if caps.supports_tools:
                features.append("Tools")
            if caps.supports_vision:
                features.append("Vision") 
            if caps.supports_json_mode:
                features.append("JSON")
            
            if features:
                print(f"    Features: {', '.join(features)}")
            if caps.max_context_length:
                print(f"    Context: {caps.max_context_length:,} tokens")
            print()
            
        except Exception as e:
            print(f"    Could not get capabilities: {e}")
            print()
    
    print("\nModel categories:")
    
    # Show models by category
    categories = ['coding', 'vision', 'large', 'reasoning']
    for category in categories:
        try:
            filtered_models = client.list_available_models(category)
            if filtered_models:
                print(f"\n{category.capitalize()} models: {', '.join(filtered_models[:5])}")
                if len(filtered_models) > 5:
                    print(f"  ... and {len(filtered_models) - 5} more")
        except Exception as e:
            print(f"Could not get {category} models: {e}")

if __name__ == "__main__":
    main()