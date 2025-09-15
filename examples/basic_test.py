from dotenv import load_dotenv
from tela import Tela

# Load environment variables from .env file
load_dotenv()

client = Tela()
models = client.get_models()
print(f"Found {len(models.data)} models")

# Use a reliable model that's commonly available
available_model = "qwen3-max"  
print(f"Using model: {available_model}")

response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello"}],
    model=available_model)
content = response.choices[0].message.content
# Handle potential Unicode encoding issues on Windows
try:
    print(content)
except UnicodeEncodeError:
    print(content.encode('ascii', errors='replace').decode('ascii'))