"""
responder.py  —  Generates a reply draft using the Claude API (Anthropic).
"""

import logging
import anthropic

import config
from database import update_status

logger = logging.getLogger(__name__)

_client = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def build_user_prompt(post: dict) -> str:
    return f"""
A Reddit user posted the following in r/{post['subreddit']}:

---
Title: {post['title']}

{post['body']}
---

Please write a helpful, genuine reply to this post that addresses their question or comment about 1031 exchanges.
Keep the tone conversational and appropriate for Reddit.
Do NOT be promotional. If applicable, gently recommend they consult a Qualified Intermediary (QI) and tax advisor.
""".strip()


def generate_reply(post: dict) -> str | None:
    """
    Calls Claude to generate a reply draft for the given post.
    Returns the reply text, or None on failure.
    Updates the post status in the DB.
    """
    client = get_client()
    user_prompt = build_user_prompt(post)

    logger.info(f"Generating reply for {post['source_id']} ...")

    try:
        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=1024,
            system=config.SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
        )
        reply = message.content[0].text.strip()
        update_status(post["source_id"], "draft_ready", reply_draft=reply)
        logger.info(f"Reply draft ready for {post['source_id']}")
        return reply

    except Exception as e:
        logger.error(f"Claude API error for {post['source_id']}: {e}")
        update_status(post["source_id"], "error")
        return None


def generate_replies_for_pending(posts: list[dict]) -> list[dict]:
    """Generate replies for a list of new posts. Returns posts with 'reply_draft' populated."""
    enriched = []
    for post in posts:
        reply = generate_reply(post)
        if reply:
            post["reply_draft"] = reply
            enriched.append(post)
    return enriched
