import os
from dotenv import load_dotenv

load_dotenv()

# Reddit API
REDDIT_CLIENT_ID     = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME      = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD      = os.getenv("REDDIT_PASSWORD")
REDDIT_USER_AGENT    = os.getenv("REDDIT_USER_AGENT", "1031ExchangeMonitor/1.0")

# Subreddits to monitor (comma-separated in .env)
SUBREDDITS = os.getenv("SUBREDDITS", "realestateinvesting,RealEstate,tax,personalfinance").split(",")

# Keywords to detect
KEYWORDS = [
    "1031 exchange", "1031exchange", "1031 swap",
    "like-kind exchange", "like kind exchange",
    "deferred exchange", "section 1031"
]

# Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL      = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

# Email (Gmail SMTP)
EMAIL_SENDER    = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD  = os.getenv("EMAIL_PASSWORD")   # App password, NOT your real password
EMAIL_APPROVER  = os.getenv("EMAIL_APPROVER")   # Who receives approval requests

# Approval server
APPROVAL_HOST = os.getenv("APPROVAL_HOST", "localhost")
APPROVAL_PORT = int(os.getenv("APPROVAL_PORT", "5055"))

# DB
DB_PATH = os.getenv("DB_PATH", "monitor.db")

# Poll interval in seconds
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "300"))  # 5 minutes

# System prompt for Claude
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", """You are a helpful expert in 1031 exchanges (like-kind exchanges under IRC Section 1031).
Your goal is to provide genuinely useful, accurate answers to people asking about 1031 exchanges in online forums.
Keep replies concise (3-5 paragraphs max), friendly, and never spammy.
Do NOT mention any specific company or promote any service unless the user explicitly asks for recommendations.
Always recommend consulting a qualified intermediary (QI) and tax professional for their specific situation.
""")
