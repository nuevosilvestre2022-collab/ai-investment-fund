"""
Multi-Source Financial Data Provider
Fetches from multiple free APIs and cross-validates the results.

Sources (all free tiers, no subscription):
  1. yfinance        — Broad coverage, historical prices, basic fundamentals (no key needed)
  2. Financial Modeling Prep (FMP) — Deep fundamentals: income statement, balance sheet, ratios
  3. Alpha Vantage   — Secondary validation for EPS, income, overview data

Strategy:
  - yfinance is primary for price/market data (fast, no rate limits on basics)
  - FMP is primary for accounting data (income statement, FCF, ROE)
  - Alpha Vantage cross-validates key numbers when FMP unavailable
  - Values are cross-validated; large discrepancies are flagged

Free tier limits (per day):
  - yfinance:   Unlimited (unofficially ~2000 req/session)
  - FMP:        250 calls/day with free key
  - Alpha Vantage: 25 calls/day with free key
"""
import os
import time
import requests
import yfinance as yf
from typing import Optional
from rich.console import Console
from dotenv import load_dotenv

load_dotenv()
console = Console()

FMP_API_KEY = os.getenv("FMP_API_KEY", "")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "")

FMP_BASE = "https://financialmodelingprep.com/api/v3"
AV_BASE  = "https://www.alphavantage.co/query"


# ─── Low-level fetchers ───────────────────────────────────────────────────────

