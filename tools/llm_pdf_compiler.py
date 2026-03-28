import json
import os
import time
from typing import List, Dict
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Usamos gemini-1.5-flash: modelo estable y gratuito (15 RPM, 1M tokens/día)
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    google_api_key=GOOGLE_API_KEY,
    model="gemini-1.5-flash",
    temperature=0.4,
    max_output_tokens=4096,  # Cap explícito para no superar el límite gratuito
)

# Tiempo de espera entre llamadas al LLM para respetar 15 RPM del free tier
DELAY_BETWEEN_CALLS = 5  # segundos

SYSTEM_DOC_COMPILER = """
Eres un Analista Financiero Senior de un Hedge Fund (estilo Buffett y Lynch).
Escribe un 'Deep Dive' conciso pero denso (equivalente a 1-2 páginas A4) sobre el activo o idea solicitada.
Responde SIEMPRE en Español. Incluye profundidad financiera, moats, catalizadores y riesgos.

CRÍTICO: Tu respuesta DEBE ser un ARRAY JSON válido y nada más. Sin texto fuera del JSON.

Bloques permitidos:
{"type": "H1", "content": "Título"}
{"type": "H2", "content": "Subtítulo"}
{"type": "H3", "content": "Sección"}
{"type": "P", "content": "Párrafo de análisis"}
{"type": "BULLETS", "items": ["Punto 1", "Punto 2", "Punto 3"]}
{"type": "IMAGE", "query": "simple_english_keyword"}

Responde SOLO con el JSON Array. Máximo 20 bloques por sección para no exceder límites.
"""

def _clean_json(text: str) -> List[Dict]:
    content = text.strip()
    if content.startswith("```json"): content = content[7:-3]
    elif content.startswith("```"): content = content[3:-3]
    import re
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        content = match.group(0)
    try:
        return json.loads(content)
    except Exception as e:
        print(f"Error parseando JSON del Deep Dive: {e}")
        return [{"type": "P", "content": "Error generando contenido profundo para este activo."}]

def _call_llm_safe(prompt: str, context_name: str) -> List[Dict]:
    """Llama al LLM con retry automático si hay rate limit (error 429)."""
    for attempt in range(3):
        try:
            msg = HumanMessage(content=prompt)
            response = llm.invoke([SystemMessage(content=SYSTEM_DOC_COMPILER), msg])
            time.sleep(DELAY_BETWEEN_CALLS)  # Respetar 15 RPM del free tier
            return _clean_json(response.content)
        except Exception as e:
            err_str = str(e).lower()
            if "quota" in err_str or "429" in err_str or "rate" in err_str:
                wait = 30 * (attempt + 1)
                print(f"[!] Rate limit en {context_name}. Esperando {wait}s (intento {attempt+1}/3)...")
                time.sleep(wait)
            else:
                print(f"[!] Error en {context_name}: {e}")
                return [{"type": "P", "content": f"Error generando análisis de {context_name}."}]
    return [{"type": "P", "content": f"Límite de intentos agotado para {context_name}."}]


def generate_stock_deep_dive(ticker: str, name: str, data: dict) -> List[Dict]:
    """Generates a deep dive on a stock (máx 15 bloques para free tier)."""
    print(f"[*] Gemini redactando Deep Dive de Acción: {ticker}...")
    prompt = f"""
    DEEP DIVE de {name} (Ticker: {ticker}).
    Datos: Precio ${data.get('current_price', 'N/A')} | P/E {data.get('pe_ratio', 'N/A')}x | FCF ${(data.get('free_cash_flow',0)/1e9):.1f}B | ROE {data.get('roe', 0)*100:.0f}%

    Cubre en MÁXIMO 15 bloques JSON:
    1. Tesis de Inversión (H1 + 1 párrafo P)
    2. [IMAGE 'stock market']
    3. Modelo de Negocio y Moat (H2 + P + BULLETS con pros/contras)
    4. Catalizadores y Valoración (H2 + P)
    """
    return _call_llm_safe(prompt, ticker)


def generate_real_estate_deep_dive(country: str, city: str, opp: str) -> List[Dict]:
    """Generates a Real Estate appraisal (máx 15 bloques para free tier)."""
    print(f"[*] Gemini redactando Deep Dive Real Estate: {city}, {country}...")
    prompt = f"""
    DEEP DIVE Inmobiliario: {city}, {country}.
    Oportunidad: {opp}

    Cubre en MÁXIMO 15 bloques JSON:
    1. Panorama del mercado (H1 + P)
    2. [IMAGE 'real estate building']
    3. Zonas recomendadas y tipo de inversión (H2 + BULLETS)
    4. Unit economics y riesgos clave (H2 + P + BULLETS)
    """
    return _call_llm_safe(prompt, f"Real Estate {city}")


def generate_startup_deep_dive(sector: str, opportunity: str) -> List[Dict]:
    """Generates a Startup/Business deep dive (máx 15 bloques para free tier)."""
    print(f"[*] Gemini redactando Business Plan: {sector}...")
    prompt = f"""
    DEEP DIVE Emprendimiento: {sector}.
    Visión: {opportunity}

    Cubre en MÁXIMO 15 bloques JSON:
    1. El problema y la oportunidad de mercado (H1 + P)
    2. [IMAGE 'startup technology']
    3. Solución y Go-To-Market (H2 + P + BULLETS primeros 100 clientes)
    4. Unit economics y plan 90 días (H2 + BULLETS)
    """
    return _call_llm_safe(prompt, f"Startup {sector}")
