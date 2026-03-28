"""
Weekly Report Scheduler
Runs the report generator every Sunday at 08:00 AM (Argentina time).
Can also be triggered manually at any time.

Usage:
  python scheduler.py              # Start the weekly scheduler (keeps running)
  python scheduler.py --now        # Generate report immediately and exit
"""
import sys
import schedule
import time
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent


def run_report():
    """Execute the weekly report generation."""
    print(f"\n{'='*60}")
    print(f"  WEEKLY REPORT — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    try:
        from reports.report_generator import generate_weekly_report
        path = generate_weekly_report()
        print(f"\n[OK] Report generated: {path}")
        print(f"     Open it to review this week's global investment intelligence.")
    except Exception as e:
        print(f"\n[ERROR] Report generation failed: {e}")
        raise


def main():
    if "--now" in sys.argv:
        print("[*] Running report immediately (--now flag)...")
        run_report()
        return

    # Schedule for every Sunday at 08:00
    schedule.every().sunday.at("08:00").do(run_report)

    print("="*60)
    print("  AI Investment Fund — Weekly Report Scheduler")
    print("  Runs every Sunday at 08:00 AM")
    print("  Press Ctrl+C to stop")
    print("="*60)
    print(f"\n  Next run: {schedule.next_run()}")

    while True:
        schedule.run_pending()
        time.sleep(60)  # check every minute


if __name__ == "__main__":
    main()
