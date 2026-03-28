"""
Market regions configuration — exchanges, currencies, benchmark indices.
"""

MARKETS = {
    "north_america": {
        "name": "North America",
        "countries": ["USA", "Canada", "Mexico"],
        "exchanges": ["NYSE", "NASDAQ", "TSX", "BMV"],
        "currency": "USD",
        "benchmark_ticker": "^GSPC",  # S&P 500
        "risk_level": "low",
        "timezone": "America/New_York",
        # Sample tickers to seed the screener (agent will expand these)
        "seed_tickers": [
            # US Large Caps
            "AAPL", "MSFT", "GOOGL", "AMZN", "BRK-B", "JNJ", "JPM", "V", "WMT",
            # US Mid/Small Caps (Lynch-style candidates)
            "CELH", "IIPR", "INMD", "ACLS", "BOOT", "MODG",
            # Canada
            "SHOP.TO", "CNR.TO", "RY.TO",
            # Mexico
            "WALMEX.MX", "FEMSA.MX",
        ],
    },

    "europe_north": {
        "name": "Northern Europe",
        "countries": ["UK", "Germany", "France", "Netherlands", "Sweden", "Norway", "Denmark"],
        "exchanges": ["LSE", "XETRA", "OMX"],
        "currency": "EUR/GBP",
        "benchmark_ticker": "^N100",  # Euronext 100
        "risk_level": "low",
        "timezone": "Europe/London",
        "seed_tickers": [
            # UK
            "SHEL.L", "AZN.L", "ULVR.L", "HSBA.L",
            # Germany
            "SAP.DE", "VOW3.DE", "SIE.DE", "MBG.DE",
            # Nordic
            "NZYM-B.CO", "NOVO-B.CO", "VOLV-B.ST", "ATCO-A.ST",
        ],
    },

    "europe_south": {
        "name": "Southern Europe",
        "countries": ["Spain", "Italy", "Portugal", "Greece"],
        "exchanges": ["IBEX", "MIB", "PSI", "ATHEX"],
        "currency": "EUR",
        "benchmark_ticker": "^IBEX",  # IBEX 35
        "risk_level": "medium",
        "timezone": "Europe/Madrid",
        "seed_tickers": [
            # Spain
            "ITX.MC", "SAN.MC", "TEF.MC", "IBE.MC", "REP.MC",
            # Italy
            "ENI.MI", "ENEL.MI", "ISP.MI", "UCG.MI",
            # Portugal
            "EDP.LS", "GALP.LS",
        ],
    },

    "asia": {
        "name": "Asia Pacific",
        "countries": ["Japan", "China", "India", "South Korea", "Taiwan", "Singapore"],
        "exchanges": ["TSE", "SSE", "SZSE", "NSE", "KOSPI", "TWSE", "SGX"],
        "currency": "Multi (JPY/CNY/INR/KRW/TWD/SGD)",
        "benchmark_ticker": "^N225",  # Nikkei 225
        "risk_level": "medium",
        "timezone": "Asia/Tokyo",
        "seed_tickers": [
            # Japan
            "7203.T", "6758.T", "9984.T", "6861.T",  # Toyota, Sony, Softbank, Keyence
            # India (ADR equivalents)
            "INFY", "WIT", "HDB", "IBN",
            # Taiwan
            "TSM",  # TSMC
            # South Korea
            "005930.KS",  # Samsung
            # China (Hong Kong listed)
            "0700.HK", "9988.HK", "3690.HK",  # Tencent, Alibaba, Meituan
        ],
    },

    "latam": {
        "name": "Latin America",
        "countries": ["Brazil", "Argentina", "Chile", "Colombia", "Peru"],
        "exchanges": ["BOVESPA", "MERVAL", "BCS", "BVC", "BVL"],
        "currency": "Multi (BRL/ARS/CLP/COP/PEN)",
        "benchmark_ticker": "EWZ",  # iShares MSCI Brazil ETF (proxy)
        "risk_level": "high",
        "timezone": "America/Sao_Paulo",
        "seed_tickers": [
            # Brazil
            "VALE3.SA", "PETR4.SA", "ITUB4.SA", "WEGE3.SA", "RENT3.SA",
            # Chile
            "FALABELLA.SN", "COLBUN.SN",
            # ADRs
            "PBR", "GGB", "SQM", "MercadoLibre".replace("MercadoLibre", "MELI"),
        ],
    },

    "africa": {
        "name": "Africa & Middle East",
        "countries": ["South Africa", "Nigeria", "Kenya", "Egypt", "Morocco"],
        "exchanges": ["JSE", "NGX", "NSE-KE", "EGX"],
        "currency": "Multi (ZAR/NGN/KES/EGP/MAD)",
        "benchmark_ticker": "AFK",  # Market Vectors Africa (ETF proxy)
        "risk_level": "high",
        "timezone": "Africa/Johannesburg",
        "seed_tickers": [
            # South Africa (JSE via ADR/ETF)
            "NPN.JO", "AGL.JO", "SOL.JO", "SBK.JO",
            # ADRs
            "GOLD", "MTN.JO",
        ],
    },
}

def get_market(region: str) -> dict:
    """Get market configuration for a region."""
    return MARKETS.get(region, {})

def list_regions() -> list:
    """List all available regions."""
    return list(MARKETS.keys())

def get_all_seed_tickers() -> list:
    """Get all seed tickers across all regions."""
    all_tickers = []
    for market in MARKETS.values():
        all_tickers.extend(market.get("seed_tickers", []))
    return all_tickers
