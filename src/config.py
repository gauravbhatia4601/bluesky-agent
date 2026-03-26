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
LLM_MODEL = os.getenv("LLM_MODEL", "gemma3:27b-cloud")  # Cloud model, good quality

# Rate limits (points per hour/day from docs)
RATE_LIMIT_POINTS_PER_HOUR = 5000
RATE_LIMIT_POINTS_PER_DAY = 35000

# Points per action
POINTS_CREATE = 3
POINTS_UPDATE = 2
POINTS_DELETE = 1

# Posting targets (balanced posting rate)
MAX_REPLIES_PER_HOUR = 10  # Allow up to 10 per hour
MAX_REPLIES_PER_DAY = 150  # 150 replies per day max
MAX_ORIGINAL_POSTS_PER_DAY = 6  # 6 original posts per day

# Scheduling
TIMELINE_FETCH_INTERVAL_MINUTES = 30  # Generate replies every 30 min
POST_DELAY_MIN_SECONDS = 60
POST_DELAY_MAX_SECONDS = 180
REPLY_INTERVAL_MINUTES = 15  # Post replies every 15 minutes (1 at a time)
ORIGINAL_POST_INTERVAL_HOURS = 4  # Post original content every 4 hours (6/day)

# LLM settings
LLM_REQUEST_DELAY_SECONDS = 5  # Delay between LLM requests
MAX_REPLIES_PER_GENERATION = 5  # Max replies to generate per fetch

# Topics to prioritize - focused on tech, AI, CS, software development
TOPIC_KEYWORDS = [
    "artificial intelligence", "machine learning", "deep learning", "neural network",
    "LLM", "large language model", "AI model", "transformer", "attention mechanism",
    "python", "javascript", "typescript", "rust", "golang", "java", "cpp",
    "software engineering", "software development", "code review", "refactoring",
    "API design", "REST API", "GraphQL", "microservices", "system design",
    "cloud computing", "kubernetes", "docker", "devops", "CI/CD", "deployment",
    "database", "postgresql", "mongodb", "redis", "elasticsearch", "data engineering",
    "web development", "frontend", "backend", "full stack", "react", "vue", "angular",
    "mobile development", "ios", "android", "flutter", "react native",
    "security", "cybersecurity", "encryption", "authentication", "authorization",
    "performance", "optimization", "scalability", "load balancing", "caching",
    "testing", "unit test", "integration test", "TDD", "debugging",
    "git", "version control", "code review", "pull request", "agile", "scrum",
    "open source", "github", "gitlab", "linux", "bash", "shell scripting",
    "machine learning ops", "MLOps", "data science", "analytics", "visualization",
    "computer vision", "NLP", "natural language processing", "speech recognition",
    "reinforcement learning", "generative AI", "diffusion model", "stable diffusion",
    "vector database", "embedding", "RAG", "retrieval augmented generation",
    "prompt engineering", "fine tuning", "model training", "inference",
    "edge computing", "IoT", "embedded systems", "firmware", "hardware",
    "blockchain", "smart contract", "web3", "cryptocurrency", "defi",
    "startup", "SaaS", "product development", "MVP", "product market fit",
    "technical debt", "architecture", "design pattern", "clean code", "refactoring"
]

# System prompt for LLM - one-liner, vague, casual style
SYSTEM_PROMPT = """You are a casual tech person sharing thoughts on social media.

When replying:
- Write one-liners only (1-2 short sentences max)
- Be vague and casual, not explanatory
- No bookish or formal language
- No emojis
- No dashes or bullet points
- Use simple everyday words
- Only explain if something really needs it
- Sound like you're texting a friend
- Don't try to sound smart or helpful
- Just drop a quick thought and move on

Examples:
- "been there, takes forever to debug"
- "this aged well"
- "wait until you try it in prod"
- "classic move"""

# Engagement settings
AUTO_LIKE_ON_REPLY = True  # Like every post we reply to

# Session persistence
SESSION_FILE = Path("/app/session.json")

# Dashboard
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_PORT = int(os.getenv("PORT", "5000"))