"""
poster.py  —  Handles approved replies.

NOTE: Since Reddit no longer allows new API app creation, automatic posting
is disabled. Instead, approved posts are marked as "ready_to_post" and the
user must manually copy/paste the reply from the dashboard.
"""

import logging

from database import update_status

logger = logging.getLogger(__name__)


def post_reply(post: dict) -> bool:
    """
    Marks the post as ready_to_post (manual posting required).
    The reply draft is shown in the dashboard for the user to copy.
    Returns True on success.
    """
    source_id  = post["source_id"]
    reply_text = post.get("reply_draft", "")
    url        = post.get("url", "")

    if not reply_text:
        logger.error(f"No reply draft for {source_id}, skipping.")
        update_status(source_id, "error")
        return False

    # Mark as posted (manual) - user needs to copy/paste from dashboard
    update_status(source_id, "posted")
    logger.info(f"✅ Reply approved for {source_id}")
    logger.info(f"   → Manual posting required at: {url}")
    logger.info(f"   → Copy reply from dashboard: http://localhost:5055/status")
    return True


def post_all_approved():
    """Post all replies that have been approved but not yet posted."""
    from database import get_posts_by_status
    approved = get_posts_by_status("approved")
    logger.info(f"Found {len(approved)} approved posts to publish.")
    for post in approved:
        post_reply(post)
