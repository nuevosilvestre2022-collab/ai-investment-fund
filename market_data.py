import requests
import datetime

def get_dolar_rates():
    """
    Fetches real-time USD rates for Argentina from DolarAPI.
    """
    try:
        response = requests.get("https://dolarapi.com/v1/dolares")
        if response.status_code == 200:
            data = response.json()
            rates = {}
            for entry in data:
                # possible casa values: oficial, blue, bolsa (mep), liqui (ccl)
                casa = entry['casa']
                rates[casa] = {
                    "compra": entry['compra'],
                    "venta": entry['venta'],
                    "fecha": entry['fechaActualizacion']
                }
            return rates
        else:
            return None
    except Exception as e:
        print(f"Error fetching dolar rates: {e}")
        return None

def get_m2_valuation(neighborhood):
    """
    Returns estimated m2 value and logic for a given neighborhood in CABA.
    Based on March 2026 data.
    """
    neighborhood = neighborhood.lower().strip()
    
    # Baseline data (USD/m2)
    market_data = {
        "puerto madero": {"avg": 7272, "range": [6500, 8500]},
        "belgrano": {"avg": 2775, "range": [2331, 3219]},
        "barrio norte": {"avg": 3160, "range": [2664, 3663]},
        "recoleta": {"avg": 3100, "range": [2600, 3700]},
        "palermo": {"avg": 3000, "range": [2500, 3800]},
        "nuñez": {"avg": 2800, "range": [2400, 3300]},
        "caballito": {"avg": 2200, "range": [1900, 2500]},
        "villa urquiza": {"avg": 2300, "range": [2000, 2600]},
        "lugano": {"avg": 1097, "range": [900, 1300]},
        "la boca": {"avg": 1552, "range": [1300, 1800]},
    }
    
    if neighborhood in market_data:
        return market_data[neighborhood]
    
    # Fallback/Generic CABA average if neighborhood not found
    return {"avg": 2455, "range": [1800, 3500], "note": "Valor promedio CABA genérico."}

def get_market_summary():
    """
    Synthesizes a short market summary based on current date.
    """
    # In a real scenario, this would fetch from a news API.
    # For now, we return the researched perspective.
    return {
        "global": "S&P 500 volátil. Petróleo Brent elevado por tensiones en Medio Oriente.",
        "argentina": "Merval resiliente. Riesgo país en niveles de tensión pero con activos locales firmes.",
        "real_estate": "CABA estable con recuperación selectiva de precios (marzo 2026)."
    }

if __name__ == "__main__":
    # Test
    print("Dolar Rates:", get_dolar_rates())
    print("Recoleta m2:", get_m2_valuation("Recoleta"))
