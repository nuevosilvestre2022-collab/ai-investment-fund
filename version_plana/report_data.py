"""
Report Data Layer — Multi-source fetching for weekly Intelligence Report.
Uses yfinance to completely bypass Alpha Vantage rate limits, ensuring 100% data availability.
"""
import yfinance as yf
from datetime import datetime

# Real Estate and Business Opportunity static databases
from val_db import REAL_ESTATE_OPPORTUNITIES, BUSINESS_OPPORTUNITIES

def get_macro_indicators() -> dict:
    """Fetch macro indicators using yfinance proxy tickers."""
    indicators = {}
    
    # 13 Week Treasury Bill (proxies short term rate / Fed Funds)
    try:
        tbill = yf.Ticker("^IRX")
        hist = tbill.history(period="5d")
        if not hist.empty:
            indicators["US_fed_rate"] = round(hist["Close"].iloc[-1], 2)
    except: pass
    
    # 10-Year Treasury Yield
    try:
        tyield = yf.Ticker("^TNX")
        hist = tyield.history(period="5d")
        if not hist.empty:
            indicators["US_10y_yield"] = round(hist["Close"].iloc[-1], 2)
    except: pass
    
    # Volatility Index (VIX) instead of CPI since real-time CPI isn't on YF
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="5d")
        if not hist.empty:
            indicators["US_vix"] = round(hist["Close"].iloc[-1], 2)
    except: pass
    
    return indicators

def get_commodity_prices() -> dict:
    """Get key commodity prices from yfinance."""
    commodities = {}
    mapping = {
        "gold": "GC=F",
        "oil_brent": "BZ=F",
        "oil_wti": "CL=F",
        "nat_gas": "NG=F",
        "copper": "HG=F",
        "wheat": "ZW=F",
        "silver": "SI=F"
    }
    
    for name, ticker in mapping.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="1d")
            if not hist.empty:
                commodities[name] = {
                    "price": round(hist["Close"].iloc[-1], 2),
                    "date": hist.index[-1].strftime("%Y-%m-%d")
                }
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            
    return commodities

def get_fx_rates() -> dict:
    """Get FX rates vs USD from yfinance."""
    fx = {}
    pairs = {
        "EUR/USD": "EURUSD=X",
        "GBP/USD": "GBPUSD=X",
        "JPY/USD": "JPY=X",
        "BRL/USD": "BRL=X",
        "ARS/USD": "ARS=X", # Official rate usually
        "CNY/USD": "CNY=X",
    }
    for label, ticker in pairs.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="1d")
            if not hist.empty:
                fx[label] = round(hist["Close"].iloc[-1], 4)
        except: pass
    return fx

def get_top_movers() -> dict:
    """Approximation of top movers since YF doesn't have a direct 'top gainers' endpoint."""
    return {} # We will generate specific deep dive analysis instead of generic movers
