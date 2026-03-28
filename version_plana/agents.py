"""
CrewAI Agent Definitions — AI Investment Fund
Primary LLM: Google Gemini 1.5 Flash (free, works in Argentina)
Fallback: Anthropic Claude Haiku (pay-per-use, for complex reasoning)
"""
import os
from crewai import Agent
from crewai_tools import SerperDevTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic

from settings import (
    GOOGLE_API_KEY, ANTHROPIC_API_KEY,
    PRIMARY_LLM_MODEL, FALLBACK_LLM_MODEL,
)

# ─── LLM Setup ────────────────────────────────────────────────────────────────

def get_gemini_llm(temperature: float = 0.1):
    """Primary LLM: Google Gemini 2.5 Flash (free tier — works in Argentina)"""
    return ChatGoogleGenerativeAI(
        google_api_key=GOOGLE_API_KEY,
        model="gemini-2.5-flash",
        temperature=temperature,
        convert_system_message_to_human=True,
    )

def get_claude_llm(temperature: float = 0.2):
    """Fallback LLM: Claude 3.5 Haiku — for complex reasoning tasks"""
    return ChatAnthropic(
        api_key=ANTHROPIC_API_KEY,
        model=FALLBACK_LLM_MODEL,
        temperature=temperature,
    )

def get_default_llm():
    """Returns best available LLM: Gemini (free) first, Claude as fallback."""
    if GOOGLE_API_KEY and GOOGLE_API_KEY != "your_google_api_key_here":
        return get_gemini_llm()
    elif ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "your_anthropic_api_key_here":
        return get_claude_llm()
    else:
        raise ValueError(
            "No LLM API key found!\n"
            "Get a FREE Google Gemini key at: https://aistudio.google.com/app/apikey\n"
            "Then add GOOGLE_API_KEY=your_key to your .env file."
        )

# Optional web search tool
def get_search_tool():
    serper_key = os.getenv("SERPER_API_KEY", "")
    if serper_key and serper_key != "your_serper_api_key_here":
        return SerperDevTool()
    return None


# ─── Agent Factory ────────────────────────────────────────────────────────────

def create_market_scout(region: str, region_data: dict) -> Agent:
    """
    Market Scout Agent — Peter Lynch inspired.
    Finds under-the-radar stocks in a specific region.
    Lynch: 'Know what you own and why you own it.'
    """
    tools = [t for t in [get_search_tool()] if t]

    return Agent(
        role=f"{region_data['name']} Market Scout",
        goal=(
            f"Identify the most promising investment opportunities in {region_data['name']} "
            f"across exchanges: {', '.join(region_data['exchanges'])}. "
            f"Focus on companies that are undervalued, growing fast, or undiscovered by Wall Street — "
            f"the classic Peter Lynch 10-bagger candidates."
        ),
        backstory=(
            "You are a seasoned equity researcher with deep knowledge of regional markets. "
            "Inspired by Peter Lynch, you believe the best investments are often found in everyday businesses "
            "that institutional investors ignore. You scout for simple, understandable companies "
            "with strong growth stories and reasonable valuations. "
            "Lynch said: 'Go for a business that any idiot can run — because sooner or later, any idiot probably will.'"
        ),
        tools=tools,
        llm=get_default_llm(),
        verbose=True,
        allow_delegation=False,
    )


def create_fundamental_analyst() -> Agent:
    """
    Fundamental Analyst — Warren Buffett style.
    Deep dives into business quality, moat, and intrinsic value.
    """
    return Agent(
        role="Value Investment Analyst (Buffett Style)",
        goal=(
            "Perform deep fundamental analysis on candidate stocks. "
            "Evaluate economic moat, management quality, financial consistency, "
            "and intrinsic value using Graham Number and DCF models. "
            "Calculate margin of safety. Only approve stocks with >= 30% margin of safety."
        ),
        backstory=(
            "You think like Warren Buffett: you look for wonderful businesses at fair prices rather than "
            "fair businesses at wonderful prices. You study the annual reports carefully, check if ROE is "
            "consistently above 15%, free cash flow is positive, and the company has an economic moat "
            "(brand, network effect, switching costs, or cost advantage). "
            "Buffett's rule #1: Never lose money. Rule #2: Never forget rule #1."
        ),
        llm=get_claude_llm() if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "your_anthropic_api_key_here" else get_default_llm(),
        verbose=True,
        allow_delegation=False,
    )


