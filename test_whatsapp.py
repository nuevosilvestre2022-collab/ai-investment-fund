import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
# Fixed Twilio Sandbox Number
from_number = "whatsapp:+14155238886"
# User's ARG number
to_number = "whatsapp:+5491138700083"

client = Client(account_sid, auth_token)

print(f"Enviando mensaje desde {from_number} hacia {to_number}...")

try:
    message = client.messages.create(
        body="¡Hola Santiago! 🔥 Soy tu Second Brain, levantado desde Python y potenciado por Claude 4. ¡Podemos decir que funciona de maravilla! 🚀",
        from_=from_number,
        to=to_number
    )
    print(f"¡EXITO! Mensaje disparado con identificador SID: {message.sid}")
except Exception as e:
    print(f"Error de Twilio: {e}")
