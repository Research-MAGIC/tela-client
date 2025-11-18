"""
Embedding API Example

This script demonstrates how to use the Tela API embeddings endpoint
to generate vector embeddings for text input.
"""

import os
import json
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_embedding(
    input_text: list[str] | str,
    model: str = "qwen/qwen3-embedding-4b",
    api_key: str = None,
    organization: str = None,
    project: str = None
) -> dict:
    """
    Create embeddings for the given input text.

    Args:
        input_text: A string or list of strings to embed
        model: The embedding model to use
        api_key: API key (defaults to TELAOS_API_KEY env var)
        organization: Organization ID (defaults to TELAOS_ORG_ID env var)
        project: Project ID (defaults to TELAOS_PROJECT_ID env var)

    Returns:
        The API response as a dictionary
    """
    # Get credentials from environment if not provided
    api_key = api_key or os.getenv("TELAOS_API_KEY")
    organization = organization or os.getenv("TELAOS_ORG_ID")
    project = project or os.getenv("TELAOS_PROJECT_ID")

    if not api_key:
        raise ValueError("API key is required. Set TELAOS_API_KEY environment variable.")

    # Ensure input is a list
    if isinstance(input_text, str):
        input_text = [input_text]

    # API endpoint
    url = "https://api.telaos.com/v1/embeddings"

    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    if organization:
        headers["OpenAI-Organization"] = organization
    if project:
        headers["OpenAI-Project"] = project

    # Request payload
    payload = {
        "model": model,
        "input": input_text
    }

    # Make the request
    with httpx.Client(timeout=60.0) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


def main():
    print("=" * 60)
    print("Tela Embeddings API Example")
    print("=" * 60)
    print()

    # Example 1: Single text embedding
    print("Example 1: Single text embedding")
    print("-" * 40)

    text = "Hello World"
    print(f"Input text: '{text}'")
    print(f"Model: qwen/qwen3-embedding-4b")
    print()

    try:
        result = create_embedding(text, model="qwen/qwen3-embedding-4b")

        print("Response payload:")
        print(f"  Object: {result.get('object')}")
        print(f"  Model: {result.get('model')}")

        if 'data' in result and len(result['data']) > 0:
            embedding_data = result['data'][0]
            print(f"  Embedding index: {embedding_data.get('index')}")
            print(f"  Embedding object: {embedding_data.get('object')}")

            embedding = embedding_data.get('embedding', [])
            print(f"  Embedding dimensions: {len(embedding)}")
            print(f"  First 10 values: {embedding[:10]}")
            print(f"  Last 10 values: {embedding[-10:]}")

        if 'usage' in result:
            usage = result['usage']
            print(f"  Usage - prompt tokens: {usage.get('prompt_tokens')}")
            print(f"  Usage - total tokens: {usage.get('total_tokens')}")

        print()
        print("Full JSON response:")
        # Print truncated version to avoid huge output
        result_copy = result.copy()
        if 'data' in result_copy:
            for item in result_copy['data']:
                if 'embedding' in item:
                    emb = item['embedding']
                    item['embedding'] = f"[{len(emb)} dimensions - truncated]"
        print(json.dumps(result_copy, indent=2))

    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

    print()
    print("=" * 60)

    # Example 2: Multiple text embeddings
    print()
    print("Example 2: Multiple text embeddings")
    print("-" * 40)

    texts = ["Hello World", "How are you?", "Machine learning is fascinating"]
    print(f"Input texts: {texts}")
    print()

    try:
        result = create_embedding(texts, model="qwen/qwen3-embedding-4b")

        print(f"Number of embeddings returned: {len(result.get('data', []))}")

        for i, item in enumerate(result.get('data', [])):
            embedding = item.get('embedding', [])
            print(f"  Text {i+1}: '{texts[i]}'")
            print(f"    Dimensions: {len(embedding)}")
            print(f"    First 5 values: {embedding[:5]}")

        if 'usage' in result:
            usage = result['usage']
            print(f"\n  Total usage - prompt tokens: {usage.get('prompt_tokens')}")
            print(f"  Total usage - total tokens: {usage.get('total_tokens')}")

    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

    print()
    print("=" * 60)
    print("Done!")


if __name__ == "__main__":
    main()
