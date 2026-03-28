"""
Telegram Bot Notifier — AI Investment Fund
Sends alerts and PDFs directly to your Telegram.

Setup (5 minutes):
  1. Open Telegram → search @BotFather → /newbot
  2. Name it "InvestmentFund" → get the TOKEN
  3. Start a chat with your bot → send /start
  4. Get your CHAT_ID: https://api.telegram.org/bot<TOKEN>/getUpdates
  5. Add to .env:
        TELEGRAM_BOT_TOKEN=xxxx:yyyy
        TELEGRAM_CHAT_ID=123456789
"""
import os
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")
BASE_URL  = f"https://api.telegram.org/bot{BOT_TOKEN}"


def _is_configured() -> bool:
    return bool(BOT_TOKEN and CHAT_ID and
                BOT_TOKEN != "your_telegram_bot_token_here" and
                CHAT_ID   != "your_telegram_chat_id_here")


def send_message(text: str, parse_mode: str = "HTML") -> bool:
    """Send a plain text (or HTML-formatted) message to Telegram."""
    if not _is_configured():
        print("[Telegram] Not configured — skipping notification")
        return False
    try:
        r = requests.post(f"{BASE_URL}/sendMessage", json={
            "chat_id":    CHAT_ID,
            "text":       text,
            "parse_mode": parse_mode,
        }, timeout=10)
        return r.ok
    except Exception as e:
        print(f"[Telegram] Error sending message: {e}")
        return False


def send_pdf(pdf_path: Path, caption: str = "") -> bool:
    """Send a PDF document to Telegram (e.g. weekly report)."""
    if not _is_configured():
        print("[Telegram] Not configured — skipping PDF notification")
        return False
    try:
        with open(pdf_path, "rb") as f:
            r = requests.post(f"{BASE_URL}/sendDocument", data={
                "chat_id": CHAT_ID,
                "caption": caption[:1024],
                "parse_mode": "HTML",
            }, files={"document": f}, timeout=30)
        return r.ok
    except Exception as e:
        print(f"[Telegram] Error sending PDF: {e}")
        return False


# ─── Pre-built alert templates ─────────────────────────────────────────────────

def alert_buy(ticker: str, company: str, price: float, target: float,
              mos_pct: float, hybrid_score: int, reason: str):
    """Send a BUY alert."""
    potential = round((target - price) / price * 100, 1)
    msg = (
        f"<b>🟢 BUY SIGNAL — {ticker}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>{company}</b>\n\n"
        f"💰 <b>Entry Price:</b> ${price:,.2f}\n"
        f"🎯 <b>Target Price:</b> ${target:,.2f} (+{potential}%)\n"
        f"🛡 <b>Margin of Safety:</b> {mos_pct:.0f}%\n"
        f"⭐ <b>Hybrid Score:</b> {hybrid_score}/100\n\n"
        f"<b>Thesis:</b> {reason}\n\n"
        f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M')} | AI Investment Fund</i>"
    )
    return send_message(msg)


def alert_sell(ticker: str, company: str, price: float, entry_price: float,
               gain_pct: float, reason: str):
    """Send a SELL / take-profit alert."""
    emoji = "🔴" if gain_pct < 0 else "💚"
    msg = (
        f"<b>{emoji} SELL SIGNAL — {ticker}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>{company}</b>\n\n"
        f"📤 <b>Sell Price:</b> ${price:,.2f}\n"
        f"📥 <b>Entry Was:</b> ${entry_price:,.2f}\n"
        f"{'🚀' if gain_pct >= 0 else '📉'} <b>Return:</b> {gain_pct:+.1f}%\n\n"
        f"<b>Reason:</b> {reason}\n\n"
        f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M')} | AI Investment Fund</i>"
    )
    return send_message(msg)


def alert_watch(ticker: str, company: str, price: float, condition: str):
    """Send a WATCH alert — approaching buy zone."""
    msg = (
        f"<b>🔵 WATCH — {ticker}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>{company}</b> @ ${price:,.2f}\n\n"
        f"⚠️ {condition}\n\n"
        f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M')} | AI Investment Fund</i>"
    )
    return send_message(msg)


def send_weekly_summary(regions_analyzed: int, picks_count: int,
                        top_pick: str, pdf_path: Optional[Path] = None):
    """Send weekly report summary + optionally attach PDF."""
    date_str = datetime.now().strftime("%d %B %Y")
    msg = (
        f"<b>📊 WEEKLY INVESTMENT REPORT</b>\n"
        f"<i>{date_str}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🌍 <b>Regions analyzed:</b> {regions_analyzed}/6\n"
        f"📈 <b>Opportunities found:</b> {picks_count}\n"
        f"⭐ <b>Top pick this week:</b> {top_pick}\n\n"
        f"Full PDF report attached below 👇"
    )
    send_message(msg)

    if pdf_path and pdf_path.exists():
        caption = f"AI Investment Fund — Weekly Report {date_str}"
        send_pdf(pdf_path, caption=caption)


def send_market_open_briefing(macro_summary: str):
    """Monday morning market briefing."""
    msg = (
        f"<b>☀️ MONDAY MARKET BRIEFING</b>\n"
        f"<i>{datetime.now().strftime('%d %B %Y')}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{macro_summary}\n\n"
        f"<i>Stay disciplined. Buffett's Rule #1: Never lose money.</i>"
    )
    return send_message(msg)
