import os
import json
import anthropic
import google.generativeai as genai
import datetime
import glob
from dotenv import load_dotenv
from calendar_service import create_event
from market_data import get_dolar_rates, get_m2_valuation, get_market_summary

load_dotenv()

# Cliente Anthropic
anthropic_client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

# Configuración Gemini (Fallback)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-2.0-flash')

# Persona: Executive Second Brain specialized in Real Estate
SYSTEM_PROMPT = """
Actúa como un "Executive Business Operator" y "Second Brain" de altísimo nivel. 
Tu especialidad es el Real Estate, la ingeniería financiera y el análisis de mercado ultra-específico.

FILOSOFÍA DE RESPUESTA:
1. NO SOS UN CHATBOT: Sos un socio de negocios que razona, cuestiona y propone. No esperes a que te pidan "códigos"; tené una conversación fluida pero técnica.
2. RAZONAMIENTO (Chain of Thought): Antes de dar una cifra, explicá brevemente la lógica de mercado detrás (ej. oferta/demanda, contexto macro, costo de oportunidad).
3. TONO: Profesional, estratégico, directo, nivel premium (español rioplatense refinado).
4. ACCIÓN: Siempre buscá el cierre o el siguiente paso lógico (visita, reserva, análisis profundo).

CAPACIDADES ESPECIALES:
- Análisis de Barrios: Si te piden Pilar o zonas específicas, razoná sobre la infraestructura, seguridad y perfiles de comprador (Inversores vs Consumidores finales).
- Gestión de Leads: Clasificá el interés y armá la estrategia de seguimiento.
- Tasación: No solo des el m2, analizá si la propiedad está en precio para "salir rápido" o para "retener valor".

REGLAS DE FORMATO:
- Usá Markdown (negritas, listas) para que en Telegram se vea IMPECABLE.
- Respuestas densas en valor pero cortas en lectura.
"""

def search_knowledge_base(query: str):
    kb_path = "knowledge_base/*.md"
    results = []
    files = glob.glob(kb_path)
    query = query.lower()
    for f in files:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            if query in content.lower() or query in f.lower():
                results.append(f"--- ARCHIVO: {os.path.basename(f)} ---\n{content}\n")
    return "\n\n".join(results[:3]) if results else "No encontré notas específicas en el Second Brain."

def run_tool(name, args):
    if name == "create_event":
        return create_event(**args)
    elif name == "get_market_dashboard":
        fx = get_dolar_rates()
        mkt = get_market_summary()
        return json.dumps({"dolares": fx, "contexto": mkt}, indent=2)
    elif name == "estimate_property_value":
        val = get_m2_valuation(args['neighborhood'])
        m2 = args['m2']
        res = {
            "min": val['range'][0] * m2,
            "recomendado": val['avg'] * m2,
            "optimista": val['range'][1] * m2,
            "valor_m2_avg": val['avg']
        }
        return json.dumps(res, indent=2)
    elif name == "search_knowledge_base":
        return search_knowledge_base(args['query'])
    return "Herramienta no encontrada."

# Claude Tool Definitions
anthropic_tools = [
    {
        "name": "create_event",
        "description": "Agenda un evento en el Google Calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "start_time_iso": {"type": "string"}
            },
            "required": ["summary", "start_time_iso"]
        }
    },
    {
        "name": "get_market_dashboard",
        "description": "Obtiene dólares y panorama de mercado actual.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "estimate_property_value",
        "description": "Calcula valor estimado según m2 y zona (CABA).",
        "input_schema": {
            "type": "object",
            "properties": {
                "neighborhood": {"type": "string"},
                "m2": {"type": "number"}
            },
            "required": ["neighborhood", "m2"]
        }
    },
    {
        "name": "search_knowledge_base",
        "description": "Busca en el Second Brain (documentos locales).",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    }
]

def process_message(text: str, history: list) -> str:
    """
    Procesa un mensaje manteniendo la historia específica del usuario.
    """
    history.append({"role": "user", "content": text})
    
    ahora = datetime.datetime.now()
    fecha_exacta_str = ahora.strftime('%A %d de %B del %Y a las %H:%M hs')
    dynamic_system = SYSTEM_PROMPT + f"\n\n[DATO CRÍTICO]: Hoy es {fecha_exacta_str}. Ajustá tus análisis a este tiempo real."
    
    try:
        # Intento con Claude
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2048,
            system=dynamic_system,
            tools=anthropic_tools,
            messages=history
        )
        
        # Procesar herramientas
        tool_uses = [b for b in response.content if getattr(b, "type", "") == "tool_use"]
        
        if tool_uses:
            history.append({"role": "assistant", "content": response.content})
            for tool_use in tool_uses:
                res = run_tool(tool_use.name, tool_use.input)
                history.append({
                    "role": "user",
                    "content": [{"type": "tool_result", "tool_use_id": tool_use.id, "content": res}]
                })
            
            final_response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=2048,
                system=dynamic_system,
                tools=anthropic_tools,
                messages=history
            )
            history.append({"role": "assistant", "content": final_response.content})
            return next((b.text for b in final_response.content if getattr(b, "type", "") == "text"), "Respuesta procesada con impacto.")
        else:
            assistant_text = next((b.text for b in response.content if getattr(b, "type", "") == "text"), "Analizando...")
            history.append({"role": "assistant", "content": assistant_text})
            return assistant_text

    except Exception as e:
        print(f"Fallback Error Claude: {e}")
        try:
            # Fallback Gemini con HISTORIA (simplificado)
            # Para mantener la sesión en Gemini, convertimos history a un prompt concatenado rápido
            chat_context = "\n".join([f"{m['role']}: {m['content']}" for m in history[-5:]])
            prompt_gemini = f"{dynamic_system}\n\nCONTEXTO RECIENTE:\n{chat_context}\n\nExecutive, respondé al último mensaje con razonamiento profundo."
            res_gemini = gemini_model.generate_content(prompt_gemini)
            
            history.append({"role": "assistant", "content": res_gemini.text})
            return res_gemini.text + "\n\n_(Nota: Respondiendo via sistema de respaldo Gemini 2.0)_"
        except Exception as ge:
            return f"❌ Falla crítica de sistemas: {ge}"
