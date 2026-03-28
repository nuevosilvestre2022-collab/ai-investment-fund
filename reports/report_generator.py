"""
Weekly PDF Report Generator — PowerBI-style Investment Intelligence Report

Generates a professional PDF covering:
  1. Executive Summary & Market Pulse
  2. Global Stock Markets (6 regions)
  3. Commodities & Currencies
  4. Top Movers of the Week
  5. Real Estate Opportunities Matrix
  6. Business / Entrepreneurship Opportunities
  7. AI-Generated Investment Picks (from portfolio crews)

Uses: ReportLab (PDF), Alpha Vantage (data), yfinance (markets)
"""
import os
import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from tools.report_data import (
    get_macro_indicators, get_commodity_prices, get_fx_rates,
    get_top_movers, REAL_ESTATE_OPPORTUNITIES, BUSINESS_OPPORTUNITIES
)

# ─── Constants ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent          # fondo_ia/
REPORTS_DIR = BASE_DIR / "output" / "reports" / "weekly"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Dark theme color palette (PowerBI-inspired)
C_BG        = colors.HexColor("#0a0e1a")
C_NAVY      = colors.HexColor("#111827")
C_BLUE      = colors.HexColor("#3b82f6")
C_PURPLE    = colors.HexColor("#8b5cf6")
C_GREEN     = colors.HexColor("#10b981")
C_RED       = colors.HexColor("#ef4444")
C_GOLD      = colors.HexColor("#f59e0b")
C_GRAY      = colors.HexColor("#6b7280")
C_LGRAY     = colors.HexColor("#e5e7eb")
C_WHITE     = colors.white
C_DARK_CARD = colors.HexColor("#1f2937")

WEEK_STR = datetime.now().strftime("%Y-W%V")
DATE_STR = datetime.now().strftime("%d %B %Y")


# ─── Style Helpers ────────────────────────────────────────────────────────────

def get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "ReportTitle",
        fontName="Helvetica-Bold",
        fontSize=28,
        textColor=C_WHITE,
        alignment=TA_CENTER,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "ReportSubtitle",
        fontName="Helvetica",
        fontSize=13,
        textColor=C_BLUE,
        alignment=TA_CENTER,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "SectionHeader",
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=C_BLUE,
        spaceBefore=14,
        spaceAfter=8,
        borderPad=4,
    ))
    styles.add(ParagraphStyle(
        "CardLabel",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=C_GRAY,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        "CardValue",
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=C_WHITE,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        "Body",
        fontName="Helvetica",
        fontSize=9,
        textColor=C_LGRAY,
        spaceAfter=4,
        leading=13,
    ))
    styles.add(ParagraphStyle(
        "SmallGray",
        fontName="Helvetica",
        fontSize=8,
        textColor=C_GRAY,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=C_WHITE,
    ))
    styles.add(ParagraphStyle(
        "Opportunity",
        fontName="Helvetica",
        fontSize=9,
        textColor=C_LGRAY,
        leading=12,
    ))
    styles.add(ParagraphStyle(
        "Tag",
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=C_BLUE,
    ))
    return styles


def _score_color(score: int) -> colors.HexColor:
    if score >= 85: return C_GREEN
    if score >= 70: return C_GOLD
    return C_RED


def _risk_color(risk: str) -> colors.HexColor:
    risk = risk.lower()
    if "low" in risk:    return C_GREEN
    if "medium" in risk: return C_GOLD
    return C_RED


# ─── Section Builders ─────────────────────────────────────────────────────────

