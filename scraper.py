"""
scraper.py  —  Monitors Reddit for posts/comments mentioning 1031 exchanges.
Uses public Reddit JSON endpoints (no API key required).
"""

import logging
import time
from datetime import datetime

import requests

import config
from database import init_db, already_seen, mark_seen, save_post

logger = logging.getLogger(__name__)

# Reddit requires a proper User-Agent for public JSON access
HEADERS = {
    "User-Agent": config.REDDIT_USER_AGENT,
}


def contains_keyword(text: str) -> bool:
    lower = text.lower()
    return any(kw.lower() in lower for kw in config.KEYWORDS)


def fetch_json(url: str) -> dict | None:
    """Fetch JSON from Reddit public endpoint with rate limiting."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        time.sleep(1)  # Rate limit: be nice to Reddit
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return None


def scan_subreddit(subreddit_name: str) -> list[dict]:
    """Scan new posts and comments in a subreddit for keyword matches."""
    found = []

    # Scan new submissions
    posts_url = f"https://www.reddit.com/r/{subreddit_name}/new.json?limit=50"
    data = fetch_json(posts_url)
    
    if data and "data" in data:
        for child in data["data"].get("children", []):
            post = child["data"]
            post_id = f"post_{post['id']}"
            
            if already_seen(post_id):
                continue
            mark_seen(post_id)

            title_body = f"{post.get('title', '')} {post.get('selftext', '')}"
            if contains_keyword(title_body):
                item = {
                    "source_id": post_id,
                    "type": "post",
                    "subreddit": subreddit_name,
                    "url": f"https://reddit.com{post['permalink']}",
                    "title": post.get("title", ""),
                    "body": post.get("selftext", "")[:2000],
                    "author": post.get("author", "[deleted]"),
                    "created_utc": datetime.utcfromtimestamp(post["created_utc"]).isoformat(),
                }
                save_post(item)
                found.append(item)
                logger.info(f"[MATCH] Post in r/{subreddit_name}: {item['title'][:80]}")

    # Scan new comments
    comments_url = f"https://www.reddit.com/r/{subreddit_name}/comments.json?limit=100"
    data = fetch_json(comments_url)
    
    if data and "data" in data:
        for child in data["data"].get("children", []):
            comment = child["data"]
            comment_id = f"comment_{comment['id']}"
            
            if already_seen(comment_id):
                continue
            mark_seen(comment_id)

            body = comment.get("body", "")
            if contains_keyword(body):
                item = {
                    "source_id": comment_id,
                    "type": "comment",
                    "subreddit": subreddit_name,
                    "url": f"https://reddit.com{comment['permalink']}",
                    "title": f"Comment in: {comment.get('link_title', 'Unknown')}",
                    "body": body[:2000],
                    "author": comment.get("author", "[deleted]"),
                    "created_utc": datetime.utcfromtimestamp(comment["created_utc"]).isoformat(),
                }
                save_post(item)
                found.append(item)
                logger.info(f"[MATCH] Comment in r/{subreddit_name}: {body[:80]}")

    return found


def run_scan() -> list[dict]:
    """Run a full scan across all configured subreddits."""
    init_db()
    all_matches = []

    for sub in config.SUBREDDITS:
        sub = sub.strip()
        logger.info(f"Scanning r/{sub} ...")
        try:
            matches = scan_subreddit(sub)
            all_matches.extend(matches)
        except Exception as e:
            logger.error(f"Error scanning r/{sub}: {e}")

    logger.info(f"Scan complete. {len(all_matches)} new matches found.")
    return all_matches
