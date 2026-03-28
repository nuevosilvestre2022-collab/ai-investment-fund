"""
Master Crew — Synthesizes outputs from all regional crews into the final portfolio.
"""
from crewai import Crew, Process
from agents.agents import create_portfolio_manager, create_macro_analyst
from tasks.tasks import create_portfolio_synthesis_task
from rich.console import Console

console = Console()


def build_master_crew(regional_outputs: list) -> Crew:
    """
    Build the master portfolio crew that takes all regional analyses
    and produces the final investment portfolio.
    """
    pm = create_portfolio_manager()
    macro = create_macro_analyst()

    # Prepare context from all regions
    formatted_outputs = []
    for r in regional_outputs:
        if r["status"] == "success":
            formatted_outputs.append(
                f"=== {r['region_name'].upper()} ===\n{r['output']}"
            )

    if not formatted_outputs:
        raise ValueError("No successful regional analyses to synthesize.")

    synthesis_task = create_portfolio_synthesis_task(
        agent=pm,
        all_regional_outputs=formatted_outputs,
    )

    return Crew(
        agents=[pm, macro],
        tasks=[synthesis_task],
        process=Process.sequential,
        verbose=True,
    )


def run_master_synthesis(regional_outputs: list) -> dict:
    """
    Run the master synthesis to produce the final portfolio.
    """
    console.print("\n[bold magenta]🏆 MASTER PORTFOLIO SYNTHESIS[/bold magenta]")
    console.print(f"Synthesizing {len([r for r in regional_outputs if r['status'] == 'success'])} regional analyses...")

    try:
        crew = build_master_crew(regional_outputs)
        result = crew.kickoff()
        return {
            "status": "success",
            "portfolio": str(result),
        }
    except Exception as e:
        console.print(f"[red]Master crew error: {e}[/red]")
        return {"status": "error", "portfolio": str(e)}
