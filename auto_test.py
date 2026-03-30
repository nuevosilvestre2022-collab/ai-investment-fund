import sys
import warnings

warnings.filterwarnings("ignore")

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

from bot_logic import process_message

print("====================================")
print("Enviando mensaje de prueba al bot:")
print("Vos: 'Che, anotame una reunion de Analisis de Datos manana a las 15:00'")
print("====================================\n")

print("Cerebro de Gemini pensando (y conectandose al calendario)...\n")
try:
    respuesta = process_message("Che, anotame una reunion de Analisis de Datos manana a las 15:00 hrs.")
    print("Respuesta del bot:")
    print(respuesta)
except Exception as e:
    print(f"Fallo grave en bot: {e}")
