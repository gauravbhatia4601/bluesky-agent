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
LLM_MODEL = os.getenv("LLM_MODEL", "glm-5:cloud")

# Rate limits (points per hour/day from docs)
RATE_LIMIT_POINTS_PER_HOUR = 5000
RATE_LIMIT_POINTS_PER_DAY = 35000

# Points per action
POINTS_CREATE = 3
POINTS_UPDATE = 2
POINTS_DELETE = 1

# Safe posting limits (well under rate limit)
MAX_REPLIES_PER_HOUR = 50  # ~150 points
MAX_REPLIES_PER_DAY = 200  # ~600 points

# Scheduling
TIMELINE_FETCH_INTERVAL_MINUTES = 15
POST_DELAY_MIN_SECONDS = 30
POST_DELAY_MAX_SECONDS = 120

# Session persistence
SESSION_FILE = Path("/app/session.json")

# Dashboard
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_PORT = 5000

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