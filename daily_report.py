import datetime
from market_data import get_dolar_rates, get_market_summary

def generate_daily_report():
    """
    Generates the formatted 9 AM report for the Executive Second Brain.
    """
    ahora = datetime.datetime.now()
    fecha_str = ahora.strftime('%d/%m/%Y')
    
    fx = get_dolar_rates()
    mkt = get_market_summary()
    
    # Official, Blue, MEP, CCL
    oficial = fx.get('oficial', {}).get('venta', 'N/A')
    blue = fx.get('blue', {}).get('venta', 'N/A')
    mep = fx.get('bolsa', {}).get('venta', 'N/A')
    ccl = fx.get('contadoconliqui', {}).get('venta', 'N/A')
    brecha = 0
    if isinstance(blue, (int, float)) and isinstance(oficial, (int, float)):
        brecha = ((blue / oficial) - 1) * 100

    report = f"""
🚀 *REPORTE EJECUTIVO - {fecha_str}*

*A) Panorama Global:*
• {mkt['global']}

*B) Argentina (Clave):*
• {mkt['argentina']}

*C) Oportunidades de Inversión:*
• Arbitraje MEP/Blue monitoreado. 
• Activos energéticos con buen upside local.

*D) Mercado Inmobiliario:*
• {mkt['real_estate']}
• Demanda sostenida en 2 ambientes (Palermo/Belgrano).

*E) Bolsa:*
• Merval estable. S&P 500 con cautela.

*F) Dólar:*
• Oficial: ${oficial}
• Blue: ${blue}
• MEP: ${mep}
• CCL: ${ccl}
• Brecha: {brecha:.1f}%

*G) Estrategias:*
• Warren Buffett: Mantener liquidez para ineficiencias.
• Peter Lynch: Mirar consumo local y energía.

*H) Oportunidades Tácticas:*
• "Rulo" MEP hoy: { "Atractivo" if brecha > 5 else "Marginal" }.
• Oportunidad en m2 pozo en zonas de derrame.

*100% ACCIONABLE.*
"""
    return report.strip()

if __name__ == "__main__":
    print(generate_daily_report())
