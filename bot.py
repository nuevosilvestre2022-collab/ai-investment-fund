"""
Interactive AI Investment Assistant (Telegram Bot)
Listens 24/7 on Telegram, answers questions, analyzes stocks, and generates reports.
Features Memory (contextual conversation) and Multimodal Real Estate Appraisal.
"""
import os
import json
import base64
import telebot
from datetime import datetime
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Import tools
from tools.financial_data import get_stock_data
from tools.valuation import full_valuation
from reports.report_generator import generate_weekly_report
from tools.memory import get_memory, add_memory

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
llm = ChatGoogleGenerativeAI(google_api_key=GOOGLE_API_KEY, model="gemini-1.5-flash", temperature=0.3)

# Simple in-memory conversation history (stores last 10 messages)
chat_history = []
MAX_HISTORY = 10

def _get_system_prompt():
    mem_facts = get_memory()
    mem_str = "\n".join([f"- {m}" for m in mem_facts]) if mem_facts else "- Ninguno (empezando de cero)"
    
    return f"""
You are the AI Investment Fund Assistant, an expert portfolio manager and real estate appraiser operating via Telegram.
You respond ONLY in Spanish, with premium formatting (using <b>, <i>, <ul> for Telegram HTML).

CONOCIMIENTO A LARGO PLAZO DEL USUARIO (Reglas de Inversión y Preferencias):
{mem_str}

Debes comportarte como el analista personal de este usuario, obedeciendo estas reglas.
Analiza la intención del usuario y responde SOLO con un objeto JSON:

1. {{"action": "chat", "reply": "Tu respuesta analítica profunda aquí."}} -> Para responder y charlar.
2. {{"action": "learn", "fact": "El usuario prefiere empresas tecnológicas", "reply": "Anotado. Lo recordaré para siempre."}} -> ÚSALO cuando el usuario te cuente una preferencia, cuánto dinero tiene, qué acciones ya posee, o te dé una regla de inversión. Tú extraerás el "fact" para guardarlo en la Memoria Permanente.
3. {{"action": "analyze_stock", "ticker": "AAPL"}} -> Solo para buscar datos financieros.
4. {{"action": "generate_report"}} -> Para el resumen en PDF de 2 páginas.
5. {{"action": "generate_deep_dive_report"}} -> SOLAMENTE si el usuario pide explícitamente el PDF largo, profundo, detallado (de 50 hojas) con fotos.
"""

def split_and_send(chat_id, text, parse_mode="HTML"):
    """Telegram limits messages to 4096 chars. Split safely."""
    MAX_LEN = 4000
    if len(text) <= MAX_LEN:
        bot.send_message(chat_id, text, parse_mode=parse_mode)
        return
        
    paragraphs = text.split("\n\n")
    current_chunk = ""
    for p in paragraphs:
        if len(current_chunk) + len(p) + 2 < MAX_LEN:
            current_chunk += p + "\n\n"
        else:
            bot.send_message(chat_id, current_chunk, parse_mode=parse_mode)
            current_chunk = p + "\n\n"
    if current_chunk:
        bot.send_message(chat_id, current_chunk, parse_mode=parse_mode)

def process_intent_with_history(user_text: str) -> dict:
    global chat_history
    try:
        messages = [SystemMessage(content=_get_system_prompt())]
        messages.extend(chat_history)
        messages.append(HumanMessage(content=user_text))
        
        import re
        response = llm.invoke(messages)
        content = response.content.strip()
        # Bulletproof JSON extraction
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            content = match.group(0)
            
        result = json.loads(content)
        
        # Guardar en memoria de largo plazo si es "learn"
        if result.get("action") == "learn" and "fact" in result:
            add_memory(result.get("fact"))
        
        chat_history.append(HumanMessage(content=user_text))
        if result.get("action") in ["chat", "learn"]:
            chat_history.append(AIMessage(content=result.get("reply", "")))
        else:
            chat_history.append(AIMessage(content=f"[Action taken: {result.get('action')}]"))
            
        if len(chat_history) > MAX_HISTORY:
            chat_history = chat_history[-MAX_HISTORY:]
            
        return result
    except Exception as e:
        print(f"Error parsing intent: {e}")
        return {"action": "chat", "reply": f"Tuve un error técnico procesando el pedido. Detalle: <code>{str(e)}</code>"}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if str(message.chat.id) != str(CHAT_ID): return
    bot.send_message(message.chat.id, "🏦 <b>AI Investment Assistant (v3.0 - con memoria)</b> online.", parse_mode='HTML')