def build_cover_page(styles, week_str: str) -> list:
    """Page 1: Cover with title, date and exec summary placeholder."""
    elements = []

    # Title block (dark background effect via table)
    title_data = [[
        Paragraph("AI INVESTMENT FUND", styles["ReportTitle"]),
    ]]
    title_table = Table(title_data, colWidths=[17*cm])
    title_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_NAVY),
        ("TOPPADDING", (0,0), (-1,-1), 24),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
        ("ROUNDEDCORNERS", (0,0), (-1,-1), [8,8,8,8]),
    ]))
    elements.append(Spacer(1, 1.5*cm))
    elements.append(title_table)
    elements.append(Spacer(1, 0.3*cm))

    subtitle_data = [[
        Paragraph("WEEKLY GLOBAL INTELLIGENCE REPORT", styles["ReportSubtitle"]),
    ]]
    elements.append(Table(subtitle_data, colWidths=[17*cm]))
    elements.append(Spacer(1, 0.2*cm))

    date_para = Paragraph(f"Week {week_str}  |  {DATE_STR}", ParagraphStyle(
        "DateStyle", fontName="Helvetica", fontSize=11, textColor=C_GRAY, alignment=TA_CENTER
    ))
    elements.append(date_para)
    elements.append(Spacer(1, 0.8*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=C_BLUE, spaceAfter=12))

    # What's inside
    toc = [
        ["1.", "Global Market Pulse", "Market performance across 6 regions + key movers"],
        ["2.", "Commodities & Currencies", "Gold, Oil, Gas, Copper, Wheat + FX rates"],
        ["3.", "Macro Indicators", "Fed rate, CPI, Treasury yields, unemployment"],
        ["4.", "Top Stock Opportunities", "Buffett + Lynch hybrid picks this week"],
        ["5.", "Real Estate Opportunities", "Best countries to buy property right now"],
        ["6.", "Business Opportunities", "Sectors and countries ripe for entrepreneurs"],
        ["7.", "Risk Monitor", "Regional risks and portfolio alerts"],
    ]

    toc_table = Table(
        [[Paragraph(r[0], styles["SmallGray"]),
          Paragraph(r[1], styles["CardLabel"]),
          Paragraph(r[2], styles["Body"])]
         for r in toc],
        colWidths=[0.8*cm, 5*cm, 11.2*cm]
    )
    toc_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_DARK_CARD),
        ("LINEBELOW", (0,0), (-1,-2), 0.3, C_GRAY),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [C_DARK_CARD, C_NAVY]),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
    ]))
    elements.append(toc_table)
    elements.append(PageBreak())
    return elements


def build_kpi_cards(styles, macro: dict, movers: dict) -> list:
    """KPI cards row: Fed Rate, CPI, 10Y Yield, Unemployment."""
    elements = []
    elements.append(Paragraph("1. GLOBAL MARKET PULSE", styles["SectionHeader"]))

    cards = [
        ("FED RATE", macro.get("US_fed_rate", "N/A"), "%", C_BLUE),
        ("US CPI", macro.get("US_cpi", "N/A"), "%", C_GOLD),
        ("10Y TREASURY", macro.get("US_10y_yield", "N/A"), "%", C_PURPLE),
        ("UNEMPLOYMENT", macro.get("US_unemployment", "N/A"), "%", C_GREEN),
    ]

    card_data = []
    for label, val, unit, color in cards:
        cell = [
            Paragraph(label, styles["CardLabel"]),
            Paragraph(f"{val}{unit}", ParagraphStyle(
                "CV", fontName="Helvetica-Bold", fontSize=20,
                textColor=color, spaceAfter=2
            )),
        ]
        card_data.append(cell)

    row_table = Table([card_data], colWidths=[4.25*cm]*4)
    row_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_DARK_CARD),
        ("TOPPADDING", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("LINEBEFORE", (1,0), (-1,-1), 1, C_GRAY),
    ]))
    elements.append(row_table)
    elements.append(Spacer(1, 0.4*cm))
    return elements


def build_top_movers(styles, movers: dict) -> list:
    """Top gainers, losers, most active table."""
    elements = []

    if not movers:
        elements.append(Paragraph("Market movers data unavailable (Alpha Vantage rate limit).", styles["SmallGray"]))
        return elements

    for section_key, section_label, color in [
        ("top_gainers", "TOP GAINERS OF THE WEEK", C_GREEN),
        ("top_losers", "TOP LOSERS OF THE WEEK", C_RED),
    ]:
        stocks = movers.get(section_key, [])
        if not stocks:
            continue

        elements.append(Paragraph(section_label, ParagraphStyle(
            "SH2", fontName="Helvetica-Bold", fontSize=10,
            textColor=color, spaceBefore=8, spaceAfter=4
        )))

        header = [["TICKER", "PRICE", "CHANGE $", "CHANGE %", "VOLUME"]]
        rows = header + [
            [s.get("ticker",""),
             f"${s.get('price','N/A')}",
             s.get("change_amount","N/A"),
             s.get("change_percentage","N/A"),
             s.get("volume","N/A")]
            for s in stocks[:5]
        ]

        t = Table(rows, colWidths=[3*cm, 3*cm, 3*cm, 3*cm, 5*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), C_NAVY),
            ("TEXTCOLOR", (0,0), (-1,0), C_WHITE),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_DARK_CARD, C_NAVY]),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("TEXTCOLOR", (0,1), (0,-1), color),
            ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.3*cm))

    return elements


