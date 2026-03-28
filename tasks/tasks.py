"""
CrewAI Tasks — Investment Fund Analysis Pipeline
Tasks are the work items assigned to agents.
"""
from crewai import Task
from crewai import Agent
from typing import List


def create_scouting_task(agent: Agent, region: str, seed_tickers: List[str]) -> Task:
    """Task: Scout a region for investment opportunities."""
    return Task(
        description=(
            f"Scout the {region} market for investment opportunities.\n\n"
            f"Starting tickers for reference: {', '.join(seed_tickers[:15])}\n\n"
            f"Your job:\n"
            f"1. Analyze each starting ticker briefly\n"
            f"2. Identify which sectors are showing strength in {region} right now\n"
            f"3. Look for companies that are:\n"
            f"   - Growing >15% EPS annually\n"
            f"   - Under-covered by analysts (<10 analyst ratings)\n"
            f"   - In growing industries\n"
            f"   - Reasonably priced (P/E < 30 or PEG < 1.5)\n"
            f"4. Return a list of 10-15 top candidates with a brief reason for each\n\n"
            f"Format output as a structured list: TICKER | Company Name | Reason | Category (Lynch type)"
        ),
        agent=agent,
        expected_output=(
            "A structured list of 10-15 investment candidates for this region. "
            "Each candidate must have: ticker, company name, reason for selection, "
            "Lynch category (fast_grower/stalwart/turnaround/etc), and brief business description."
        ),
    )


def create_fundamental_analysis_task(agent: Agent, candidates_output: str, region: str) -> Task:
    """Task: Deep fundamental analysis on scouted candidates."""
    return Task(
        description=(
            f"Perform deep Buffett-style fundamental analysis on the candidates from {region}.\n\n"
            f"Candidates from scouting: {candidates_output[:1000]}\n\n"
            f"For the top 8 candidates:\n"
            f"1. Evaluate economic moat (brand/network/switching costs/cost advantage)\n"
            f"2. Check financial consistency (ROE > 15%, positive FCF, stable margins)\n"
            f"3. Assess management quality and capital allocation\n"
            f"4. Verify debt is manageable (Debt/Equity < 1.5)\n"
            f"5. Assign a BUFFETT SCORE (0-100)\n"
            f"6. Estimate intrinsic value and calculate Margin of Safety\n"
            f"7. Flag any RED FLAGS\n\n"
            f"Buffett says: 'It's far better to buy a wonderful company at a fair price "
            f"than a fair company at a wonderful price.'"
        ),
        agent=agent,
        expected_output=(
            "Fundamental analysis report for top candidates. "
            "For each stock: Buffett Score (0-100), moat type, key financial metrics, "
            "estimated intrinsic value, margin of safety %, red flags, and PASS/FAIL verdict."
        ),
    )


def create_growth_hunting_task(agent: Agent, candidates_output: str, region: str) -> Task:
    """Task: Identify Lynch-style 10-bagger potential."""
    return Task(
        description=(
            f"Hunt for 10-bagger potential among {region} candidates using Peter Lynch's methodology.\n\n"
            f"Candidates: {candidates_output[:1000]}\n\n"
            f"For each candidate:\n"
            f"1. Calculate or estimate PEG ratio (P/E ÷ EPS growth rate)\n"
            f"2. Assess 10-bagger potential: market cap < $2B? addressable market >> market cap?\n"
            f"3. Check insider ownership (does management have skin in the game?)\n"
            f"4. Identify the growth story: what will drive 10x growth?\n"
            f"5. Assign LYNCH SCORE (0-100)\n"
            f"6. Categorize: fast_grower / stalwart / turnaround / cyclical / asset_play\n\n"
            f"Lynch: 'All you need for a lifetime of successful investing is a few big winners, "
            f"and the pluses from those will overwhelm the minuses from the stocks that don't work out.'"
        ),
        agent=agent,
        expected_output=(
            "Growth analysis report. For each stock: Lynch Score, PEG ratio, "
            "10-bagger potential (YES/NO + reason), Lynch category, "
            "5-year return target, and growth story summary."
        ),
    )


