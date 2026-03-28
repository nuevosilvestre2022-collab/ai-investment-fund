"""
🏦 AI Investment Fund — Main Orchestrator
Combines Buffett's margin of safety with Lynch's 10-bagger hunting.

Usage:
  python main.py                          # Full analysis: all regions
  python main.py --region north_america   # Single region
  python main.py --mode test              # Quick test with mock data
  python main.py --mode valuation --ticker AAPL  # Valuate a single stock
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

# ─── Banner ───────────────────────────────────────────────────────────────────

BANNER = """
[bold cyan]
 ╔═══════════════════════════════════════════════════════════╗
 ║         🏦  AI INVESTMENT FUND  🏦                        ║
 ║     Buffett's Safety × Lynch's 10-Bagger Ambition        ║
 ╚═══════════════════════════════════════════════════════════╝
[/bold cyan]
"""


def print_banner():
    console.print(BANNER)
    console.print(f"[dim]Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n")


# ─── Modes ────────────────────────────────────────────────────────────────────

def run_full_analysis(regions: list = None, parallel: bool = False):
    """Run the full multi-region analysis and generate portfolio."""
    from crews.regional_crew import run_regional_analysis
    from crews.master_crew import run_master_synthesis
    from config.markets import list_regions

    available_regions = list_regions()
    target_regions = regions if regions else available_regions

    console.print(Panel(
        f"[bold]Running analysis for:[/bold] {', '.join(target_regions)}\n"
        f"[bold]Regions:[/bold] {len(target_regions)} | [bold]Mode:[/bold] Sequential",
        title="📊 Analysis Configuration",
        border_style="cyan",
    ))

    # Run regional analyses
    regional_results = []
    for region in target_regions:
        result = run_regional_analysis(region)
        regional_results.append(result)

        # Save intermediate result
        _save_regional_output(region, result)

    # Master synthesis
    console.print("\n[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")
    console.print("[bold magenta]RUNNING MASTER PORTFOLIO SYNTHESIS[/bold magenta]")
    console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]\n")

    portfolio_result = run_master_synthesis(regional_results)

    # Save and display final portfolio
    _save_portfolio(portfolio_result, regional_results)
    _display_summary(portfolio_result, regional_results)

    return portfolio_result


def run_single_valuation(ticker: str):
    """Valuate a single stock using all methods."""
    from tools.financial_data import get_stock_data
    from tools.valuation import full_valuation
    from config.philosophy import hybrid_score, StockMetrics

    console.print(f"\n[bold cyan]📈 Analyzing {ticker.upper()}...[/bold cyan]")

    data = get_stock_data(ticker.upper())

    if "error" in data:
        console.print(f"[red]Error: {data['error']}[/red]")
        return

    # Display info (data is now flat — no separate fin dict needed)
    _display_stock_info(ticker, data, data)

    # Run valuation
    eps = data.get("eps_ttm", 0) or 0
    bvps = data.get("book_value_per_share", 0) or 0
    fcf = data.get("free_cash_flow", 0) or 0
    pe = data.get("pe_ratio", 0) or 0
    eps_growth = (data.get("eps_growth_3y_cagr", 0) or 0) * 100
    price = data.get("current_price", 0) or 0
    market_cap = data.get("market_cap", 0) or 0
    shares = int(market_cap / price) if price > 0 else 1

    if eps > 0 or fcf > 0:
        val = full_valuation(
            ticker=ticker,
            current_price=price,
            eps=eps,
            book_value_per_share=bvps,
            free_cash_flow=max(fcf, 0),
            shares_outstanding=shares,
            pe_ratio=pe,
            eps_growth_annual_pct=eps_growth,
        )
        _display_valuation(val)

    # Hybrid score
    metrics = StockMetrics(
        ticker=ticker,
        roe=data.get("roe"),
        pe_ratio=pe,
        peg_ratio=data.get("peg_ratio"),
        eps_growth_3y=data.get("eps_growth_3y_cagr"),
        debt_to_equity=data.get("debt_to_equity"),
        free_cash_flow=fcf,
        market_cap=market_cap,
        insider_ownership=data.get("insider_ownership"),
        institutional_ownership=data.get("institution_ownership"),
        dividend_yield=data.get("dividend_yield"),
        net_margin=data.get("net_margin"),
    )

    scores = hybrid_score(metrics)
    _display_scores(scores)

    # Show data quality warnings from cross-validation
    if data.get("warnings"):
        console.print("\n[yellow]📊 Data Cross-Validation Warnings:[/yellow]")
        for w in data["warnings"]:
            console.print(f"  {w}")



def run_test_mode():
    """Quick test with AAPL to verify everything works."""
    console.print("[yellow]Running test mode with AAPL...[/yellow]")
    run_single_valuation("AAPL")
    console.print("\n[green]✓ Test passed — system is working correctly![/green]")


# ─── Display Helpers ──────────────────────────────────────────────────────────

def _display_stock_info(ticker: str, info: dict, fin: dict):
    table = Table(title=f"📊 {ticker} — {info.get('name', ticker)}", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    rows = [
        ("Sector", info.get("sector", "N/A")),
        ("Industry", info.get("industry", "N/A")),
        ("Country", info.get("country", "N/A")),
        ("Current Price", f"${info.get('current_price', 'N/A')}"),
        ("Market Cap", _fmt_large(info.get("market_cap"))),
        ("P/E Ratio", str(round(info.get("pe_ratio", 0) or 0, 2))),
        ("PEG Ratio", str(info.get("peg_ratio", "N/A"))),
        ("ROE", f"{round((info.get('roe') or 0)*100, 1)}%"),
        ("Debt/Equity", str(info.get("debt_to_equity", "N/A"))),
        ("Dividend Yield", f"{round((info.get('div_yield') or 0)*100, 2)}%"),
        ("EPS (TTM)", f"${info.get('eps_ttm', 'N/A')}"),
        ("EPS Growth 3Y CAGR", f"{round((fin.get('eps_growth_3y_cagr') or 0)*100, 1)}%"),
        ("Free Cash Flow", _fmt_large(fin.get("free_cash_flow"))),
        ("Insider Ownership", f"{round((info.get('insider_percent') or 0)*100, 1)}%"),
        ("Analyst Coverage", str(info.get("num_analyst_opinions", 0))),
    ]

    for metric, value in rows:
        table.add_row(metric, str(value))

    console.print(table)


def _display_valuation(val: dict):
    console.print("\n[bold]📐 Valuation Summary:[/bold]")
    table = Table(box=box.SIMPLE)
    table.add_column("Method", style="cyan")
    table.add_column("Intrinsic Value", style="green")
    table.add_column("Margin of Safety", style="yellow")
    table.add_column("Assessment")

    table.add_row("Graham Number", f"${val.get('graham_number', 'N/A')}", val.get('graham_mos', 'N/A'), val.get('graham_mos_label', 'N/A'))
    table.add_row("DCF (10yr)", f"${val.get('dcf_per_share', 'N/A')}", val.get('dcf_mos', 'N/A'), val.get('dcf_mos_label', 'N/A'))
    table.add_row("[bold]BLENDED[/bold]", f"[bold]${val.get('blended_intrinsic_value', 'N/A')}[/bold]", f"[bold]{val.get('blended_mos', 'N/A')}[/bold]", "")

    console.print(table)
    console.print(f"\n  PEG Ratio: {val.get('peg_ratio', 'N/A')} — {val.get('peg_label', 'N/A')}")
    console.print(f"\n  [bold]Overall Verdict:[/bold] {val.get('valuation_summary', 'N/A')}\n")


def _display_scores(scores: dict):
    console.print(Panel(
        f"  [cyan]Buffett Score:[/cyan]  {scores['buffett_score']}/100\n"
        f"  [green]Lynch Score:[/green]   {scores['lynch_score']}/100\n"
        f"  [yellow]Hybrid Score:[/yellow]  {scores['hybrid_score']}/100\n\n"
        f"  10-Bagger Potential: {'✅ YES' if scores['ten_bagger_potential'] else '❌ NO'}\n"
        f"  Moat Type: {scores['moat_type']}\n"
        f"  Lynch Category: {scores['lynch_category']}\n\n"
        f"  [bold]RECOMMENDATION: {scores['recommendation']}[/bold]",
        title="🎯 Investment Scores",
        border_style="green",
    ))


def _display_summary(portfolio: dict, regional: list):
    console.print("\n")
    console.print(Panel(
        f"  ✅ Regions analyzed: {len([r for r in regional if r['status'] == 'success'])}/{len(regional)}\n"
        f"  ❌ Regions failed: {len([r for r in regional if r['status'] == 'error'])}\n"
        f"  📁 Portfolio saved to: output/portfolio.json\n"
        f"  📊 Reports saved to: output/reports/\n\n"
        f"  Run the dashboard: python dashboard/app.py",
        title="✅ Analysis Complete",
        border_style="green",
    ))


def _fmt_large(val) -> str:
    if val is None: return "N/A"
    val = float(val)
    if abs(val) >= 1e12: return f"${val/1e12:.2f}T"
    if abs(val) >= 1e9:  return f"${val/1e9:.2f}B"
    if abs(val) >= 1e6:  return f"${val/1e6:.2f}M"
    return f"${val:,.0f}"


# ─── Save Outputs ─────────────────────────────────────────────────────────────

def _save_regional_output(region: str, result: dict):
    from config.settings import REPORTS_DIR
    output_path = REPORTS_DIR / f"{region}_{datetime.now().strftime('%Y%m%d')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in result.items() if k != "raw"}, f, indent=2, ensure_ascii=False)
    console.print(f"[dim]  Saved: {output_path}[/dim]")


def _save_portfolio(portfolio: dict, regional: list):
    from config.settings import PORTFOLIO_FILE, REPORTS_DIR

    full_report = {
        "timestamp": datetime.now().isoformat(),
        "portfolio": portfolio,
        "regional_analyses": [
            {k: v for k, v in r.items() if k != "raw"}
            for r in regional
        ],
    }

    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)

    # Also save as dated report
    dated_path = REPORTS_DIR / f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(dated_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)


# ─── CLI Entry Point ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="🏦 AI Investment Fund — Buffett + Lynch Multi-Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                              # Full global analysis
  python main.py --region north_america       # Single region
  python main.py --region asia latam          # Multiple specific regions
  python main.py --mode test                  # Quick test (no LLM needed)
  python main.py --mode valuation --ticker AAPL   # Single stock analysis
  python main.py --mode valuation --ticker MSFT TSLA BRK-B  # Multi-stock
        """
    )

    parser.add_argument(
        "--mode",
        choices=["full", "test", "valuation"],
        default="full",
        help="Operation mode",
    )
    parser.add_argument(
        "--region",
        nargs="+",
        choices=["north_america", "europe_north", "europe_south", "asia", "latam", "africa"],
        help="Specific region(s) to analyze",
    )
    parser.add_argument(
        "--ticker",
        nargs="+",
        help="Stock ticker(s) for valuation mode",
    )

    args = parser.parse_args()

    print_banner()

    if args.mode == "test":
        run_test_mode()

    elif args.mode == "valuation":
        if not args.ticker:
            console.print("[red]Error: --ticker required for valuation mode[/red]")
            sys.exit(1)
        for ticker in args.ticker:
            run_single_valuation(ticker.upper())

    elif args.mode == "full":
        run_full_analysis(regions=args.region)


if __name__ == "__main__":
    main()
