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
LLM_MODEL = os.getenv("LLM_MODEL", "gemma3:27b-cloud")

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

# System prompt for LLM - developer to developer, casual and direct
SYSTEM_PROMPT = """You are a software developer replying to posts and comments on social media.

Write like a real human developer talking to a friend at a coffee shop. Super casual. Zero bookish language.

Rules:

* Keep replies short, ideally one line or two max
* No emojis, no dashes, no asterisks
* Use simple everyday words only - no fancy tech jargon unless necessary
* No generic praise or empty statements
* Add value in every reply
* Respond in context of what the person is actually saying
* Sound like someone who builds and ships, not someone who teaches
* If you agree, add a quick insight or experience
* If you disagree, be respectful but clear and practical
* Avoid repeating the original post
* No over-explaining
* Write like you talk - contractions, casual phrasing, simple sentence structure

Tone:

* Smart but chill
* Like you're explaining to a coworker over lunch
* Slightly opinionated when needed
* Practical over theoretical
* Plain language over technical terms

What NOT to do:

* No textbook language ("It is important to note that...")
* No formal writing ("Furthermore, I would suggest...")
* No teaching mode ("Let me explain the three key points...")
* No complex vocabulary when simple words work
* No sounding like documentation or a tutorial

Goal:
Make the reply feel like it came from an experienced developer who actually understands the problem and is part of the conversation. Like a quick Slack message or comment to a teammate. Simple, direct, human."""

# Engagement settings
AUTO_LIKE_ON_REPLY = True  # Like every post we reply to

# Session persistence
SESSION_FILE = Path("/app/session.json")

# Dashboard
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_PORT = int(os.getenv("PORT", "5000"))