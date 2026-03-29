"""
main.py  —  Orchestrates the full monitoring loop.

Two threads run in parallel:
  1. Monitor loop   — scans Reddit every POLL_INTERVAL seconds,
                      generates Claude drafts, sends approval emails.
  2. Approval server — Flask HTTP server that handles approve/reject clicks.

Usage:
    python main.py
"""

import logging
import time
import threading
import sys

import config
from database import init_db, update_status
from scraper import run_scan
from responder import generate_replies_for_pending
from emailer import send_approval_emails
import approval_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("monitor.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def monitor_loop():
    """Runs the scan → generate → email pipeline in a loop."""
    logger.info("=== Monitor loop started ===")
    while True:
        try:
            logger.info("--- Starting scan cycle ---")

            # 1. Scrape Reddit for new keyword matches
            new_posts = run_scan()

            if new_posts:
                logger.info(f"Found {len(new_posts)} new posts. Generating replies...")

                # 2. Generate Claude reply drafts
                posts_with_drafts = generate_replies_for_pending(new_posts)

                if posts_with_drafts:
                    # Mark as pending_approval before sending emails
                    for p in posts_with_drafts:
                        update_status(p["source_id"], "pending_approval", p.get("reply_draft"))

                    # 3. Send approval emails
                    sent = send_approval_emails(posts_with_drafts)
                    logger.info(f"Sent {sent}/{len(posts_with_drafts)} approval emails.")
                else:
                    logger.info("No successful drafts generated.")
            else:
                logger.info("No new keyword matches this cycle.")

        except Exception as e:
            logger.error(f"Error in monitor loop: {e}", exc_info=True)

        logger.info(f"Sleeping {config.POLL_INTERVAL}s until next scan...")
        time.sleep(config.POLL_INTERVAL)


def main():
    init_db()

    # Start the approval server in a background thread
    server_thread = threading.Thread(target=approval_server.run_server, daemon=True)
    server_thread.start()
    logger.info(f"Approval server → http://{config.APPROVAL_HOST}:{config.APPROVAL_PORT}")
    logger.info(f"Status dashboard → http://{config.APPROVAL_HOST}:{config.APPROVAL_PORT}/status")

    # Run the monitor loop in the main thread
    monitor_loop()


if __name__ == "__main__":
    main()
