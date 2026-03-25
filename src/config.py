import os
from pathlib import Path

# Bluesky credentials
BSKY_HANDLE = os.getenv("BSKY_HANDLE", "")
BSKY_PASSWORD = os.getenv("BSKY_PASSWORD", "")
BSKY_SERVICE = "https://bsky.social"

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bluesky.db")

# LLM endpoint
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://host.docker.internal:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.5:cloud")

# Rate limits (points per hour/day from docs)
RATE_LIMIT_POINTS_PER_HOUR = 5000
RATE_LIMIT_POINTS_PER_DAY = 35000

# Points per action
POINTS_CREATE = 3
POINTS_UPDATE = 2
POINTS_DELETE = 1

# Posting targets (100+ replies/day, 6 original posts/day)
MAX_REPLIES_PER_HOUR = 10  # Allow up to 10 per hour
MAX_REPLIES_PER_DAY = 150  # 150 replies per day max
MAX_ORIGINAL_POSTS_PER_DAY = 6  # 6 original posts per day

# Scheduling
TIMELINE_FETCH_INTERVAL_MINUTES = 2  # Generate replies every 2 min
POST_DELAY_MIN_SECONDS = 60
POST_DELAY_MAX_SECONDS = 180
REPLY_INTERVAL_MINUTES = 15  # Post replies every 15 minutes (96/day)
ORIGINAL_POST_INTERVAL_HOURS = 4  # Post original content every 4 hours (6/day)

# LLM settings
LLM_REQUEST_DELAY_SECONDS = 5  # Delay between LLM requests
MAX_REPLIES_PER_GENERATION = 5  # Max replies to generate per fetch

# Engagement settings
AUTO_LIKE_ON_REPLY = True  # Like every post we reply to

# Session persistence
SESSION_FILE = Path("/app/session.json")

# Dashboard
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_PORT = int(os.getenv("PORT", "5000"))

# Topics to prioritize (from user request)
TOPIC_KEYWORDS = [
    "tech", "developer", "software", "AI", "automation", "code",
    "programming", "SaaS", "startup", "self-hosted", "open-source",
    "API", "docker", "cloud", "security", "php", "laravel", "JS",
    "ollama", "cursor", "agentic AI"
]

# System prompt for LLM (user's tone preference)
SYSTEM_PROMPT = """You are an experienced software engineer and tech builder with deep expertise in AI, automation, and modern development. You've shipped real products, dealt with production issues, and learned from failures.

When replying:
- Draw from actual experience. Mention specific trade-offs, edge cases, or gotchas.
- Don't just agree. Push back when something doesn't sound right. Offer counter-perspectives.
- Match the post's structure and style. If it's a thread, reply in thread format. If it's technical, go technical.
- Keep it concise but dense with insight. No fluff.
- Avoid hedging phrases like "I think" or "In my opinion" — speak directly.
- Use specific technical details when relevant: libraries, versions, error messages, benchmarks.
- If something is genuinely good, acknowledge it briefly and add value (don't just compliment).
- If something is wrong or oversimplified, correct it without being condescending.
- Never mention you're an AI or bot.

Reply as someone who's been in the trenches, not a tutorial reader."""