def _fmp_get(endpoint: str, params: dict = None) -> Optional[dict | list]:
    """Fetch from FMP API. Returns None on error."""
    if not FMP_API_KEY or FMP_API_KEY == "your_fmp_api_key_here":
        return None
    try:
        url = f"{FMP_BASE}/{endpoint}"
        p = {"apikey": FMP_API_KEY, **(params or {})}
        r = requests.get(url, params=p, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        console.print(f"[dim yellow]FMP error ({endpoint}): {e}[/dim yellow]")
        return None


def _av_get(params: dict) -> Optional[dict]:
    """Fetch from Alpha Vantage. Returns None on error."""
    if not ALPHA_VANTAGE_KEY or ALPHA_VANTAGE_KEY == "your_alpha_vantage_key_here":
        return None
    try:
        p = {"apikey": ALPHA_VANTAGE_KEY, **params}
        r = requests.get(AV_BASE, params=p, timeout=10)
        r.raise_for_status()
        data = r.json()
        # AV returns error inside JSON
        if "Note" in data or "Information" in data:
            console.print("[dim yellow]Alpha Vantage rate limit reached[/dim yellow]")
            return None
        return data
    except Exception as e:
        console.print(f"[dim yellow]Alpha Vantage error: {e}[/dim yellow]")
        return None


# ─── Source 1: yfinance ───────────────────────────────────────────────────────

def _yf_get_info(ticker: str) -> dict:
    """Fetch stock info from yfinance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            return {}
        return info
    except Exception as e:
        console.print(f"[dim yellow]yfinance error ({ticker}): {e}[/dim yellow]")
        return {}


def _yf_get_financials(ticker: str) -> dict:
    """Get income statement / cash flow / balance from yfinance."""
    try:
        stock = yf.Ticker(ticker)
        result = {}

        # Cash flow
        cf = stock.cashflow
        if not cf.empty:
            for row_name in ["Operating Cash Flow", "Free Cash Flow", "Capital Expenditure"]:
                if row_name in cf.index:
                    result[row_name.lower().replace(" ", "_")] = float(cf.loc[row_name].iloc[0])

        # Income statement
        inc = stock.financials
        if not inc.empty:
            if "Net Income" in inc.index:
                result["net_income_history"] = [float(v) for v in inc.loc["Net Income"].dropna().tolist()[:4]]
            if "Total Revenue" in inc.index:
                result["revenue_history"] = [float(v) for v in inc.loc["Total Revenue"].dropna().tolist()[:4]]

        # Balance sheet
        bal = stock.balance_sheet
        if not bal.empty:
            if "Total Debt" in bal.index:
                result["total_debt"] = float(bal.loc["Total Debt"].iloc[0])

        return result
    except Exception as e:
        console.print(f"[dim yellow]yfinance financials error ({ticker}): {e}[/dim yellow]")
        return {}


# ─── Source 2: Financial Modeling Prep (FMP) ─────────────────────────────────

def _fmp_get_profile(ticker: str) -> dict:
    """Get company profile from FMP."""
    data = _fmp_get(f"profile/{ticker}")
    if not data or not isinstance(data, list) or len(data) == 0:
        return {}
    return data[0]


def _fmp_get_ratios(ticker: str) -> dict:
    """Get financial ratios from FMP (TTM = trailing twelve months)."""
    data = _fmp_get(f"ratios-ttm/{ticker}")
    if not data or not isinstance(data, list) or len(data) == 0:
        return {}
    return data[0]


def _fmp_get_income(ticker: str) -> list:
    """Get last 4 years of income statements from FMP."""
    data = _fmp_get(f"income-statement/{ticker}", {"limit": 4})
    return data if isinstance(data, list) else []


def _fmp_get_cashflow(ticker: str) -> list:
    """Get last 4 years of cash flow from FMP."""
    data = _fmp_get(f"cash-flow-statement/{ticker}", {"limit": 4})
    return data if isinstance(data, list) else []


def _fmp_get_key_metrics(ticker: str) -> dict:
    """Get key metrics (TTM) from FMP."""
    data = _fmp_get(f"key-metrics-ttm/{ticker}")
    if not data or not isinstance(data, list) or len(data) == 0:
        return {}
    return data[0]


# ─── Source 3: Alpha Vantage ──────────────────────────────────────────────────

def _av_get_overview(ticker: str) -> dict:
    """Get company overview from Alpha Vantage."""
    data = _av_get({"function": "OVERVIEW", "symbol": ticker})
    return data if data else {}


def _av_get_income(ticker: str) -> dict:
    """Get annual income statement from Alpha Vantage."""
    data = _av_get({"function": "INCOME_STATEMENT", "symbol": ticker})
    return data if data else {}


# ─── Cross-validation helper ──────────────────────────────────────────────────

def _cross_validate(yf_val, fmp_val, av_val, label: str, tolerance: float = 0.20) -> tuple:
    """
    Compare values from multiple sources. Flag if discrepancy > tolerance (20%).
    Returns (best_value, confidence, warning_message)
    """
    values = [(v, src) for v, src in [
        (yf_val, "yfinance"),
        (fmp_val, "FMP"),
        (av_val, "AlphaVantage")
    ] if v is not None and v != 0]

    if not values:
        return None, "no_data", None

    if len(values) == 1:
        return values[0][0], "single_source", None

    # Check for large discrepancies
    nums = [v for v, _ in values]
    min_v, max_v = min(nums), max(nums)
    spread = abs(max_v - min_v) / abs(max_v) if max_v != 0 else 0

    warning = None
    if spread > tolerance:
        sources_str = ", ".join([f"{s}={v:.2f}" for v, s in values])
        warning = f"⚠️  {label} discrepancy ({spread:.0%}): {sources_str}"

    # Prefer FMP > yfinance > AV for fundamental data
    for preferred in [fmp_val, yf_val, av_val]:
        if preferred is not None:
            return preferred, "multi_source", warning

    return values[0][0], "multi_source", warning


# ─── Main Public API ──────────────────────────────────────────────────────────

def get_stock_data(ticker: str, verbose: bool = True) -> dict:
    """
    Fetch comprehensive stock data from all available sources.
    Cross-validates key metrics and flags discrepancies.

    Returns a unified dict with all the data needed for Buffett/Lynch analysis.
    """
    if verbose:
        console.print(f"[cyan]>> Fetching {ticker} from multiple sources...[/cyan]")

    # ── Fetch from all sources ────────────────────────────────────────────────
    yf_info   = _yf_get_info(ticker)
    yf_fin    = _yf_get_financials(ticker)
    fmp_prof  = _fmp_get_profile(ticker)
    fmp_rat   = _fmp_get_ratios(ticker)
    fmp_inc   = _fmp_get_income(ticker)
    fmp_cf    = _fmp_get_cashflow(ticker)
    fmp_km    = _fmp_get_key_metrics(ticker)
    av_ov     = _av_get_overview(ticker)

    sources_used = []
    if yf_info:      sources_used.append("yfinance")
    if fmp_prof:     sources_used.append("FMP")
    if av_ov:        sources_used.append("AlphaVantage")

    if verbose:
        console.print(f"[dim]  Sources: {', '.join(sources_used) or 'none'}[/dim]")

    if not sources_used:
        return {"ticker": ticker, "error": "No data found from any source"}

    warnings = []

    # ── Price & Market Cap ────────────────────────────────────────────────────
    price_yf  = yf_info.get("currentPrice") or yf_info.get("regularMarketPrice")
    price_fmp = fmp_prof.get("price")
    price, _, w = _cross_validate(price_yf, price_fmp, None, "price", tolerance=0.02)
    if w: warnings.append(w)

    market_cap_yf  = yf_info.get("marketCap")
    market_cap_fmp = fmp_prof.get("mktCap")
    market_cap, _, _ = _cross_validate(market_cap_yf, market_cap_fmp, None, "market_cap")

    # ── P/E Ratio ─────────────────────────────────────────────────────────────
    pe_yf  = yf_info.get("trailingPE")
    pe_fmp = fmp_rat.get("peRatioTTM")
    pe_av  = float(av_ov["PERatio"]) if av_ov.get("PERatio") and av_ov["PERatio"] != "None" else None
    pe, _, w = _cross_validate(pe_yf, pe_fmp, pe_av, "P/E ratio", tolerance=0.15)
    if w: warnings.append(w)

    # ── EPS ───────────────────────────────────────────────────────────────────
    eps_yf  = yf_info.get("trailingEps")
    eps_av  = float(av_ov["EPS"]) if av_ov.get("EPS") and av_ov["EPS"] != "None" else None
    eps_fmp = fmp_prof.get("eps")
    eps, _, w = _cross_validate(eps_yf, eps_fmp, eps_av, "EPS", tolerance=0.15)
    if w: warnings.append(w)

    # ── ROE ───────────────────────────────────────────────────────────────────
    roe_yf  = yf_info.get("returnOnEquity")
    roe_fmp_raw = fmp_rat.get("returnOnEquityTTM")
    roe_fmp = roe_fmp_raw  # FMP already in decimal
    roe_av  = float(av_ov["ReturnOnEquityTTM"]) if av_ov.get("ReturnOnEquityTTM") and av_ov["ReturnOnEquityTTM"] != "None" else None
    roe, _, w = _cross_validate(roe_yf, roe_fmp, roe_av, "ROE")
    if w: warnings.append(w)

    # ── Free Cash Flow ────────────────────────────────────────────────────────
    fcf_yf = yf_fin.get("free_cash_flow")
    fcf_fmp = fmp_cf[0].get("freeCashFlow") if fmp_cf else None
    fcf, _, w = _cross_validate(fcf_yf, fcf_fmp, None, "FCF")
    if w: warnings.append(w)

    # ── PEG Ratio ─────────────────────────────────────────────────────────────
    peg_yf  = yf_info.get("pegRatio")
    peg_fmp = fmp_km.get("pegRatioTTM")
    peg_av  = float(av_ov["PEGRatio"]) if av_ov.get("PEGRatio") and av_ov["PEGRatio"] != "None" else None
    peg, _, w = _cross_validate(peg_yf, peg_fmp, peg_av, "PEG ratio")
    if w: warnings.append(w)

    # ── Debt/Equity ───────────────────────────────────────────────────────────
    de_yf  = (yf_info.get("debtToEquity") or 0) / 100  # yf gives it as %, convert
    de_fmp = fmp_rat.get("debtEquityRatioTTM")
    de, _, _ = _cross_validate(de_yf, de_fmp, None, "Debt/Equity")

    # ── EPS Growth (3Y CAGR) ──────────────────────────────────────────────────
    eps_growth = None
    # From yfinance net income history
    ni = yf_fin.get("net_income_history", [])
    if len(ni) >= 4 and ni[-1] and ni[0] and ni[-1] > 0 and ni[0] > 0:
        eps_growth = (ni[0] / ni[-1]) ** (1/3) - 1

    # Cross-check with FMP income statements
    if fmp_inc and len(fmp_inc) >= 4:
        ni_fmp = [s.get("netIncome", 0) for s in fmp_inc[:4]]
        if ni_fmp[-1] and ni_fmp[0] and ni_fmp[-1] > 0 and ni_fmp[0] > 0:
            eps_growth_fmp = (ni_fmp[0] / ni_fmp[-1]) ** (1/3) - 1
            if eps_growth is None:
                eps_growth = eps_growth_fmp
            elif abs(eps_growth - eps_growth_fmp) > 0.10:
                warnings.append(f"⚠️  EPS growth discrepancy: yfinance={eps_growth:.1%}, FMP={eps_growth_fmp:.1%}")

    # Book value / share
    bvps_yf  = yf_info.get("bookValue")
    bvps_fmp = fmp_km.get("bookValuePerShareTTM")
    bvps, _, _ = _cross_validate(bvps_yf, bvps_fmp, None, "Book Value/Share")

    # Insider / institution ownership
    insider_yf  = yf_info.get("heldPercentInsiders")
    insider_fmp = fmp_km.get("insiderOwnershipTTM")
    insider, _, _ = _cross_validate(insider_yf, insider_fmp, None, "insider ownership")

    # ── Build unified result ──────────────────────────────────────────────────
    result = {
        "ticker":          ticker,
        "name":            yf_info.get("longName") or fmp_prof.get("companyName") or av_ov.get("Name") or ticker,
        "sector":          yf_info.get("sector") or fmp_prof.get("sector") or av_ov.get("Sector", "Unknown"),
        "industry":        yf_info.get("industry") or fmp_prof.get("industry") or av_ov.get("Industry", "Unknown"),
        "country":         yf_info.get("country") or fmp_prof.get("country") or av_ov.get("Country", "Unknown"),
        "currency":        yf_info.get("currency") or fmp_prof.get("currency", "USD"),
        "exchange":        yf_info.get("exchange") or fmp_prof.get("exchangeShortName", ""),
        "description":     (yf_info.get("longBusinessSummary") or fmp_prof.get("description") or "")[:400],

        # Pricing
        "current_price":   price,
        "market_cap":      market_cap,
        "52w_high":        yf_info.get("fiftyTwoWeekHigh") or fmp_prof.get("range", "").split("-")[-1] if fmp_prof else None,
        "52w_low":         yf_info.get("fiftyTwoWeekLow"),
        "beta":            yf_info.get("beta") or float(av_ov.get("Beta", 0) or 0),

        # Core ratios (cross-validated)
        "pe_ratio":        round(pe, 2) if pe else None,
        "forward_pe":      yf_info.get("forwardPE"),
        "peg_ratio":       round(peg, 2) if peg else None,
        "price_to_book":   yf_info.get("priceToBook") or fmp_km.get("priceToBookRatioTTM"),
        "ev_to_ebitda":    yf_info.get("enterpriseToEbitda") or fmp_km.get("evToEBITDATTM"),

        # Profitability (cross-validated)
        "eps_ttm":         round(eps, 4) if eps else None,
        "eps_forward":     yf_info.get("forwardEps"),
        "roe":             round(roe, 4) if roe else None,
        "roa":             yf_info.get("returnOnAssets") or fmp_rat.get("returnOnAssetsTTM"),
        "net_margin":      yf_info.get("profitMargins") or fmp_rat.get("netProfitMarginTTM"),
        "gross_margin":    yf_info.get("grossMargins") or fmp_rat.get("grossProfitMarginTTM"),
        "operating_margin":yf_info.get("operatingMargins") or fmp_rat.get("operatingProfitMarginTTM"),

        # Balance sheet
        "debt_to_equity":  round(de, 4) if de else None,
        "current_ratio":   yf_info.get("currentRatio") or fmp_rat.get("currentRatioTTM"),
        "book_value_per_share": round(bvps, 4) if bvps else None,
        "total_debt":      yf_fin.get("total_debt"),

        # Cash flow (cross-validated)
        "free_cash_flow":  fcf,
        "operating_cash_flow": yf_fin.get("operating_cash_flow"),

        # Growth
        "eps_growth_3y_cagr":  round(eps_growth, 4) if eps_growth else None,
        "revenue_growth":      yf_info.get("revenueGrowth") or fmp_rat.get("revenueGrowthTTM"),
        "earnings_growth":     yf_info.get("earningsGrowth"),

        # Ownership
        "dividend_yield":      yf_info.get("dividendYield") or fmp_rat.get("dividendYieldTTM"),
        "insider_ownership":   round(insider, 4) if insider else None,
        "institution_ownership": yf_info.get("heldPercentInstitutions"),

        # Analyst
        "analyst_target":      yf_info.get("targetMeanPrice") or fmp_prof.get("dcf"),
        "num_analysts":        yf_info.get("numberOfAnalystOpinions", 0),

        # Meta
        "sources_used":        sources_used,
        "data_confidence":     "high" if len(sources_used) >= 2 else "medium" if len(sources_used) == 1 else "none",
        "warnings":            warnings,
    }

    if warnings and verbose:
        for w in warnings:
            console.print(f"  {w}")

    confidence_icon = "🟢" if result["data_confidence"] == "high" else "🟡"
    if verbose:
        console.print(f"  {confidence_icon} Data confidence: {result['data_confidence']} ({len(sources_used)} sources)")

    return result


def get_price_history(ticker: str, years: int = 5) -> dict:
    """Fetch price history + returns. yfinance is best for this."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=f"{years}y")
        if hist.empty:
            return {"ticker": ticker, "error": "No price history"}

        start_price = hist["Close"].iloc[0]
        end_price   = hist["Close"].iloc[-1]
        total_return = (end_price - start_price) / start_price
        annual_return = (1 + total_return) ** (1 / years) - 1

        return {
            "ticker":           ticker,
            "start_price":      round(float(start_price), 2),
            "current_price":    round(float(end_price), 2),
            "total_return_pct": round(total_return * 100, 2),
            "annual_return_pct":round(annual_return * 100, 2),
            "years":            years,
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}
