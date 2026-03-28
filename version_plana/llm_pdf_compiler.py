import json
import os
import time
from typing import List, Dict
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# We will use Gemini 2.5 Flash to generate massive deep dive reports
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    google_api_key=GOOGLE_API_KEY,
    model="gemini-2.5-flash",
    temperature=0.4, # slightly creative for business ideas
)

SYSTEM_DOC_COMPILER = """
Eres un Analista Financiero Senior de un Hedge Fund Cuantitativo (estilo Buffett y Lynch).
Tu objetivo es escribir un 'Deep Dive' ultra detallado (equivalente a 3-5 páginas A4) sobre el activo o idea solicitada.
DEBES escribir en Español nativo, con muchísima profundidad financiera, lógica de mercado, pros, contras, catalizadores, moats, y unit economics.

IMPORTANTE: El formato de salida DEBE ser estrictamente un ARRAY JSON válido. NO uses Markdown fuera del JSON. Cada elemento del array representa un bloque visual en el PDF generado.

Tipos de bloques permitidos:
{{"type": "H1", "content": "Título Principal"}}
{{"type": "H2", "content": "Subtítulo"}}
{{"type": "H3", "content": "Sección Pequeña"}}
{{"type": "P", "content": "Un párrafo largo y denso de análisis..."}}
{{"type": "BULLETS", "items": ["Punto 1", "Punto 2"]}}
{{"type": "IMAGE", "query": "palabra_clave_en_ingles"}} -> Usa keywords muy simples (ej: 'building', 'stock_market', 'technology', 'artificial_intelligence', 'real_estate') para que el sistema descargue una foto ilustrativa.

Estructura tu respuesta como un enorme JSON Array sin nada más.
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

def generate_stock_deep_dive(ticker: str, name: str, data: dict) -> List[Dict]:
    """Generates a 3-4 page fundamental deep dive on a stock."""
    print(f"[*] Gemini redactando Deep Dive de Acción: {ticker}...")
    
    prompt = f"""
    Genera el DEEP DIVE completo de la empresa {name} (Ticker: {ticker}).
    Datos actuales cruzados (yfinance+fmp):
    - Precio: ${data.get('current_price', 'N/A')}
    - P/E: {data.get('pe_ratio', 'N/A')}x
    - FCF TTM: ${(data.get('free_cash_flow',0)/1e9):.2f}B
    - ROE: {data.get('roe', 0)*100:.1f}%
    
    Estructura obligatoria (usa multiples H2, H3 y P):
    1. Tesis de Inversión Ejecutiva (H1, H2, P...)
    2. Foto ilustrativa (IMAGE 'corporate office')
    3. Análisis del Modelo de Negocio (¿Cómo ganan plata exactamente?)
    4. Ventaja Competitiva / Moat (Foso económico, estilo Buffett)
    5. Catalizadores de Crecimiento (Peter Lynch 10-bagger potential)
    6. Análisis de Riesgos (Pros y Contras detallados en BULLETS)
    7. Valoración y Conclusión
    """
    
    msg = HumanMessage(content=prompt)
    response = llm.invoke([SystemMessage(content=SYSTEM_DOC_COMPILER), msg])
    return _clean_json(response.content)

def generate_real_estate_deep_dive(country: str, city: str, opp: str) -> List[Dict]:
    """Generates a comprehensive Real Estate market appraisal."""
    print(f"[*] Gemini redactando Deep Dive Real Estate: {city}, {country}...")
    
    prompt = f"""
    Genera el DEEP DIVE Inmobiliario para: {city}, {country}.
    Oportunidad Base: {opp}
    
    Estructura obligatoria:
    1. Panorama Macro del Real Estate en {country} (H1, P)
    2. Foto de la ciudad o casas (IMAGE '{city} architecture')
    3. Zonas Calientes / Barrios Recomendados.
    4. Tipología de inversión recomendada (Flipping, Airbnb, Long-term).
    5. Unit Economics (Costos de entrada, impuestos, expensas, yield neto estimado).
    6. Riesgos Legales y Macroeconómicos.
    7. Conclusión.
    """
    
    msg = HumanMessage(content=prompt)
    response = llm.invoke([SystemMessage(content=SYSTEM_DOC_COMPILER), msg])
    return _clean_json(response.content)

def generate_startup_deep_dive(sector: str, opportunity: str) -> List[Dict]:
    """Generates a Startup Pitch / Business Model deep dive."""
    print(f"[*] Gemini redactando Business Plan: {sector}...")
    
    prompt = f"""
    Genera el BUSINESS PLAN o DEEP DIVE de Emprendimiento para el sector: {sector}.
    Visión: {opportunity}
    Especialmente enfocado en el contexto actual (2026+) e Inteligencia Artificial en español si aplica.
    
    Estructura obligatoria:
    1. El Problema (H1) / ¿Por qué nadie lo está resolviendo bien?
    2. Foto conceptual (IMAGE '{sector.replace(' ', '_')} startup')
    3. La Solución / Producto Base (Software o Físico).
    4. Go-To-Market Strategy (¿Cómo conseguimos los primeros 100 clientes que paguen?).
    5. Unit Economics y Estructura de Costos.
    6. Competencia y Foso Defensivo.
    7. Plan de Ejecución a 90 días.
    """
    
    msg = HumanMessage(content=prompt)
    response = llm.invoke([SystemMessage(content=SYSTEM_DOC_COMPILER), msg])
    return _clean_json(response.content)
