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
system_instruction_base = """
Actúa como un "Second Brain Ejecutivo" especializado en real estate, automatización comercial, análisis financiero global y consulta inteligente en tiempo real. 
No sos un chatbot: sos un operador de negocio. Tu objetivo es cerrar operaciones, detectar oportunidades antes que el mercado y automatizar decisiones.

REGLAS DE OPERACIÓN:
- Canal: Telegram (usá negritas, listas y formato Markdown).
- Tono: Profesional, Directo, Estratégico, Nivel alto (cliente premium).
- Idioma: Español Rioplatense (Argentino) con voseo ('che', 'fijate', 'tenés').
- Estilo: Respuestas cortas, estructuradas y 100% accionables. Sin relleno.
- Prioridad: Decisiones y acciones sobre explicaciones teóricas.

FUNCIONES:
1) GESTIÓN DE LEADS: Clasificá siempre en Caliente, Tibio o Frío. Mensaje listo para enviar/copiar.
2) TASACIÓN: Usá la herramienta 'estimate_property_value'. Explicación en máx 5 líneas.
3) MERCADO: Usá 'get_market_dashboard' para datos en tiempo real de USD y bolsa.
4) AGENDA: Usá 'create_event' para agendar visitas o llamadas.
5) KNOWLEDGE BASE (NOTION MODE): Usá 'search_knowledge_base' para consultar documentos guardados.

[DATO CRÍTICO]: Siempre que te pidan info de mercado, tasar o buscar en tus notas, USÁ LAS HERRAMIENTAS correspondientes. 
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
    return "\n\n".join(results[:3]) if results else "No encontré notas específicas."

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
        "description": "Obtiene dólares y mercado.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "estimate_property_value",
        "description": "Tasación de propiedad.",
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
        "description": "Busca en el Second Brain.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    }
]

messages = []

def process_message(text: str) -> str:
    global messages
    messages.append({"role": "user", "content": text})
    
    ahora = datetime.datetime.now()
    fecha_exacta_str = ahora.strftime('%A %d de %B del %Y a las %H:%M hs')
    dynamic_system = system_instruction_base + f"\n\n[FECHA ACTUAL]: {fecha_exacta_str}."
    
    try:
        # Intento con Claude
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2048,
            system=dynamic_system,
            tools=anthropic_tools,
            messages=messages
        )
        
        messages.append({"role": "assistant", "content": response.content})
        tool_uses = [b for b in response.content if getattr(b, "type", "") == "tool_use"]
        
        if tool_uses:
            tool_results = []
            for tool_use in tool_uses:
                res = run_tool(tool_use.name, tool_use.input)
                tool_results.append({
                    "role": "user",
                    "content": [{"type": "tool_result", "tool_use_id": tool_use.id, "content": res}]
                })
            messages.extend(tool_results)
            final_response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=2048,
                system=dynamic_system,
                tools=anthropic_tools,
                messages=messages
            )
            messages.append({"role": "assistant", "content": final_response.content})
            return next((b.text for b in final_response.content if getattr(b, "type", "") == "text"), "Ok.")
        else:
            return next((b.text for b in response.content if getattr(b, "type", "") == "text"), "Dime.")

    except Exception as e:
        print(f"Fallback detectado. Error Claude: {e}")
        # FALLBACK A GEMINI 2.0 FLASH
        try:
            # Gemini chat manual (simplificado para no implementar todas las herramientas de nuevo aquí)
            prompt_gemini = f"{dynamic_system}\n\nUsuario dice: {text}\n\nResponde como el Executive Second Brain."
            res_gemini = gemini_model.generate_content(prompt_gemini)
            return res_gemini.text + "\n\n_(Nota: Respondiendo via motor de respaldo Gemini 2.0)_"
        except Exception as ge:
            return f"❌ Error total en ambos motores: {ge}"
