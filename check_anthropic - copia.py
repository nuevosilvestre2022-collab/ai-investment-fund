import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv("CLAUDE_API_KEY")
)

# Probamos modelos conocidos
models = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-sonnet-20240229",
    "claude-3-opus-20240229",
    "claude-3-haiku-20240307"
]

print("Verificando acceso a modelos...")
for m in models:
    try:
        response = client.messages.create(
            model=m,
            max_tokens=10,
            messages=[{"role": "user", "content": "hola"}]
        )
        print(f"[OK] {m}")
    except Exception as e:
        print(f"[ERROR] {m}: {e}")
