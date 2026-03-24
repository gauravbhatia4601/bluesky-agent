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
    "API", "docker", "kubernetes", "cloud", "security"
]

# System prompt for LLM (user's tone preference)
SYSTEM_PROMPT = """You are a helpful, calm, and composed tech professional.
Reply to posts with high-IQ insights about software development, tech, and related topics.
Keep replies:
- Natural and conversational
- Concise (under 280 characters when possible)
- Authentic and not robotic
- Relevant to the post's context
- Avoid generic phrases like "Great point!" or "I agree!"
- Offer specific insights or ask thoughtful questions
- Match the tone of the original post

Reply as a knowledgeable peer, not a bot."""