@bot.message_handler(content_types=['photo'])
def handle_property_photo(message):
    if str(message.chat.id) != str(CHAT_ID): return
    bot.send_chat_action(message.chat.id, 'typing')
    
    caption = message.caption or "Analizame esta propiedad para invertir."
    bot.send_message(message.chat.id, "🏘 <i>Analizando fotos con motores de tasación...</i>", parse_mode="HTML")
    
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    b64_img = base64.b64encode(downloaded_file).decode('utf-8')
    
    vision_prompt = f"""
    Eres un experto tasador inmobiliario en Argentina. 
    Usuario: '{caption}'
    
    Observa la foto, calcula años de antiguedad, mantenimiento, espacios y da un valor de venta/alquiler estimado y pros/contras para inversión. Responde directo en HTML para Telegram.
    """
    try:
        msg = HumanMessage(content=[
            {"type": "text", "text": vision_prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
        ])
        response = llm.invoke([msg])
        split_and_send(message.chat.id, response.content)
    except Exception as e:
        split_and_send(message.chat.id, f"Error analizando imagen: {e}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    if str(message.chat.id) != str(CHAT_ID): return
    bot.send_chat_action(message.chat.id, 'typing')
    
    if message.document.mime_type != 'application/pdf':
        split_and_send(message.chat.id, "❌ Por ahora solo puedo leer y aprender de archivos PDF.")
        return
        
    bot.send_message(message.chat.id, "📚 <i>Descargando PDF y leyéndolo con Gemini Vision + PyPDF2...</i>", parse_mode="HTML")
    
    try:
        import PyPDF2
        import io
        
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(downloaded_file))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
            
        # Limit to ~800k chars just in case (Gemini handles 1M tokens = ~4M chars)
        text = text[:800000]
        
        doc_prompt = f"""
        El usuario acaba de subirte este documento PDF (como un libro o reporte).
        Nombre del archivo: {message.document.file_name}
        
        Instrucciones:
        1. Lee este documento con cuidado.
        2. Haz un resumen estructurado de las ideas principales, tesis de inversión o reglas de negocio.
        3. Si encuentras reglas útiles para tu trabajo como Analista del Fondo o para el portafolio del usuario, dímelas claramente para que las pueda guardar en la Memoria Permanente.
        
        Contenido del PDF:
        {text}
        """
        response = llm.invoke([HumanMessage(content=doc_prompt)])
        split_and_send(message.chat.id, response.content)
        
    except Exception as e:
        split_and_send(message.chat.id, f"Error leyendo el PDF: {e}")

@bot.message_handler(content_types=['voice', 'audio'])
def handle_audio(message):
    if str(message.chat.id) != str(CHAT_ID): return
    bot.send_chat_action(message.chat.id, 'typing')
    
    bot.send_message(message.chat.id, "🎧 <i>Escuchando tu audio...</i>", parse_mode="HTML")
    
    try:
        # Get file
        file_id = message.voice.file_id if message.content_type == 'voice' else message.audio.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Audio from Telegram is usually OGG OPUS
        b64_audio = base64.b64encode(downloaded_file).decode('utf-8')
        
        audio_prompt = """
        El usuario te ha enviado esta nota de voz por Telegram. 
        Instrucciones:
        1. Escucha/Transcribe internamente lo que dijo.
        2. Analiza su intención. ¿Es una charla? ¿Es un pedido de análisis de una acción? ¿Es información para que guardes en la Memoria Permanente?
        3. Responde directamente a lo que te pide o comenta en formato HTML para Telegram. 
        Actúa como su analista personal hablando naturalmente.
        """
        
        # We try to pass media to LangChain. If it complains, we will use raw REST API.
        try:
            msg = HumanMessage(content=[
                {"type": "text", "text": audio_prompt},
                # For langchain-google-genai 0.1.x +
                {"type": "media", "mime_type": "audio/ogg", "data": b64_audio}
            ])
            response = llm.invoke([msg])
            reply = response.content
        except Exception:
            # Fallback: Raw REST API call to Gemini if LangChain doesn't support 'media' cleanly yet
            import requests
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GOOGLE_API_KEY}"
            payload = {
                "contents": [{
                    "parts": [
                        {"text": audio_prompt},
                        {"inlineData": {"mimeType": "audio/ogg", "data": b64_audio}}
                    ]
                }]
            }
            res = requests.post(url, json=payload).json()
            reply = res["candidates"][0]["content"]["parts"][0]["text"]
            
        split_and_send(message.chat.id, reply)
    except Exception as e:
        split_and_send(message.chat.id, f"Error procesando audio: {e}")

