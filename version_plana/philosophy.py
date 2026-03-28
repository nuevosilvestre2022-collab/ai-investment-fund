"""
Investment Philosophy Module — Hybrid Buffett + Lynch Rules
Encodes the decision criteria from:
  - Warren Buffett (Berkshire Letters, The Warren Buffett Way)
  - Peter Lynch (One Up on Wall Street, Beating the Street, 25 Rules)
  - Benjamin Graham (The Intelligent Investor)
"""
from dataclasses import dataclass
from typing import Optional


# ─── Lynch Stock Categories (from One Up on Wall Street) ─────────────────────
LYNCH_CATEGORIES = {
    "slow_growers":   "Large, mature companies; steady dividends; 2-5% EPS growth",
    "stalwarts":      "Large companies; 10-12% EPS growth; protection in recessions",
    "fast_growers":   "Small, aggressive; 20-25%+ EPS growth; 10-bagger candidates",
    "cyclicals":      "Sales/profits expand & contract with economy (auto, airline, steel)",
    "turnarounds":    "Beaten-down companies with recovery potential; zero or negative earnings",
    "asset_plays":    "Companies with hidden/undervalued assets (real estate, patents, cash)",
}

# ─── Moat Categories (Buffett's Economic Moat Framework) ───────────────────
MOAT_TYPES = {
    "brand":        {"description": "Powerful consumer brand (Coca-Cola, Apple)",       "score": 5},
    "network":      {"description": "Network effect (Visa, MSFT, social media)",         "score": 5},
    "switching":    {"description": "High switching costs (Oracle, SAP, Adobe)",         "score": 4},
    "cost":         {"description": "Structural cost advantage (Walmart, Amazon)",       "score": 4},
    "efficient":    {"description": "Efficient scale (local monopoly, niche markets)",   "score": 3},
    "intangible":   {"description": "Patents, licenses, regulatory approval",            "score": 3},
    "none":         {"description": "No identifiable moat",                              "score": 0},
}

# ─── Buffett Checklist (from The Warren Buffett Way + Letters) ───────────────
BUFFETT_CHECKLIST = [
    # Business Fundamentals
    {"criterion": "Consistent earnings power (10+ years)",             "weight": 15},
    {"criterion": "ROE > 15% consistently",                            "weight": 15},
    {"criterion": "Positive free cash flow",                           "weight": 15},
    {"criterion": "Economic moat (competitive advantage)",             "weight": 20},
    {"criterion": "Low debt (Debt/Equity < 1)",                        "weight": 10},
    # Management
    {"criterion": "Honest, shareholder-friendly management",           "weight": 10},
    {"criterion": "Rational capital allocation (buybacks / dividends)", "weight": 5},
    # Price / Value
    {"criterion": "Margin of safety >= 30% to intrinsic value",        "weight": 10},
]

# ─── Lynch Checklist (from 25 Golden Rules + One Up on Wall Street) ──────────
LYNCH_CHECKLIST = [
    # Business Simplicity
    {"criterion": "Business simple enough to explain in 2 minutes",    "weight": 10},
    {"criterion": "Under-followed by Wall Street analysts",            "weight": 10},
    # Growth Metrics
    {"criterion": "EPS growth rate > 20% (fast-growers) or PEG < 1.5","weight": 20},
    {"criterion": "Company growing into new markets (expandable niche)","weight": 10},
    {"criterion": "Insider buying (management owns stock)",            "weight": 10},
    # Financial Health
    {"criterion": "Strong balance sheet (cash > debt ideally)",        "weight": 10},
    {"criterion": "Inventory growing slower than sales",               "weight": 10},
    # Story
    {"criterion": "Compelling growth story still intact",              "weight": 10},
    {"criterion": "P/E reasonable relative to growth (PEG principle)", "weight": 10},
]

# ─── Red Flags (Both Buffett & Lynch warn against these) ────────────────────
RED_FLAGS = [
    "Company name ends in .com or has 'AI' trend-chasing rebranding",
    "Insiders selling large blocks of stock",
    "Debt growing faster than earnings",
    "Inventory growing faster than sales (Lynch warning)",
    "Company in industry with no pricing power",
    "Recent auditor change or accounting irregularities",
    "CEO making big diversifying acquisitions outside core business",
    "Operating in country with nationalization risk",
]

# ─── 10-Bagger Criteria (Lynch's x10 candidates) ─────────────────────────────
TEN_BAGGER_CRITERIA = {
    "market_cap_max_usd": 2_000_000_000,   # Under $2B (room to grow 10x)
    "eps_growth_min_annual": 0.20,          # 20%+ EPS growth per year
    "peg_max": 1.0,                         # PEG <= 1
    "sector_tailwind": True,                # Growing industry
    "institutional_ownership_max": 0.50,    # Less than 50% institutional (undiscovered)
    "insider_ownership_min": 0.05,          # Insiders own >= 5%
}

# ─── Scoring Functions ────────────────────────────────────────────────────────

@dataclass
class StockMetrics:
    ticker: str
    roe: Optional[float] = None
    pe_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None
    eps_growth_3y: Optional[float] = None
    debt_to_equity: Optional[float] = None
    free_cash_flow: Optional[float] = None
    market_cap: Optional[float] = None
    insider_ownership: Optional[float] = None
    institutional_ownership: Optional[float] = None
    dividend_yield: Optional[float] = None
    revenue_growth_3y: Optional[float] = None
    net_margin: Optional[float] = None
    moat_type: str = "none"
    intrinsic_value: Optional[float] = None
    current_price: Optional[float] = None
    lynch_category: str = "unknown"


