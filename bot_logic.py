import os
import json
from anthropic import AsyncAnthropic
import google.generativeai as genai
import datetime
import glob
from dotenv import load_dotenv
from calendar_service import create_event
from market_data import get_dolar_rates, get_m2_valuation, get_market_summary

load_dotenv()

# Clientes Asincrónicos
anthropic_client = AsyncAnthropic(api_key=os.getenv("CLAUDE_API_KEY"))

# Gemini (ya soporta async en su modelo si se llama adecuadamente)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-2.0-flash')

# Persona: Executive Second Brain (Advanced Operator Mode)
SYSTEM_PROMPT = """
Sos el "Executive Second Brain" de Santiago. No sos un asistente; sos un OPERADOR ESTRATÉGICO. 

TU ADN:
1. RAZONAMIENTO: Siempre explicá tu lógica. Santiago quiere ver CÓMO pensás el mercado.
2. INICIATIVA: Si ves una oportunidad (dólar bajo, zona en alza), proponela.
3. TONO: Socio de confianza, nivel premium. Español rioplatense (voseo).
4. ACCIÓN: Buscá siempre el siguiente paso de negocios.

REGLAS:
- Formato impecable en Telegram (negritas, listas).
- Herramientas mandatorias para datos reales.
"""

async def search_knowledge_base(query: str):
    kb_path = "knowledge_base/*.md"
    results = []
    files = glob.glob(kb_path)
    for f in files:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            if query.lower() in content.lower():
                results.append(f"--- ARCHIVO: {os.path.basename(f)} ---\n{content}\n")
    return "\n\n".join(results[:3]) if results else "No encontré notas específicas."

async def run_tool(name, args):
    if name == "get_market_dashboard":
        return json.dumps({"dolares": get_dolar_rates(), "contexto": get_market_summary()}, indent=2)
    elif name == "estimate_property_value":
        val = get_m2_valuation(args['neighborhood'])
        return json.dumps({"min": val['range'][0]*args['m2'], "avg": val['avg']*args['m2']}, indent=2)
    elif name == "search_knowledge_base":
        return await search_knowledge_base(args['query'])
    elif name == "create_event":
        return create_event(**args)
    return "Error: Tool not found."

anthropic_tools = [
    {"name": "create_event", "description": "Agenda en Calendar", "input_schema": {"type": "object", "properties": {"summary": {"type": "string"}, "start_time_iso": {"type": "string"}}, "required": ["summary", "start_time_iso"]}},
    {"name": "get_market_dashboard", "description": "USD y Mercado", "input_schema": {"type": "object", "properties": {}}},
    {"name": "estimate_property_value", "description": "Tasar propiedad", "input_schema": {"type": "object", "properties": {"neighborhood": {"type": "string"}, "m2": {"type": "number"}}, "required": ["neighborhood", "m2"]}},
    {"name": "search_knowledge_base", "description": "Buscar en notas", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}
]

# Nombres de modelos para rotación resiliente
CLAUDE_MODELS = ["claude-3-5-sonnet-20241022", "claude-3-5-sonnet-latest", "claude-3-haiku-20240307"]
GEMINI_MODELS = [
    "gemini-2.5-pro", 
    "gemini-2.0-flash", 
    "gemini-pro-latest", 
    "gemini-1.5-flash-latest",
    "gemini-flash-latest"
]

async def process_message(text: str, history: list) -> str:
    history.append({"role": "user", "content": text})
    dynamic_system = SYSTEM_PROMPT + f"\n\n[TIEMPO REAL]: {datetime.datetime.now()}"
    
    error_log = []

    # 1. INTENTAR CLAUDE (Prioridad Alta)
    for model_name in CLAUDE_MODELS:
        try:
            response = await anthropic_client.messages.create(
                model=model_name,
                max_tokens=2048,
                system=dynamic_system,
                tools=anthropic_tools,
                messages=history
            )
            return await handle_anthropic_response(response, history, dynamic_system)
        except Exception as e:
            error_log.append(f"Claude ({model_name}): {str(e)[:50]}")
            continue

    # 2. FALLBACK GEMINI (Inteligencia Pro -> Flash)
    for g_model in GEMINI_MODELS:
        try:
            model = genai.GenerativeModel(g_model)
            chat_ctx = "\n".join([f"{m['role']}: {str(m.get('content'))[:400]}" for m in history[-6:]])
            prompt = f"{dynamic_system}\n\n[MODO RESILIENCIA]\nContexto:\n{chat_ctx}\n\nSantiago dice: {text}"
            
            response_google = await model.generate_content_async(prompt)
            if response_google.text:
                history.append({"role": "assistant", "content": response_google.text})
                footer = f"\n\n_(Usando {g_model} por mantenimiento en Claude)_"
                return response_google.text + footer
        except Exception as ge:
            error_log.append(f"Gemini ({g_model}): {str(ge)[:50]}")
            continue

    # 3. ÚLTIMO RECURSO (Falla Total)
    debug_str = "\n".join(error_log)
    return f"❌ Error Crítico: No pude conectar con ninguna IA.\nDetalles:\n{debug_str[:200]}"

async def handle_anthropic_response(response, history, dynamic_system):
    tool_uses = [b for b in response.content if getattr(b, "type", "") == "tool_use"]
    if tool_uses:
        history.append({"role": "assistant", "content": response.content})
        for tu in tool_uses:
            res = await run_tool(tu.name, tu.input)
            history.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": tu.id, "content": res}]})
        
        final_res = await anthropic_client.messages.create(
            model=response.model, # Usar el mismo modelo que respondió inicialmente
            max_tokens=2048,
            system=dynamic_system,
            tools=anthropic_tools,
            messages=history
        )
        txt = next((b.text for b in final_res.content if getattr(b, "type", "") == "text"), "Respuesta procesada.")
        history.append({"role": "assistant", "content": txt})
        return txt
    else:
        txt = next((b.text for b in response.content if getattr(b, "type", "") == "text"), "Analizado.")
        history.append({"role": "assistant", "content": txt})
        return txt
