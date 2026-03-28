"""
Massive 50-Page Visual Deep Dive Report Generator
Uses Gemini 2.5 JSON compiler to generate unlimited hyper-detailed pages with contextual photos.
"""
import os
import json
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, KeepTogether, PageBreak, Image, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from financial_data import get_stock_data
from val_db import REAL_ESTATE_OPPORTUNITIES, BUSINESS_OPPORTUNITIES
from llm_pdf_compiler import generate_stock_deep_dive, generate_real_estate_deep_dive, generate_startup_deep_dive
from image_utils import download_context_image
from report_generator import get_styles, build_cover_page, C_BG, C_WHITE, C_NAVY

BASE_DIR = Path(__file__).parent
REPORTS_DIR = BASE_DIR / "output" / "reports" / "deep_dives"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DATE_STR = datetime.now().strftime("%d %B %Y")
WEEK_STR = datetime.now().strftime("%Y-W%V")

def _parse_llm_json_to_flowables(json_blocks: list, styles) -> list:
    """Takes the rigidly structured JSON array from Gemini and maps it to ReportLab PDF flows."""
    elements = []
    
    # Custom styles mapping
    style_map = {
        "H1": styles["ReportTitle"],
        "H2": styles["SectionHeader"],
        "H3": ParagraphStyle("H3", fontName="Helvetica-Bold", fontSize=13, textColor=C_WHITE, spaceBefore=8, spaceAfter=4),
        "P": styles["Body"],
    }
    
    for block in json_blocks:
        btype = block.get("type", "P")
        content = block.get("content", "")
        
        if btype in ["H1", "H2", "H3", "P"]:
            # Ensure safe XML characters for ReportLab
            safe_content = content.replace("<", "&lt;").replace(">", "&gt;")
            if btype == "H1":
                elements.append(PageBreak())
            elements.append(Paragraph(safe_content, style_map[btype]))
            
        elif btype == "BULLETS":
            items = block.get("items", [])
            list_items = []
            for item in items:
                safe_item = item.replace("<", "&lt;").replace(">", "&gt;")
                list_items.append(ListItem(Paragraph(safe_item, styles["Body"]), leftIndent=15))
            elements.append(ListFlowable(list_items, bulletType='bullet', spaceAfter=8))
            
        elif btype == "IMAGE":
            kw = block.get("query", "finance")
            # Force download an image
            img_path = download_context_image(kw, width=600, height=350)
            if img_path and os.path.exists(img_path):
                # Scale image nicely
                img = Image(img_path, width=15*cm, height=8.75*cm)
                elements.append(Spacer(1, 0.4*cm))
                elements.append(KeepTogether([img]))
                elements.append(Spacer(1, 0.4*cm))
            else:
                elements.append(Paragraph(f"[Image Placeholder for: {kw}]", styles["SmallGray"]))

        elements.append(Spacer(1, 0.2*cm))
        
    return elements

def build_deep_dive_report() -> Path:
    """Main Orchestrator: Generate the 50-page massive PDF."""
    
    filename = f"deep_dive_report_{datetime.now().strftime('%Y%m%d')}.pdf"
    output_path = REPORTS_DIR / filename
    
    print(f"[*] Starting 50-Page Visual Deep Dive Report Generator...")
    
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title=f"AI Investment Fund - DEEP DIVE {WEEK_STR}",
        author="Antigravity Deep Dive Engine",
    )
    
    styles = get_styles()
    elements = []
    
    # 1. Cover
    elements += build_cover_page(styles, WEEK_STR)
    elements.append(PageBreak())
    
    # 2. Stock Deep Dives (Top 3 for now so it doesn't take 30 minutes, can expand to 10)
    top_stocks = [("NVDA", "Nvidia Corp"), ("PLTR", "Palantir Tech"), ("MELI", "Mercado Libre")]
    for ticker, name in top_stocks:
        data = get_stock_data(ticker, verbose=False)
        blocks = generate_stock_deep_dive(ticker, name, data)
        elements += _parse_llm_json_to_flowables(blocks, styles)
        
    # 3. Real Estate Deep Dives
    for r in REAL_ESTATE_OPPORTUNITIES:
        blocks = generate_real_estate_deep_dive(r["country"], r["city"], r["opportunity"])
        elements += _parse_llm_json_to_flowables(blocks, styles)
        
    # 4. Startup / Business Ideas Deep Dives
    for b in BUSINESS_OPPORTUNITIES:
        blocks = generate_startup_deep_dive(b["sector"], b["opportunity"])
        elements += _parse_llm_json_to_flowables(blocks, styles)

    # Compile the 50-page PDF
    print("[*] Rendering massive PDF with ReportLab...")
    
    # Dark Mode Background Fix for ReportLab SimpleDocTemplate
    def add_dark_background(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(C_BG)
        canvas.rect(0, 0, A4[0], A4[1], fill=1)
        canvas.restoreState()
        
    doc.build(elements, onFirstPage=add_dark_background, onLaterPages=add_dark_background)
    
    print(f"[+] DONE! Deep Dive Report saved at: {output_path}")
    return output_path

if __name__ == "__main__":
    p = build_deep_dive_report()
    import sys
    sys.exit(0)
