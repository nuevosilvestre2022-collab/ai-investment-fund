import datetime
from calendar_service import authenticate_google

def main():
    service = authenticate_google()
    # Buscamos eventos desde el 2024 en adelante para ver si se perdió en el tiempo
    past_date = datetime.datetime(2024, 1, 1).isoformat() + 'Z'
    print('Buscando eventos agendados desde 2024...\n')
    
    events_result = service.events().list(calendarId='primary', timeMin=past_date,
                                          maxResults=15, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No se encontró absolutamente ningún evento en este calendario.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"Fecha: {start} | Resumen: {event['summary']}")

if __name__ == '__main__':
    main()
