"""
Valuation Engine — Graham Number, DCF, Margin of Safety, PEG
Implements the quantitative side of Buffett + Lynch valuations.
"""
import math
from typing import Optional
from settings import DCF_DISCOUNT_RATE, DCF_GROWTH_YEARS, TERMINAL_GROWTH_RATE


# ─── Graham Number (Benjamin Graham / Buffett foundation) ────────────────────

def graham_number(eps: float, book_value_per_share: float) -> Optional[float]:
    """
    Graham Number = sqrt(22.5 * EPS * BVPS)
    The upper bound of a stock's fair value per Graham/Buffett.
    A stock trading BELOW this is potentially undervalued.
    """
    if eps <= 0 or book_value_per_share <= 0:
        return None
    return round(math.sqrt(22.5 * eps * book_value_per_share), 2)


# ─── DCF Valuation (Buffett's preferred intrinsic value method) ───────────────

def dcf_intrinsic_value(
    free_cash_flow: float,
    growth_rate_high: float = 0.15,
    growth_rate_terminal: float = None,
    discount_rate: float = None,
    projection_years: int = None,
) -> Optional[float]:
    """
    Discounted Cash Flow valuation.
    
    Args:
        free_cash_flow: Most recent annual FCF in dollars
        growth_rate_high: Expected FCF growth rate for projection period
        growth_rate_terminal: Terminal growth rate after projection period
        discount_rate: Required rate of return (Buffett typically uses 10%)
        projection_years: Years to project (default: 10)
    
    Returns:
        Intrinsic value per... (it's a total company value, divide by shares outstanding)
    """
    if free_cash_flow <= 0:
        return None

    discount_rate = discount_rate or DCF_DISCOUNT_RATE
    growth_rate_terminal = growth_rate_terminal or TERMINAL_GROWTH_RATE
    projection_years = projection_years or DCF_GROWTH_YEARS

    pv_of_cash_flows = 0.0
    current_fcf = free_cash_flow

    for year in range(1, projection_years + 1):
        current_fcf *= (1 + growth_rate_high)
        pv = current_fcf / ((1 + discount_rate) ** year)
        pv_of_cash_flows += pv

    # Terminal value (Gordon Growth Model)
    terminal_fcf = current_fcf * (1 + growth_rate_terminal)
    terminal_value = terminal_fcf / (discount_rate - growth_rate_terminal)
    pv_terminal = terminal_value / ((1 + discount_rate) ** projection_years)

    total_intrinsic_value = pv_of_cash_flows + pv_terminal
    return round(total_intrinsic_value, 2)


def dcf_per_share(
    free_cash_flow: float,
    shares_outstanding: int,
    growth_rate_high: float = 0.15,
    **kwargs
) -> Optional[float]:
    """DCF value per share."""
    total = dcf_intrinsic_value(free_cash_flow, growth_rate_high, **kwargs)
    if total is None or shares_outstanding <= 0:
        return None
    return round(total / shares_outstanding, 2)


# ─── Margin of Safety (Buffett's #1 rule) ────────────────────────────────────

def margin_of_safety(intrinsic_value: float, current_price: float) -> Optional[float]:
    """
    Margin of Safety = (Intrinsic Value - Current Price) / Intrinsic Value
    Positive = stock is trading at a DISCOUNT (good)
    Negative = stock is overvalued (avoid)
    Buffett aims for >= 30% margin of safety.
    """
    if intrinsic_value <= 0 or current_price <= 0:
        return None
    mos = (intrinsic_value - current_price) / intrinsic_value
    return round(mos, 4)


def mos_label(mos: float) -> str:
    """Human-readable margin of safety label."""
    if mos >= 0.50:  return "🟢 Excellent (>50%)"
    if mos >= 0.40:  return "🟢 Very Good (40-50%)"
    if mos >= 0.30:  return "🟡 Good (30-40%) — Buffett minimum"
    if mos >= 0.20:  return "🟡 Acceptable (20-30%)"
    if mos >= 0.10:  return "🔴 Thin (10-20%)"
    if mos >= 0:     return "🔴 Very Thin (<10%)"
    return "❌ Overvalued — trading above intrinsic value"


