"""
emailer.py  —  Sends approval request emails via Gmail SMTP.

The email contains:
  - The original post
  - The Claude-generated reply draft
  - Two links:  [APPROVE]  and  [REJECT]
    pointing to the local approval_server.py Flask app.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

logger = logging.getLogger(__name__)


def _build_approval_url(source_id: str, action: str) -> str:
    return (
        f"http://{config.APPROVAL_HOST}:{config.APPROVAL_PORT}"
        f"/approval?id={source_id}&action={action}"
    )


def _build_html(post: dict) -> str:
    approve_url = _build_approval_url(post["source_id"], "approve")
    reject_url  = _build_approval_url(post["source_id"], "reject")

    return f"""
<html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto">
  <h2 style="color:#1a1a2e">📋 New 1031 Exchange Mention — Approval Required</h2>

  <table style="width:100%;border-collapse:collapse">
    <tr>
      <td style="padding:4px;font-weight:bold;width:120px">Subreddit:</td>
      <td>r/{post['subreddit']}</td>
    </tr>
    <tr>
      <td style="padding:4px;font-weight:bold">Type:</td>
      <td>{post['type'].capitalize()}</td>
    </tr>
    <tr>
      <td style="padding:4px;font-weight:bold">Author:</td>
      <td>u/{post['author']}</td>
    </tr>
    <tr>
      <td style="padding:4px;font-weight:bold">Link:</td>
      <td><a href="{post['url']}">{post['url']}</a></td>
    </tr>
  </table>

  <hr/>
  <h3>Original Post</h3>
  <div style="background:#f4f4f4;padding:12px;border-left:4px solid #888;border-radius:4px">
    <strong>{post['title']}</strong><br/><br/>
    {post['body'].replace(chr(10), '<br/>')}
  </div>

  <hr/>
  <h3>Proposed Reply (Claude Draft)</h3>
  <div style="background:#eaf4fb;padding:12px;border-left:4px solid #2196F3;border-radius:4px">
    {post['reply_draft'].replace(chr(10), '<br/>')}
  </div>

  <br/>
  <div style="text-align:center">
    <a href="{approve_url}"
       style="background:#4CAF50;color:white;padding:14px 32px;text-decoration:none;
              border-radius:6px;font-size:18px;margin-right:16px">
      ✅ APPROVE &amp; POST
    </a>
    <a href="{reject_url}"
       style="background:#f44336;color:white;padding:14px 32px;text-decoration:none;
              border-radius:6px;font-size:18px">
      ❌ REJECT
    </a>
  </div>

  <p style="color:#888;font-size:12px;margin-top:24px">
    Source ID: {post['source_id']} — This is an automated approval request.
  </p>
</body></html>
"""


def send_approval_email(post: dict) -> bool:
    """Send an approval email for the given post. Returns True on success."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[APPROVE?] 1031 mention in r/{post['subreddit']} — {post['title'][:60]}"
        msg["From"]    = config.EMAIL_SENDER
        msg["To"]      = config.EMAIL_APPROVER

        html_body = _build_html(post)
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
            server.sendmail(config.EMAIL_SENDER, config.EMAIL_APPROVER, msg.as_string())

        logger.info(f"Approval email sent for {post['source_id']} → {config.EMAIL_APPROVER}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email for {post['source_id']}: {e}")
        return False


def send_approval_emails(posts: list[dict]) -> int:
    """Send approval emails for all posts. Returns count of successful sends."""
    sent = 0
    for post in posts:
        if send_approval_email(post):
            sent += 1
    return sent
