import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scope necesario para tener acceso total al calendario (leer y escribir)
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def authenticate_google():
    """Autentica al usuario usando el archivo credentials.json y guarda token.json"""
    creds = None
    # Verifica si ya tenemos el token guardado de una sesión anterior
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # Si no hay credenciales válidas, le pide al usuario que inicie sesión en el navegador
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Guarda el token para la próxima vez
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)

def create_event(summary: str, start_time_iso: str, end_time_iso: str = None, description: str = ""):
    """Crea un evento en el calendario principal."""
    try:
        service = authenticate_google()
        
        # Si no nos dan la hora de fin, asume 1 hora por defecto
        if not end_time_iso:
            start_date = datetime.datetime.fromisoformat(start_time_iso.replace('Z', '+00:00'))
            end_date = start_date + datetime.timedelta(hours=1)
            end_time_iso = end_date.isoformat()
            
        event = {
          'summary': summary,
          'description': description,
          'start': {
            'dateTime': start_time_iso,
            'timeZone': 'America/Argentina/Buenos_Aires',
          },
          'end': {
            'dateTime': end_time_iso,
            'timeZone': 'America/Argentina/Buenos_Aires',
          },
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        return f"Éxito: Evento '{summary}' creado en tu calendario."

    except HttpError as error:
        return f"Hubo un error al contactar al calendario: {error}"


# Si se ejecuta este archivo suelto, lo usamos para forzar el inicio de sesión
if __name__ == "__main__":
    print("Iniciando autenticación manual de Google Calendar...")
    authenticate_google()
    print("Autenticación exitosa! 'token.json' guardado. Ya no te pedirá iniciar sesión.")