def create_risk_evaluation_task(agent: Agent, fundamental_output: str, growth_output: str) -> Task:
    """Task: Evaluate risk and assign position sizes."""
    return Task(
        description=(
            f"Evaluate risk and assign position sizes for approved investment candidates.\n\n"
            f"Fundamental analysis results: {fundamental_output[:800]}\n\n"
            f"Growth analysis results: {growth_output[:800]}\n\n"
            f"For approved stocks (Buffett score >= 40 OR Lynch score >= 50):\n"
            f"1. Verify Margin of Safety >= 20% (must have some discount)\n"
            f"2. Assess: Country risk, Currency risk, Liquidity risk, Sector concentration\n"
            f"3. Recommend position size: Conservative (2-3%), Moderate (4-6%), or Aggressive (7-10%)\n"
            f"4. Flag any deal breakers that override positive scores\n"
            f"5. Produce final APPROVED list with position size recommendations\n\n"
            f"Rule: No single stock should exceed 10% of total portfolio."
        ),
        agent=agent,
        expected_output=(
            "Risk evaluation report with: final approved stock list, "
            "risk level for each (LOW/MEDIUM/HIGH), recommended position size (%), "
            "deal breakers if any, and overall region risk assessment."
        ),
    )


def create_macro_analysis_task(agent: Agent, region: str, region_data: dict) -> Task:
    """Task: Analyze macro environment for a region."""
    return Task(
        description=(
            f"Analyze the current macroeconomic environment for {region_data['name']}.\n\n"
            f"Countries: {', '.join(region_data['countries'])}\n"
            f"Currency: {region_data['currency']}\n"
            f"Benchmark: {region_data['benchmark_ticker']}\n\n"
            f"Analyze:\n"
            f"1. Economic cycle phase (expansion/peak/contraction/trough)\n"
            f"2. Interest rate environment and central bank stance\n"
            f"3. Inflation trends\n"
            f"4. Currency stability and trend vs USD\n"
            f"5. Geopolitical risks\n"
            f"6. Sector tailwinds (what industries benefit NOW in this region)\n"
            f"7. Sector headwinds (what to avoid)\n\n"
            f"Output: MACRO SCORE (1-10), risk flags, and recommended sector tilts."
        ),
        agent=agent,
        expected_output=(
            "Macro analysis report with: Macro Score (1-10), economic cycle phase, "
            "top 3 sector tailwinds, top 3 risks, currency assessment, "
            "and overall investment climate (FAVORABLE/NEUTRAL/UNFAVORABLE)."
        ),
    )


def create_portfolio_synthesis_task(agent: Agent, all_regional_outputs: List[str]) -> Task:
    """Task: Final portfolio synthesis across all regions."""
    combined = "\n\n---\n\n".join(all_regional_outputs[:5])  # Limit context size

    return Task(
        description=(
            f"Synthesize investment recommendations from ALL regional analyses into a final portfolio.\n\n"
            f"Regional analyses:\n{combined[:3000]}\n\n"
            f"Your job:\n"
            f"1. Select the BEST 15-25 stocks across all regions\n"
            f"2. Ensure diversification: max 40% any single region, max 30% any sector\n"
            f"3. Target portfolio composition:\n"
            f"   - 40% High-conviction Buffett plays (quality + MOS >= 30%)\n"
            f"   - 40% Lynch growth plays (PEG < 1.5, high growth)\n"
            f"   - 20% Speculative 10-bagger candidates (small positions 2-3%)\n"
            f"4. Assign final position sizes (must sum to ~100%)\n"
            f"5. For each position: entry price zone, 12-month target, 3-5 year target\n"
            f"6. Write an executive summary of the portfolio thesis\n\n"
            f"Remember: Preservation of capital first, then growth."
        ),
        agent=agent,
        expected_output=(
            "FINAL PORTFOLIO REPORT including: "
            "Executive Summary (200 words), "
            "Portfolio table (ticker, name, region, weight%, entry zone, 1yr target, 3yr target, thesis), "
            "Risk metrics, and monthly monitoring triggers."
        ),
    )