def build_commodities_fx(styles, commodities: dict, fx: dict) -> list:
    """Page: Commodities prices + FX rates."""
    elements = []
    elements.append(PageBreak())
    elements.append(Paragraph("2. COMMODITIES & CURRENCIES", styles["SectionHeader"]))

    # Commodities table
    elements.append(Paragraph("KEY COMMODITIES", styles["CardLabel"]))
    comm_rows = [["COMMODITY", "PRICE", "DATE"]]
    labels = {
        "gold": "Gold (USD/oz)", "oil_brent": "Brent Oil (USD/bbl)",
        "nat_gas": "Natural Gas (USD/MMBtu)", "copper": "Copper (USD/lb)",
        "wheat": "Wheat (USD/bushel)", "coffee": "Coffee (USD/lb)",
    }
    for key, label in labels.items():
        c = commodities.get(key, {})
        comm_rows.append([label, c.get("price", "N/A"), c.get("date", "N/A")])

    comm_table = Table(comm_rows, colWidths=[7*cm, 5*cm, 5*cm])
    comm_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), C_NAVY),
        ("TEXTCOLOR", (0,0), (-1,0), C_WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_DARK_CARD, C_NAVY]),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("TEXTCOLOR", (0,1), (1,-1), C_GOLD),
        ("FONTNAME", (0,1), (1,-1), "Helvetica-Bold"),
    ]))
    elements.append(comm_table)
    elements.append(Spacer(1, 0.5*cm))

    # FX rates
    if fx:
        elements.append(Paragraph("FX RATES vs USD", styles["CardLabel"]))
        fx_rows = [["PAIR", "RATE"]]
        for pair, rate in fx.items():
            fx_rows.append([pair, rate])

        fx_table = Table(fx_rows, colWidths=[7*cm, 10*cm])
        fx_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), C_NAVY),
            ("TEXTCOLOR", (0,0), (-1,0), C_WHITE),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_DARK_CARD, C_NAVY]),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
        ]))
        elements.append(fx_table)

    return elements


def build_real_estate_section(styles) -> list:
    """Real Estate Opportunities section."""
    elements = []
    elements.append(PageBreak())
    elements.append(Paragraph("5. REAL ESTATE OPPORTUNITIES", styles["SectionHeader"]))
    elements.append(Paragraph(
        "Best countries/cities for real estate investment right now, ranked by opportunity score.",
        styles["Body"]
    ))
    elements.append(Spacer(1, 0.3*cm))

    sorted_re = sorted(REAL_ESTATE_OPPORTUNITIES, key=lambda x: x["score"], reverse=True)

    for i, opp in enumerate(sorted_re):
        score_color = _score_color(opp["score"])
        risk_color = _risk_color(opp["risk"])

        card_data = [
            [
                Paragraph(f"#{i+1}  {opp['country'].upper()} — {opp['city']}", ParagraphStyle(
                    "CardH", fontName="Helvetica-Bold", fontSize=12, textColor=C_WHITE
                )),
                Paragraph(f"SCORE: {opp['score']}/100", ParagraphStyle(
                    "ScoreP", fontName="Helvetica-Bold", fontSize=14,
                    textColor=score_color, alignment=TA_RIGHT
                )),
            ],
            [
                Paragraph(opp["opportunity"], styles["Opportunity"]),
                Paragraph(f"Risk: {opp['risk']}", ParagraphStyle(
                    "RiskP", fontName="Helvetica-Bold", fontSize=9,
                    textColor=risk_color, alignment=TA_RIGHT
                )),
            ],
            [
                Paragraph(
                    f"Type: {opp['asset_type']}  |  ~${opp['avg_price_sqm_usd']}/m²  |  Yield: {opp['rental_yield_pct']}%",
                    styles["Tag"]
                ),
                Paragraph(opp["catalyst"], styles["SmallGray"]),
            ],
        ]

        card = Table(card_data, colWidths=[12*cm, 5*cm])
        card.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), C_DARK_CARD),
            ("TOPPADDING", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 10),
            ("RIGHTPADDING", (0,0), (-1,-1), 10),
            ("LINEBELOW", (0,2), (-1,2), 0.5, C_GRAY),
        ]))
        elements.append(KeepTogether(card))
        elements.append(Spacer(1, 0.25*cm))

    return elements


