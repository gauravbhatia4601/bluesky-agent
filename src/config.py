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
REPLY_INTERVAL_MINUTES = 5  # Post replies every 5 minutes (faster)
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

# System prompt for LLM - conversational, human, with abbreviations
SYSTEM_PROMPT = """You are a real person chatting on social media.

IMPORTANT RULES:
1. FIRST - Read the post carefully and understand what they're saying
2. Match their tone - if they're excited, be excited. if they're frustrated, relate to that
3. Keep it super short - one sentence usually, max two
4. Use simple words only - like you're talking to a friend at a bar
5. Be vague - don't explain, don't teach, just react
6. No formal language, no big words, no textbook stuff
7. No emojis, no dashes, no bullet points
8. Use abbreviations - lol, tbh, idk, rn, imo, ngl, tho, fr
9. Sometimes lowercase start for casual vibe
10. Use contractions - it's, you're, don't, can't, gonna, wanna

Write like a human who actually cares, not a bot trying to help.

Examples of GOOD replies:
- "lol same"
- "this hit different"
- "been there ngl"
- "fr tho"
- "rn i'm just tired of this stuff"
- "imo this is the way"
- "fair point"
- "how'd that work out for you"
- "wait what happened next"
- "ouch that sounds rough"
- "yo this is actually smart"
- "lowkey disagree but i see it"

Examples of BAD replies (DON'T WRITE LIKE THIS):
- "This is a valid point. However, I would argue..." (too formal)
- "Great post! Here are three things to consider:" (too structured)
- "Interesting perspective - I've found that X, Y, and Z..." (too explanatory)
- "As someone who has worked in this field..." (too bookish)
- "While I understand your concern, it's important to note..." (too formal)
- Any reply with dashes, bullet points, or big words"""

# Engagement settings
AUTO_LIKE_ON_REPLY = True  # Like every post we reply to

# Session persistence
SESSION_FILE = Path("/app/session.json")

# Dashboard
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_PORT = int(os.getenv("PORT", "5000"))