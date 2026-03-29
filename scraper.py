"""
scraper.py  —  Monitors Reddit for posts/comments mentioning 1031 exchanges.
Uses PRAW (Python Reddit API Wrapper).
"""

import logging
import sqlite3
from datetime import datetime

import praw

import config
from database import init_db, already_seen, mark_seen, save_post

logger = logging.getLogger(__name__)


def get_reddit_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_CLIENT_SECRET,
        username=config.REDDIT_USERNAME,
        password=config.REDDIT_PASSWORD,
        user_agent=config.REDDIT_USER_AGENT,
    )


def contains_keyword(text: str) -> bool:
    lower = text.lower()
    return any(kw.lower() in lower for kw in config.KEYWORDS)


def scan_subreddit(reddit: praw.Reddit, subreddit_name: str) -> list[dict]:
    """Scan new posts and comments in a subreddit for keyword matches."""
    found = []
    subreddit = reddit.subreddit(subreddit_name)

    # Scan new submissions
    for submission in subreddit.new(limit=50):
        post_id = f"post_{submission.id}"
        if already_seen(post_id):
            continue
        mark_seen(post_id)

        title_body = f"{submission.title} {submission.selftext}"
        if contains_keyword(title_body):
            item = {
                "source_id": post_id,
                "type": "post",
                "subreddit": subreddit_name,
                "url": f"https://reddit.com{submission.permalink}",
                "title": submission.title,
                "body": submission.selftext[:2000],
                "author": str(submission.author),
                "created_utc": datetime.utcfromtimestamp(submission.created_utc).isoformat(),
            }
            save_post(item)
            found.append(item)
            logger.info(f"[MATCH] Post in r/{subreddit_name}: {submission.title[:80]}")

    # Scan new comments
    for comment in subreddit.comments(limit=100):
        comment_id = f"comment_{comment.id}"
        if already_seen(comment_id):
            continue
        mark_seen(comment_id)

        if contains_keyword(comment.body):
            item = {
                "source_id": comment_id,
                "type": "comment",
                "subreddit": subreddit_name,
                "url": f"https://reddit.com{comment.permalink}",
                "title": f"Comment in: {comment.link_title}",
                "body": comment.body[:2000],
                "author": str(comment.author),
                "created_utc": datetime.utcfromtimestamp(comment.created_utc).isoformat(),
            }
            save_post(item)
            found.append(item)
            logger.info(f"[MATCH] Comment in r/{subreddit_name}: {comment.body[:80]}")

    return found


def run_scan() -> list[dict]:
    """Run a full scan across all configured subreddits."""
    init_db()
    reddit = get_reddit_client()
    all_matches = []

    for sub in config.SUBREDDITS:
        sub = sub.strip()
        logger.info(f"Scanning r/{sub} ...")
        try:
            matches = scan_subreddit(reddit, sub)
            all_matches.extend(matches)
        except Exception as e:
            logger.error(f"Error scanning r/{sub}: {e}")

    logger.info(f"Scan complete. {len(all_matches)} new matches found.")
    return all_matches
