"""
poster.py  —  Posts the approved reply to Reddit.
"""

import logging
import praw

import config
from database import update_status

logger = logging.getLogger(__name__)


def get_reddit_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_CLIENT_SECRET,
        username=config.REDDIT_USERNAME,
        password=config.REDDIT_PASSWORD,
        user_agent=config.REDDIT_USER_AGENT,
    )


def post_reply(post: dict) -> bool:
    """
    Posts the reply_draft as a comment on the Reddit post/comment.
    Returns True on success.
    """
    reddit = get_reddit_client()
    source_id   = post["source_id"]
    reply_text  = post.get("reply_draft", "")
    post_type   = post.get("type", "post")

    if not reply_text:
        logger.error(f"No reply draft for {source_id}, skipping.")
        update_status(source_id, "error")
        return False

    try:
        # Extract the raw Reddit ID (strip "post_" or "comment_" prefix)
        raw_id = source_id.split("_", 1)[1]

        if post_type == "post":
            submission = reddit.submission(id=raw_id)
            submission.reply(reply_text)
        else:
            comment = reddit.comment(id=raw_id)
            comment.reply(reply_text)

        update_status(source_id, "posted")
        logger.info(f"✅ Reply posted for {source_id}")
        return True

    except praw.exceptions.APIException as e:
        logger.error(f"Reddit API error for {source_id}: {e}")
        update_status(source_id, "error")
        return False

    except Exception as e:
        logger.error(f"Unexpected error posting {source_id}: {e}")
        update_status(source_id, "error")
        return False


def post_all_approved():
    """Post all replies that have been approved but not yet posted."""
    from database import get_posts_by_status
    approved = get_posts_by_status("approved")
    logger.info(f"Found {len(approved)} approved posts to publish.")
    for post in approved:
        post_reply(post)