# ─── PEG Ratio (Peter Lynch's signature metric) ──────────────────────────────

def peg_ratio(pe: float, earnings_growth_rate_pct: float) -> Optional[float]:
    """
    PEG = P/E ÷ Annual EPS Growth Rate (%)
    Lynch's rule: PEG < 1 = undervalued, PEG > 1.5 = overvalued for growth stocks.
    
    Args:
        pe: Price/Earnings ratio
        earnings_growth_rate_pct: Annual EPS growth in PERCENT (e.g., 20 for 20%)
    """
    if pe <= 0 or earnings_growth_rate_pct <= 0:
        return None
    return round(pe / earnings_growth_rate_pct, 2)


def peg_label(peg: float) -> str:
    """Lynch's PEG interpretation."""
    if peg <= 0.5:   return "🟢 Exceptional bargain (<0.5)"
    if peg <= 1.0:   return "🟢 Undervalued (<1.0) — Lynch sweet spot"
    if peg <= 1.5:   return "🟡 Fair value (1.0-1.5)"
    if peg <= 2.0:   return "🔴 Slightly overvalued (1.5-2.0)"
    return "❌ Overvalued for its growth rate (>2.0)"


# ─── Combined Valuation Summary ───────────────────────────────────────────────

def full_valuation(
    ticker: str,
    current_price: float,
    eps: float,
    book_value_per_share: float,
    free_cash_flow: float,
    shares_outstanding: int,
    pe_ratio: float,
    eps_growth_annual_pct: float,
    fcf_growth_rate: float = 0.12,
) -> dict:
    """
    Run all valuation methods and return a comprehensive summary.
    """
    # Graham Number
    g_num = graham_number(eps, book_value_per_share)
    g_mos = margin_of_safety(g_num, current_price) if g_num else None

    # DCF Value
    dcf = dcf_per_share(free_cash_flow, shares_outstanding, growth_rate_high=fcf_growth_rate)
    dcf_mos = margin_of_safety(dcf, current_price) if dcf else None

    # Blended intrinsic value (average of available methods)
    values = [v for v in [g_num, dcf] if v is not None]
    blended_iv = round(sum(values) / len(values), 2) if values else None
    blended_mos = margin_of_safety(blended_iv, current_price) if blended_iv else None

    # PEG
    peg = peg_ratio(pe_ratio, eps_growth_annual_pct)

    return {
        "ticker": ticker,
        "current_price": current_price,
        "graham_number": g_num,
        "graham_mos": f"{round(g_mos*100,1)}%" if g_mos is not None else "N/A",
        "graham_mos_label": mos_label(g_mos) if g_mos is not None else "N/A",
        "dcf_per_share": dcf,
        "dcf_mos": f"{round(dcf_mos*100,1)}%" if dcf_mos is not None else "N/A",
        "dcf_mos_label": mos_label(dcf_mos) if dcf_mos is not None else "N/A",
        "blended_intrinsic_value": blended_iv,
        "blended_mos": f"{round(blended_mos*100,1)}%" if blended_mos is not None else "N/A",
        "blended_mos_raw": blended_mos,
        "peg_ratio": peg,
        "peg_label": peg_label(peg) if peg is not None else "N/A",
        "valuation_summary": _valuation_verdict(blended_mos, peg),
    }


def _valuation_verdict(mos: Optional[float], peg: Optional[float]) -> str:
    """Combined verdict from MOS + PEG."""
    score = 0
    if mos is not None:
        if mos >= 0.30: score += 2
        elif mos >= 0.20: score += 1
        elif mos < 0: score -= 2

    if peg is not None:
        if peg <= 1.0: score += 2
        elif peg <= 1.5: score += 1
        elif peg > 2.0: score -= 1

    if score >= 4:   return "🟢 STRONG BUY — Both value and growth criteria met"
    elif score >= 2: return "🟡 BUY — Good opportunity"
    elif score == 1: return "🔵 WATCH — Monitor for better entry"
    elif score < 0:  return "🔴 AVOID — Overvalued"
    else:            return "⚪ NEUTRAL — Insufficient data"
