"""
Regional Crew Builder — creates a CrewAI crew for a specific market region.
Each regional crew runs: Scout → Fundamental Analysis → Growth Hunting → Risk Evaluation.
"""
from crewai import Crew, Process
from agents.agents import (
    create_market_scout,
    create_fundamental_analyst,
    create_growth_hunter,
    create_risk_evaluator,
    create_macro_analyst,
)
from tasks.tasks import (
    create_scouting_task,
    create_fundamental_analysis_task,
    create_growth_hunting_task,
    create_risk_evaluation_task,
    create_macro_analysis_task,
)
from config.markets import MARKETS
from rich.console import Console

console = Console()


def build_regional_crew(region: str) -> Crew:
    """
    Build a full analysis crew for a given region.
    Region must be one of: north_america, europe_north, europe_south, asia, latam, africa
    """
    region_data = MARKETS.get(region)
    if not region_data:
        raise ValueError(f"Unknown region: {region}. Available: {list(MARKETS.keys())}")

    console.print(f"\n[bold cyan]🌍 Building crew for: {region_data['name']}[/bold cyan]")

    # ── Create Agents ──────────────────────────────────────────────────────────
    scout = create_market_scout(region, region_data)
    fundamental = create_fundamental_analyst()
    growth = create_growth_hunter()
    risk = create_risk_evaluator()

    # ── Create Tasks (sequential pipeline) ────────────────────────────────────
    scout_task = create_scouting_task(
        agent=scout,
        region=region_data["name"],
        seed_tickers=region_data["seed_tickers"],
    )

    fundamental_task = create_fundamental_analysis_task(
        agent=fundamental,
        candidates_output="{scouting_output}",  # will be filled by CrewAI context
        region=region_data["name"],
    )
    fundamental_task.context = [scout_task]

    growth_task = create_growth_hunting_task(
        agent=growth,
        candidates_output="{scouting_output}",
        region=region_data["name"],
    )
    growth_task.context = [scout_task]

    risk_task = create_risk_evaluation_task(
        agent=risk,
        fundamental_output="{fundamental_output}",
        growth_output="{growth_output}",
    )
    risk_task.context = [fundamental_task, growth_task]

    # ── Build Crew ─────────────────────────────────────────────────────────────
    crew = Crew(
        agents=[scout, fundamental, growth, risk],
        tasks=[scout_task, fundamental_task, growth_task, risk_task],
        process=Process.sequential,
        verbose=True,
        memory=False,  # Keep costs low — no memory storage
    )

    return crew


def build_macro_crew(region: str) -> Crew:
    """Build a standalone macro analysis crew for a region."""
    region_data = MARKETS.get(region)
    macro_agent = create_macro_analyst()
    macro_task = create_macro_analysis_task(macro_agent, region, region_data)

    return Crew(
        agents=[macro_agent],
        tasks=[macro_task],
        process=Process.sequential,
        verbose=True,
    )


def run_regional_analysis(region: str) -> dict:
    """
    Run the full analysis pipeline for a region.
    Returns: dict with crew output and region metadata.
    """
    console.print(f"\n[bold green]▶ Starting analysis for region: {region}[/bold green]")

    try:
        crew = build_regional_crew(region)
        result = crew.kickoff()

        return {
            "region": region,
            "region_name": MARKETS[region]["name"],
            "status": "success",
            "output": str(result),
            "raw": result,
        }
    except Exception as e:
        console.print(f"[red]✗ Error in {region} crew: {e}[/red]")
        return {
            "region": region,
            "region_name": MARKETS.get(region, {}).get("name", region),
            "status": "error",
            "output": str(e),
            "raw": None,
        }
