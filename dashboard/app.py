"""
Flask Dashboard API — AI Investment Fund
Serves the portfolio data and triggers analysis runs.
"""
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# ─── Path helpers ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
REPORTS_DIR = OUTPUT_DIR / "reports"
PORTFOLIO_FILE = OUTPUT_DIR / "portfolio.json"


def read_portfolio():
    if PORTFOLIO_FILE.exists():
        with open(PORTFOLIO_FILE, encoding="utf-8") as f:
            return json.load(f)
    return None


def list_reports():
    if not REPORTS_DIR.exists():
        return []
    return sorted(
        [f.name for f in REPORTS_DIR.glob("*.json")],
        reverse=True,
    )


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/portfolio")
def get_portfolio():
    data = read_portfolio()
    if data is None:
        return jsonify({"error": "No portfolio found. Run main.py first."}), 404
    return jsonify(data)


@app.route("/api/reports")
def get_reports():
    return jsonify({"reports": list_reports()})


@app.route("/api/valuation")
def quick_valuation():
    """Quick single-ticker valuation via API."""
    ticker = request.args.get("ticker", "").upper()
    if not ticker:
        return jsonify({"error": "ticker parameter required"}), 400

    try:
        import sys
        sys.path.insert(0, str(BASE_DIR))
        from tools.financial_data import get_stock_data
        from tools.valuation import full_valuation

        data = get_stock_data(ticker, verbose=False)

        if "error" in data:
            return jsonify({"error": data["error"]}), 400

        eps = data.get("eps_ttm", 0) or 0
        bvps = data.get("book_value_per_share", 0) or 0
        fcf = data.get("free_cash_flow", 0) or 0
        pe = data.get("pe_ratio", 0) or 0
        eps_growth = (data.get("eps_growth_3y_cagr", 0) or 0) * 100
        price = data.get("current_price", 0) or 0
        market_cap = data.get("market_cap", 0) or 0
        shares = int(market_cap / price) if price > 0 else 1

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

        return jsonify({
            "info": data,
            "financials": data,
            "valuation": val,
            "timestamp": datetime.now().isoformat(),
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/status")
def status():
    return jsonify({
        "status": "running",
        "portfolio_exists": PORTFOLIO_FILE.exists(),
        "reports_count": len(list_reports()),
        "timestamp": datetime.now().isoformat(),
    })


if __name__ == "__main__":
    print("\n🏦 AI Investment Fund Dashboard")
    print("   Open: http://localhost:5000\n")
    app.run(debug=True, port=5000)
