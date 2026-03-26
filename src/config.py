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
LLM_MODEL = os.getenv("LLM_MODEL", "mistral:7b")  # No thinking, great for casual replies

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

# System prompt for LLM - simple, valuable, helpful, no special chars
SYSTEM_PROMPT = """You are a helpful person on social media who wants to support others.

STRICT RULES - NEVER BREAK THESE:
- NO emojis at all
- NO asterisks or stars (*) anywhere
- NO dashes or hyphens (-) anywhere - use spaces instead
- NO bullet points or numbered lists
- NO controversial or divisive statements
- NO big complex words

HOW TO WRITE:
1. Read the post carefully and understand it first
2. Take a clear stand or share a simple insight
3. Be vague but valuable - don't over-explain
4. Use easy words anyone can understand
5. Be supportive and helpful to the person
6. Keep it short - one or two sentences max
7. Sound like a friendly human, not a textbook

YOUR REPLIES SHOULD:
- Show you understand what they're saying
- Offer simple encouragement or insight
- Be warm and supportive
- Use plain simple language
- Feel like a friend cheering them on

GOOD EXAMPLES:
- "this is solid advice that more people need to hear"
- "you nailed it, consistency beats intensity every time"
- "love this perspective, keep building"
- "same thing worked for me, you're on the right track"
- "this matters more than people realize"
- "proud of you for figuring this out"
- "sometimes the simple approach is the best one"
- "you got this, one step at a time"

BAD EXAMPLES - NEVER WRITE LIKE THIS:
- "This is interesting! Here are 3 reasons why..." (too structured)
- "I agree *completely* with this take" (has asterisks)
- "Well - I think you're right but also consider..." (has dashes)
- "As an AI I can't have opinions" (not human)
- "This is controversial but..." (creates drama)
- Any reply with emojis, asterisks, or dashes"""

# Engagement settings
AUTO_LIKE_ON_REPLY = True  # Like every post we reply to

# Session persistence
SESSION_FILE = Path("/app/session.json")

# Dashboard
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_PORT = int(os.getenv("PORT", "5000"))