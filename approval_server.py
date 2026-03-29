"""
approval_server.py  —  Tiny Flask server that handles Approve / Reject clicks.

The approver clicks a link in the email like:
  http://localhost:5055/approval?id=post_abc123&action=approve

The server updates the DB and (if approved) triggers the poster.
"""

import logging
import threading
from flask import Flask, request, jsonify, abort

import config
from database import init_db, update_status, get_posts_by_status
import poster

logger = logging.getLogger(__name__)
app = Flask(__name__)


@app.route("/approval")
def approval():
    source_id = request.args.get("id", "").strip()
    action    = request.args.get("action", "").strip().lower()

    if not source_id or action not in ("approve", "reject"):
        abort(400, "Missing or invalid parameters.")

    # Lookup post
    rows = get_posts_by_status("draft_ready") + get_posts_by_status("pending_approval")
    post = next((r for r in rows if r["source_id"] == source_id), None)

    if post is None:
        # Might already be processed
        return _html_response(
            "Already Processed",
            f"Post <code>{source_id}</code> has already been handled.",
            "#888"
        )

    if action == "approve":
        update_status(source_id, "approved")
        logger.info(f"✅ APPROVED: {source_id}")

        # Post in background so the HTTP response returns fast
        threading.Thread(target=_post_async, args=(post,), daemon=True).start()

        return _html_response(
            "✅ Approved!",
            f"Reply will be posted to Reddit shortly.<br/><br/>"
            f"<a href=\"{post['url']}\">View original post →</a>",
            "#4CAF50"
        )

    else:  # reject
        update_status(source_id, "rejected")
        logger.info(f"❌ REJECTED: {source_id}")
        return _html_response(
            "❌ Rejected",
            f"Post <code>{source_id}</code> has been rejected. No reply will be sent.",
            "#f44336"
        )


@app.route("/status")
def status():
    """Quick dashboard endpoint — returns all posts as JSON."""
    from database import get_conn
    import sqlite3
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT source_id, type, subreddit, status, title, created_at FROM posts ORDER BY created_at DESC LIMIT 50").fetchall()
    return jsonify([dict(r) for r in rows])


def _post_async(post: dict):
    try:
        poster.post_reply(post)
    except Exception as e:
        logger.error(f"Background poster error for {post['source_id']}: {e}")


def _html_response(title: str, body: str, color: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{title}</title></head>
<body style="font-family:Arial,sans-serif;text-align:center;padding:60px">
  <h1 style="color:{color}">{title}</h1>
  <p style="font-size:18px">{body}</p>
  <p style="margin-top:40px">
    <a href="/status" style="color:#2196F3">View all posts →</a>
  </p>
</body>
</html>
"""


def run_server():
    init_db()
    logger.info(f"Approval server running at http://{config.APPROVAL_HOST}:{config.APPROVAL_PORT}")
    app.run(host=config.APPROVAL_HOST, port=config.APPROVAL_PORT, debug=False)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_server()
