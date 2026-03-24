# Bluesky Agent

A self-hosted, autonomous Bluesky agent that monitors your timeline, generates human-like replies using your local LLM, and posts them with natural spacing — all within a Docker container.

## Features

- **Timeline Monitoring**: Fetches your Bluesky timeline every 15 minutes
- **Topic-Based Search**: Searches for posts matching tech keywords
- **LLM-Powered Replies**: Generates contextually relevant, natural replies using GLM-5 or any Ollama model
- **Rate Limit Aware**: Stays well under Bluesky's limits (50 posts/hour, 200/day)
- **Session Persistence**: Avoids re-login rate limits by saving sessions
- **Bot Labeling**: Self-labels as a bot for transparency
- **Clean Dashboard**: Real-time view of pending queue, posted replies, and stats
- **Docker-First**: Runs entirely in a container, database externally hosted

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/bluesky-agent.git
cd bluesky-agent
```

### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
BSKY_HANDLE=yourhandle.bsky.social
BSKY_PASSWORD=your-app-password
DATABASE_URL=postgresql://user:password@host:5432/bluesky_agent
LLM_ENDPOINT=http://host.docker.internal:11434
LLM_MODEL=glm-5:cloud
```

### 3. Run with Docker Compose

```bash
docker-compose up -d
```

### 4. Access Dashboard

Open http://localhost:5000 in your browser.

## Requirements

- **Bluesky Account**: Create an app password at Settings → Privacy & Security → App passwords
- **PostgreSQL**: External database for persistence
- **Ollama**: Local LLM endpoint (or use a cloud API)
- **Docker**: Container runtime

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `BSKY_HANDLE` | Your Bluesky handle | Required |
| `BSKY_PASSWORD` | App password from Bluesky | Required |
| `DATABASE_URL` | PostgreSQL connection string | `sqlite:///bluesky.db` |
| `LLM_ENDPOINT` | Ollama API endpoint | `http://host.docker.internal:11434` |
| `LLM_MODEL` | Model to use for replies | `glm-5:cloud` |
| `TZ` | Timezone | `UTC` |

## Rate Limits

Bluesky limits:
- 5,000 points/hour (CREATE = 3 points)
- 35,000 points/day

This agent is configured to:
- Max 50 replies/hour (~150 points)
- Max 200 replies/day (~600 points)

Well under the limits, with room for manual posts.

## Customization

### Topics

Edit `src/config.py` to change topic keywords:

```python
TOPIC_KEYWORDS = [
    "tech", "developer", "software", "AI", "automation",
    "code", "programming", "SaaS", "startup"
]
```

### Reply Tone

Edit `SYSTEM_PROMPT` in `src/config.py` to adjust the tone and style of replies.

### Scheduling

Edit `TIMELINE_FETCH_INTERVAL_MINUTES` in `src/config.py` to change fetch frequency.

## Architecture

```
┌─────────────────────────────────────────────┐
│  Dashboard (Flask) :5000                    │
│  - Real-time stats                          │
│  - Pending queue                           │
│  - Recent replies                           │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│  Scheduler (APScheduler)                   │
│  - Fetch timeline (every 15 min)           │
│  - Post replies (every 5 min)              │
│  - Reset counters (hourly/daily)           │
└─────────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌─────────────────┐   ┌─────────────────────┐
│ Bluesky Client  │   │ LLM Client          │
│ (atproto SDK)   │   │ (Ollama/GLM-5)      │
│ - Timeline       │   │ - Generate replies  │
│ - Search posts   │   │ - Score quality     │
│ - Post replies   │   │                     │
└─────────────────┘   └─────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  PostgreSQL (External)                      │
│  - Reply history                           │
│  - Engagement metrics                      │
│  - Daily stats                             │
└─────────────────────────────────────────────┘
```

## License

MIT

## Support

For issues or feature requests, open a GitHub issue.