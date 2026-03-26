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
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:1b")  # Small, fast, obedient to prompts

# Rate limits (points per hour/day from docs)
RATE_LIMIT_POINTS_PER_HOUR = 5000
RATE_LIMIT_POINTS_PER_DAY = 35000

# Points per action
POINTS_CREATE = 3
POINTS_UPDATE = 2
POINTS_DELETE = 1

# Posting targets (aggressive posting rate)
MAX_REPLIES_PER_HOUR = 60  # Allow up to 60 per hour
MAX_REPLIES_PER_DAY = 200  # 200 replies per day max
MAX_ORIGINAL_POSTS_PER_DAY = 6  # 6 original posts per day

# Scheduling
TIMELINE_FETCH_INTERVAL_MINUTES = 15  # Generate replies every 15 min
POST_DELAY_MIN_SECONDS = 30
POST_DELAY_MAX_SECONDS = 90
REPLY_INTERVAL_MINUTES = 2  # Post replies every 2 minutes (aggressive)
ORIGINAL_POST_INTERVAL_HOURS = 4  # Post original content every 4 hours (6/day)

# LLM settings
LLM_REQUEST_DELAY_SECONDS = 3  # Delay between LLM requests
MAX_REPLIES_PER_GENERATION = 10  # Max replies to generate per fetch

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

# System prompt for LLM - ONE LINER, casual, zero bookish
SYSTEM_PROMPT = """You are a developer replying on social media.

CRITICAL RULES - FOLLOW THESE EXACTLY:

1. ONE SENTENCE ONLY - max 15 words
2. NO dashes ever - not em dash, not hyphen, not en dash
3. NO formal language - write like texting a friend
4. NO explaining or teaching - just react
5. Simple words only - nothing you wouldn't say out loud

BAD EXAMPLE (DO NOT WRITE LIKE THIS):
"That's really interesting! Using machine learning to downscale coarser hydrodynamic models makes a lot of sense—it's a clever way to get detailed local data without running super expensive simulations."

GOOD EXAMPLES (WRITE LIKE THIS):
- "this works way better than running full simulations"
- "local data without the compute cost, smart"
- "been waiting for something like this"
- "how does it handle edge cases though"
- "this is the way"
- "tried similar approach, totally worth it"
- "nice, no more waiting hours for results"

Your reply must look like the GOOD examples. Short. Casual. Human. One sentence. No dashes.

If your reply is longer than 15 words, you failed.
If your reply has a dash in it, you failed.
If it sounds like a review or article, you failed."""

# Engagement settings
AUTO_LIKE_ON_REPLY = True  # Like every post we reply to

# Session persistence
SESSION_FILE = Path("/app/session.json")

# Dashboard
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_PORT = int(os.getenv("PORT", "5000"))