def build_business_opportunities(styles) -> list:
    """Business / Entrepreneurship Opportunities section."""
    elements = []
    elements.append(PageBreak())
    elements.append(Paragraph("6. BUSINESS & ENTREPRENEURSHIP OPPORTUNITIES", styles["SectionHeader"]))
    elements.append(Paragraph(
        "Sectors and markets with structural demand gaps — opportunities to build or invest in companies.",
        styles["Body"]
    ))
    elements.append(Spacer(1, 0.3*cm))

    sorted_biz = sorted(BUSINESS_OPPORTUNITIES, key=lambda x: x["score"], reverse=True)

    for i, opp in enumerate(sorted_biz):
        score_color = _score_color(opp["score"])

        card_data = [
            [
                Paragraph(
                    f"#{i+1}  {opp['sector'].upper()}",
                    ParagraphStyle("BH", fontName="Helvetica-Bold", fontSize=11, textColor=C_WHITE)
                ),
                Paragraph(f"SCORE: {opp['score']}/100", ParagraphStyle(
                    "ScP", fontName="Helvetica-Bold", fontSize=13,
                    textColor=score_color, alignment=TA_RIGHT
                )),
            ],
            [
                Paragraph(f"Regions: {', '.join(opp['regions'])}", styles["Tag"]),
                Paragraph(f"Market: ${opp['market_size_usd_b']}B | Barrier: {opp['entry_barrier']}", ParagraphStyle(
                    "MB", fontName="Helvetica", fontSize=8, textColor=C_GRAY, alignment=TA_RIGHT
                )),
            ],
            [
                Paragraph(opp["opportunity"], styles["Opportunity"]),
                Paragraph("", styles["Body"]),
            ],
            [
                Paragraph(f"Model: {opp['model']}", styles["SmallGray"]),
                Paragraph("", styles["Body"]),
            ],
            [
                Paragraph(f"WHY NOW: {opp['why_now']}", ParagraphStyle(
                    "WN", fontName="Helvetica-Bold", fontSize=8, textColor=C_GOLD
                )),
                Paragraph("", styles["Body"]),
            ],
        ]

        card = Table(card_data, colWidths=[12*cm, 5*cm])
        card.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), C_DARK_CARD),
            ("TOPPADDING", (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING", (0,0), (-1,-1), 10),
            ("RIGHTPADDING", (0,0), (-1,-1), 10),
            ("SPAN", (0,2), (-1,2)),
            ("SPAN", (0,3), (-1,3)),
            ("SPAN", (0,4), (-1,4)),
        ]))
        elements.append(KeepTogether(card))
        elements.append(Spacer(1, 0.25*cm))

    return elements


def build_footer_page(styles) -> list:
    """Last page: Disclaimer and methodology."""
    elements = []
    elements.append(PageBreak())
    elements.append(Paragraph("METHODOLOGY & DISCLAIMER", styles["SectionHeader"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=C_GRAY))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        "This report is generated automatically by the AI Investment Fund system using:"
        " yfinance (market data), Alpha Vantage (economic indicators, commodities, FX),"
        " Financial Modeling Prep (fundamentals), and Anthropic Claude / Google Gemini"
        " for intelligent analysis.",
        styles["Body"]
    ))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        "Investment Philosophy: Hybrid Buffett (margin of safety >=30%, ROE >15%, economic moat)"
        " + Lynch (PEG <1.5, EPS growth >20%, under-discovered companies).",
        styles["Body"]
    ))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        "DISCLAIMER: This report is for informational purposes only and does not constitute"
        " investment advice. All investment decisions carry risk. Past performance does not"
        " guarantee future results. Always conduct your own due diligence.",
        ParagraphStyle("Disc", fontName="Helvetica-Oblique", fontSize=8, textColor=C_GRAY)
    ))
    return elements


# ─── Main Report Builder ───────────────────────────────────────────────────────

def generate_weekly_report(output_path: Optional[Path] = None) -> Path:
    """
    Generate the full weekly PDF report.
    Returns the path to the generated PDF.
    """
    if output_path is None:
        filename = f"weekly_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        output_path = REPORTS_DIR / filename

    print(f"[*] Generating weekly report: {output_path}")

    # Fetch all data
    print("[*] Fetching macro indicators from Alpha Vantage...")
    macro = get_macro_indicators()
    print(f"    Got: {list(macro.keys())}")

    print("[*] Fetching commodity prices...")
    commodities = get_commodity_prices()
    print(f"    Got: {list(commodities.keys())}")

    print("[*] Fetching FX rates...")
    fx = get_fx_rates()
    print(f"    Got: {list(fx.keys())}")

    print("[*] Fetching top movers...")
    movers = get_top_movers()
    print(f"    Got gainers: {len(movers.get('top_gainers', []))}")

    # Build PDF
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title=f"AI Investment Fund - Weekly Report {WEEK_STR}",
        author="AI Investment Fund",
    )

    styles = get_styles()
    elements = []

    elements += build_cover_page(styles, WEEK_STR)
    elements += build_kpi_cards(styles, macro, movers)
    elements += build_top_movers(styles, movers)
    elements += build_commodities_fx(styles, commodities, fx)
    elements += build_real_estate_section(styles)
    elements += build_business_opportunities(styles)
    elements += build_footer_page(styles)

    doc.build(elements)
    print(f"[+] Report saved: {output_path}")
    return output_path


if __name__ == "__main__":
    path = generate_weekly_report()
    print(f"\nReport generated: {path}")
