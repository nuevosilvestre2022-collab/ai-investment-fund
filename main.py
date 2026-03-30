import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
from aiohttp import web

# Import logic
from bot_logic import process_message
from daily_report import generate_daily_report

load_dotenv()

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.environ.get("PORT", "8000")) # Para Render

async def handle_health_check(request):
    """Responder OK a Render."""
    return web.Response(text="Bot is ALIVE", status=200)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /start."""
    user = update.effective_user
    await update.message.reply_text(
        f"Hola {user.first_name}. Soy tu **Executive Second Brain**.\n"
        "Estoy listo para operar. Mandame tus leads, pedime tasaciones o consultame el mercado.\n"
        "Usa /report para el resumen diario."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa mensajes de texto del usuario."""
    text = update.message.text
    print(f"\n[NUEVO TELEGRAM] {update.effective_user.first_name}: {text}")
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Procesar con Claude (bot_logic)
    respuesta_ia = process_message(text)
    
    # Responder
    await update.message.reply_text(respuesta_ia, parse_mode='Markdown')

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /report."""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    report = generate_daily_report()
    await update.message.reply_text(report, parse_mode='Markdown')

async def run_bot():
    """Inicia el bot de Telegram."""
    if not TOKEN:
        print("ERROR: No se encontró TELEGRAM_BOT_TOKEN en el .env")
        return
    
    print("Iniciando Executive Second Brain en Telegram...")
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('report', report_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Loop de espera
    while True:
        await asyncio.sleep(1)

async def main():
    """Inicia tanto el servidor web como el bot."""
    # Servidor Web para Render Health Check
    app_web = web.Application()
    app_web.router.add_get("/", handle_health_check)
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"Health check server running on port {PORT}")
    
    # Ejecutar Bot
    await run_bot()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