def buffett_score(m: StockMetrics) -> int:
    """
    Returns 0-100 score based on Buffett's investment criteria.
    Higher = better Buffett-style investment.
    """
    score = 0

    # ROE (15 pts)
    if m.roe is not None:
        if m.roe >= 0.20:   score += 15
        elif m.roe >= 0.15: score += 10
        elif m.roe >= 0.12: score += 5

    # Free Cash Flow (20 pts)
    if m.free_cash_flow is not None:
        if m.free_cash_flow > 0: score += 20

    # Debt/Equity (15 pts)
    if m.debt_to_equity is not None:
        if m.debt_to_equity <= 0.5:  score += 15
        elif m.debt_to_equity <= 1.0: score += 10
        elif m.debt_to_equity <= 1.5: score += 5

    # Economic Moat (25 pts)
    moat_score = MOAT_TYPES.get(m.moat_type, MOAT_TYPES["none"])["score"]
    score += moat_score * 5  # 0, 15, 20, or 25

    # Margin of Safety (25 pts)
    if m.intrinsic_value and m.current_price and m.current_price > 0:
        mos = (m.intrinsic_value - m.current_price) / m.intrinsic_value
        if mos >= 0.40:   score += 25
        elif mos >= 0.30: score += 18
        elif mos >= 0.20: score += 10
        elif mos >= 0.10: score += 5

    return min(score, 100)


def lynch_score(m: StockMetrics) -> int:
    """
    Returns 0-100 score based on Peter Lynch's investment criteria.
    Higher = better Lynch-style growth investment.
    """
    score = 0

    # PEG Ratio (25 pts) — Lynch's favorite metric
    if m.peg_ratio is not None:
        if m.peg_ratio <= 0.5:   score += 25
        elif m.peg_ratio <= 1.0: score += 20
        elif m.peg_ratio <= 1.5: score += 12
        elif m.peg_ratio <= 2.0: score += 5

    # EPS Growth (25 pts)
    if m.eps_growth_3y is not None:
        if m.eps_growth_3y >= 0.30:  score += 25
        elif m.eps_growth_3y >= 0.20: score += 18
        elif m.eps_growth_3y >= 0.15: score += 12
        elif m.eps_growth_3y >= 0.10: score += 6

    # Insider Ownership (15 pts) — Lynch loves when mgmt owns shares
    if m.insider_ownership is not None:
        if m.insider_ownership >= 0.20:  score += 15
        elif m.insider_ownership >= 0.10: score += 10
        elif m.insider_ownership >= 0.05: score += 5

    # Under-discovered (15 pts) — Lynch likes stocks analysts ignore
    if m.institutional_ownership is not None:
        if m.institutional_ownership <= 0.30:  score += 15
        elif m.institutional_ownership <= 0.50: score += 10
        elif m.institutional_ownership <= 0.70: score += 5

    # Lynch Category bonus (20 pts) — fast growers & turnarounds get bonus
    category_bonus = {
        "fast_growers": 20,
        "turnarounds":  15,
        "asset_plays":  12,
        "stalwarts":    8,
        "cyclicals":    6,
        "slow_growers": 2,
    }
    score += category_bonus.get(m.lynch_category, 5)

    return min(score, 100)


def hybrid_score(m: StockMetrics) -> dict:
    """
    Combines Buffett + Lynch scores into a final investment score.
    Returns dict with all scores and recommendation.
    """
    b_score = buffett_score(m)
    l_score = lynch_score(m)

    # Weighted: 50% Buffett safety + 50% Lynch growth
    combined = int(b_score * 0.50 + l_score * 0.50)

    # Margin of safety gate (hard rule from Buffett)
    margin_of_safety = 0.0
    if m.intrinsic_value and m.current_price and m.current_price > 0:
        margin_of_safety = (m.intrinsic_value - m.current_price) / m.intrinsic_value

    # 10-bagger potential check
    ten_bagger_potential = (
        (m.market_cap or 999e9) <= TEN_BAGGER_CRITERIA["market_cap_max_usd"] and
        (m.eps_growth_3y or 0) >= TEN_BAGGER_CRITERIA["eps_growth_min_annual"] and
        (m.peg_ratio or 99) <= TEN_BAGGER_CRITERIA["peg_max"]
    )

    # Final recommendation
    if combined >= 70 and margin_of_safety >= 0.30:
        recommendation = "STRONG BUY 🟢"
    elif combined >= 55 and margin_of_safety >= 0.20:
        recommendation = "BUY 🟡"
    elif combined >= 40:
        recommendation = "WATCH 🔵"
    else:
        recommendation = "AVOID 🔴"

    return {
        "ticker": m.ticker,
        "buffett_score": b_score,
        "lynch_score": l_score,
        "hybrid_score": combined,
        "margin_of_safety": round(margin_of_safety * 100, 1),
        "ten_bagger_potential": ten_bagger_potential,
        "recommendation": recommendation,
        "lynch_category": m.lynch_category,
        "moat_type": m.moat_type,
    }
