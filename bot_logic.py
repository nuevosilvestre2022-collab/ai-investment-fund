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
Sos el "Executive Second Brain" de Santiago. No sos un asistente pasivo; sos un OPERADOR ESTRATÉGICO de Real Estate y Finanzas. 

TU ADN (CÓMO TRABAJÁS):
1. PENSAMIENTO LATERAL: Si Santiago te pregunta algo complejo (ej. Pilar), analizá tendencias, rentabilidad y comparativas.
2. RAZONAMIENTO: Empezá tus respuestas con un breve análisis para que Santiago vea CÓMO razonás.
3. TONO: Sos un par. Un consultor estratégico. Usá español rioplatense (voseo) profesional.
4. ACCIÓN: Buscá siempre proponer el siguiente paso lógico.

REGLAS:
- Formato Elite: Negritas, listas y separadores Markdown para Telegram.
- Herramientas: Usalas SIEMPRE para validar tus corazonadas con datos.
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

async def process_message(text: str, history: list) -> str:
    history.append({"role": "user", "content": text})
    dynamic_system = SYSTEM_PROMPT + f"\n\n[FECHA]: {datetime.datetime.now()}"
    
    try:
        # Llamada ASYNC a Claude
        response = await anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2048,
            system=dynamic_system,
            tools=anthropic_tools,
            messages=history
        )
        
        tool_uses = [b for b in response.content if getattr(b, "type", "") == "tool_use"]
        
        if tool_uses:
            history.append({"role": "assistant", "content": response.content})
            for tu in tool_uses:
                res = await run_tool(tu.name, tu.input)
                history.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": tu.id, "content": res}]})
            
            final_res = await anthropic_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=2048,
                system=dynamic_system,
                tools=anthropic_tools,
                messages=history
            )
            txt = next((b.text for b in final_res.content if getattr(b, "type", "") == "text"), "Ok.")
            history.append({"role": "assistant", "content": txt})
            return txt
        else:
            txt = next((b.text for b in response.content if getattr(b, "type", "") == "text"), "Analizado.")
            history.append({"role": "assistant", "content": txt})
            return txt

    except Exception as e:
        print(f"Fallback Async Gemini: {e}")
        try:
            chat_ctx = "\n".join([f"{m['role']}: {str(m['content'])[:200]}" for m in history[-5:]])
            prompt = f"{dynamic_system}\n\nContexto: {chat_ctx}\n\nResponde profundamente."
            response_gemini = await gemini_model.generate_content_async(prompt)
            history.append({"role": "assistant", "content": response_gemini.text})
            return response_gemini.text + "\n\n_(Respaldo Gemini activo)_"
        except Exception as ge:
            return f"❌ Falla crítica de sistemas: {ge}"