@bot.message_handler(content_types=['text'])
def handle_conversation(message):
    if str(message.chat.id) != str(CHAT_ID): return
    bot.send_chat_action(message.chat.id, 'typing')
    
    intent = process_intent_with_history(message.text)
    action = intent.get("action")
    
    if action == "chat":
        reply = intent.get("reply", "No comprendí.")
        # Sometimes Telegram HTML breaks if tags are unclosed, catch it gracefully
        try:
            split_and_send(message.chat.id, reply, parse_mode="HTML")
        except telebot.apihelper.ApiTelegramException:
            # Fallback without HTML formatting if it fails parsing
            split_and_send(message.chat.id, reply, parse_mode=None)
            
    elif action == "analyze_stock":
        ticker = intent.get("ticker", "").upper()
        bot.send_message(message.chat.id, f"🔍 <i>Cruzando datos de {ticker}...</i>", parse_mode="HTML")
        data = get_stock_data(ticker, verbose=False)
        if "error" in data:
            bot.send_message(message.chat.id, f"❌ Ticker {ticker} no encontrado.")
            return

        eps = data.get("eps_ttm", 0) or 0
        pe = data.get("pe_ratio", 0) or 0
        fcf = data.get("free_cash_flow", 0) or 0
        price = data.get("current_price", 0) or 0
        mos, target = "N/A", "N/A"

        if eps > 0 or fcf > 0:
            bvps = data.get("book_value_per_share", 0) or 0
            growth = (data.get("eps_growth_3y_cagr", 0) or 0) * 100
            cap = data.get("market_cap", 0) or 0
            shares = cap / price if price > 0 else 1
            val = full_valuation(ticker, price, eps, bvps, max(fcf,0), int(shares), pe, growth)
            mos = val.get("blended_mos", "N/A")
            target = f"${val.get('blended_intrinsic_value', 'N/A')}"

        name = data.get("name", ticker)
        msg = (
            f"<b>📊 {ticker} — {name}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Precio:</b> ${price}  |  <b>Target:</b> {target}\n"
            f"<b>Margen Seguridad:</b> {mos}\n"
            f"<b>P/E:</b> {pe}x  |  <b>FCF:</b> ${(fcf/1e9):.1f}B\n\n"
            f"<i>Podés preguntarme '¿por qué comprarías esta acción?' para charlar sobre esto.</i>"
        )
        split_and_send(message.chat.id, msg)

    elif action == "generate_report":
        bot.send_message(message.chat.id, "⏳ <i>Armando PDF Rápido (Resumen)... (~15s)</i>", parse_mode="HTML")
        try:
            path = generate_weekly_report()
            with open(path, 'rb') as f:
                bot.send_document(message.chat.id, f)
        except Exception as e:
            bot.send_message(message.chat.id, f"Error: {e}")

    elif action == "generate_deep_dive_report":
        bot.send_message(message.chat.id, "💎 <i>Iniciando Motor Deep Dive de 50 Páginas con fotos. Esto demora entre 3 y 5 minutos porque Gemini está redactando tesis financieras completas para cada activo. ¡Paciencia! Te avisaré al terminar...</i>", parse_mode="HTML")
        try:
            from reports.deep_dive_pdf import build_deep_dive_report
            path = build_deep_dive_report()
            with open(path, 'rb') as f:
                bot.send_document(message.chat.id, f, caption="Tu Inteligencia Deep Dive Semanal con fotos 📸")
        except Exception as e:
            bot.send_message(message.chat.id, f"Error armando el Deep Dive masivo: {e}")

# --- TRUCO PARA RENDER (WEB SERVICE GRATIS) ---
# UptimeRobot pinga estos endpoints cada 5 min para evitar que Render duerma el bot
from flask import Flask, jsonify
from threading import Thread
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!", 200

@app.route('/ping')
def ping():
    """Endpoint para UptimeRobot keep-alive (gratis en uptimerobot.com)"""
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()}), 200

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "bot": "running"}), 200

def run_server():
    port = int(os.environ.get('PORT', 8080))
    print(f"[Flask] Keep-alive server started on port {port}")
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Arrancamos el mini-servidor web falso en un hilo para engañar a Render
    Thread(target=run_server).start()
    
    # Arrancamos el bot real
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
