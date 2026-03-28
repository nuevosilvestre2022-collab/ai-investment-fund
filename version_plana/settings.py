"""
AI Investment Fund - Configuration Settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── LLM Configuration ───────────────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# Primary LLM: Google Gemini 1.5 Flash (FREE — works in Argentina)
PRIMARY_LLM_PROVIDER = "google"
PRIMARY_LLM_MODEL = "gemini-1.5-flash"  # Free: 15 RPM, 1M tokens/day

# Fallback LLM: Claude 3.5 Haiku (complex reasoning, pay-per-use)
FALLBACK_LLM_PROVIDER = "anthropic"
FALLBACK_LLM_MODEL = "claude-3-5-haiku-20241022"

# ─── Investment Parameters ───────────────────────────────────────────────────
INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", 10000))
RISK_LEVEL = os.getenv("RISK_LEVEL", "moderate")  # conservative / moderate / aggressive
MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", 0.10))  # 10% max per stock
MIN_MARGIN_OF_SAFETY = float(os.getenv("MIN_MARGIN_OF_SAFETY", 0.30))  # 30% minimum

# ─── Portfolio Allocation by Region ──────────────────────────────────────────
REGION_ALLOCATION = {
    "north_america": 0.35,   # 35% - USA / Canada / Mexico
    "asia":          0.25,   # 25% - Japan / China / India / Korea
    "europe_north":  0.15,   # 15% - UK / Germany / Nordics
    "europe_south":  0.10,   # 10% - Spain / Italy / Portugal
    "latam":         0.10,   # 10% - Brazil / Argentina / Chile
    "africa":        0.05,   # 5%  - South Africa / Nigeria / Kenya
}

# ─── Screening Thresholds (Hybrid Buffett-Lynch) ──────────────────────────────
SCREENING_FILTERS = {
    # Buffett-style
    "min_roe": 0.12,               # ROE >= 12%
    "max_debt_to_equity": 1.5,     # Debt/Equity <= 1.5
    "max_pe_ratio": 35,            # P/E <= 35

    # Lynch-style
    "max_peg_ratio": 1.5,          # PEG <= 1.5
    "min_eps_growth_3y": 0.10,     # EPS growth >= 10% per year

    # Hybrid
    "min_market_cap_usd": 100e6,   # Min $100M market cap (avoid micro-cap traps)
    "min_buffett_score": 40,       # Minimum Buffett score to pass
    "min_lynch_score": 40,         # Minimum Lynch score to pass
    "min_hybrid_score": 50,        # Minimum combined score
}

# ─── Output Paths ─────────────────────────────────────────────────────────────
import pathlib
BASE_DIR = pathlib.Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
REPORTS_DIR = OUTPUT_DIR / "reports"
PORTFOLIO_FILE = OUTPUT_DIR / "portfolio.json"

OUTPUT_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# ─── Analysis Settings ────────────────────────────────────────────────────────
MAX_CANDIDATES_PER_REGION = 30    # Max stocks to analyze per region
TOP_PICKS_PER_REGION = 5          # Top final picks per region
DCF_DISCOUNT_RATE = 0.10          # 10% discount rate for DCF
DCF_GROWTH_YEARS = 10             # Years of growth projection
TERMINAL_GROWTH_RATE = 0.03       # 3% terminal growth
