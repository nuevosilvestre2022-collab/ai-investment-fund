import requests
import json

try:
    response = requests.get("https://openrouter.ai/api/v1/models")
    models = response.json().get("data", [])
    free_models = []
    
    for m in models:
        # Algunos modelos tienen pricing={"prompt": "0", "completion": "0"} 
        # u otros floats que equivalen a 0.
        try:
            pricing = m.get("pricing", {})
            prompt_price = float(pricing.get("prompt", 1))
            completion_price = float(pricing.get("completion", 1))
            if prompt_price == 0 and completion_price == 0:
                free_models.append(m["id"])
        except:
            pass
            
    print("Modelos Gratuitos Disponibles:")
    for fm in free_models:
        print(fm)
except Exception as e:
    print(f"Error: {e}")