def create_growth_hunter() -> Agent:
    """
    Growth Hunter — Peter Lynch 10-bagger style.
    Hunts for high-growth, under-valued growth companies.
    """
    return Agent(
        role="Growth Stock Hunter (Lynch Style)",
        goal=(
            "Find potential 10-bagger stocks — companies that could grow 10x in value over 5-10 years. "
            "Focus on: PEG ratio < 1.5, EPS growth > 20% annually, insider buying, "
            "small/mid cap with runway for growth, and simple understandable business models."
        ),
        backstory=(
            "You are a growth investor inspired by Peter Lynch's legendary Magellan Fund performance (29.2% annual returns). "
            "You categorize stocks as fast growers, stalwarts, turnarounds, cyclicals, slow growers, or asset plays. "
            "You love finding companies where analysts say 'there's no way this grows 10x' — and proving them wrong. "
            "Lynch's PEG ratio is your primary tool: a stock growing 20% annually with a P/E of 15 has a PEG of 0.75 — a bargain. "
            "You are not afraid of volatility. You are afraid of missing the next Walmart or Home Depot at 10x."
        ),
        llm=get_default_llm(),
        verbose=True,
        allow_delegation=False,
    )


def create_risk_evaluator() -> Agent:
    """
    Risk Evaluator — Guardian of capital and margin of safety.
    Combines Buffett's conservatism with practical position sizing.
    """
    return Agent(
        role="Risk Manager & Margin of Safety Guardian",
        goal=(
            "Evaluate risk of each investment opportunity. "
            "Verify margin of safety >= 30%. Check country risk, currency risk, liquidity, "
            "debt levels, and concentration risk. "
            "Recommend maximum position size for each stock. "
            "Protect capital above all — Buffett's primary principle."
        ),
        backstory=(
            "You are a conservative risk manager who has read Graham's 'The Intelligent Investor' cover to cover. "
            "You know that the biggest investing mistake is permanent loss of capital. "
            "You ensure no position is too large, debt is manageable, the business has staying power, "
            "and the price paid includes an adequate margin of safety. "
            "Your motto: 'An investment operation is one which, upon thorough analysis, promises safety of principal and adequate return.' — Benjamin Graham"
        ),
        llm=get_default_llm(),
        verbose=True,
        allow_delegation=False,
    )


def create_macro_analyst() -> Agent:
    """
    Macro Analyst — evaluates geopolitical and economic context per region.
    """
    tools = [t for t in [get_search_tool()] if t]

    return Agent(
        role="Global Macro & Geopolitical Analyst",
        goal=(
            "Analyze the macroeconomic environment of each region: interest rates, inflation, "
            "GDP growth, currency trends, geopolitical risks, and sector tailwinds/headwinds. "
            "Provide a MACRO SCORE (1-10) for each region and flag any red flags that could "
            "impair investment returns regardless of individual stock quality."
        ),
        backstory=(
            "You are a top-down macro analyst who understands that even the best stocks can suffer "
            "in the wrong macro environment. You monitor central bank policies, commodity cycles, "
            "trade flows, and political risk. You know that Buffett himself says he doesn't try to "
            "predict macro, but you ensure we avoid regions with extreme risk: hyperinflation, "
            "nationalization risk, or severe currency devaluation (hello, Argentina)."
        ),
        tools=tools,
        llm=get_default_llm(),
        verbose=True,
        allow_delegation=False,
    )


def create_portfolio_manager() -> Agent:
    """
    Portfolio Manager — orchestrates the final portfolio allocation.
    Synthesizes all regional analyses into a global portfolio.
    """
    return Agent(
        role="Chief Portfolio Manager",
        goal=(
            "Synthesize investment recommendations from all regional crews into a final diversified portfolio. "
            "Allocate capital across regions based on opportunity quality, risk levels, and diversification rules. "
            "Ensure no single stock exceeds 10% of portfolio. "
            "Generate a clear, actionable investment report with buy recommendations, "
            "target prices, expected returns, and position sizes."
        ),
        backstory=(
            "You are the Chief Investment Officer of the AI Investment Fund. You have the hybrid philosophy: "
            "Buffett's discipline (margin of safety, quality businesses, long-term thinking) combined with "
            "Lynch's ambition (find 10-baggers before anyone else, know your companies deeply). "
            "You balance safety and upside. You never let one bet ruin the portfolio. "
            "You generate clear weekly/monthly reports that a non-expert can understand and act upon."
        ),
        llm=get_claude_llm() if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "your_anthropic_api_key_here" else get_default_llm(),
        verbose=True,
        allow_delegation=True,
    )
