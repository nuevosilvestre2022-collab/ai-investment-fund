import os
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
try:
    models = client.models.list()
    print("Modelos disponibles para esta API Key:")
    for model in models:
        print(model.id)
except Exception as e:
    print(f"Error listando modelos: {e}")
