"""
Bluesky Agent - Main entry point
Starts the scheduler and dashboard server
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, render_template, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import (
    DASHBOARD_HOST, DASHBOARD_PORT, SESSION_FILE,
    TIMELINE_FETCH_INTERVAL_MINUTES
)
from bluesky_client import BlueskyClient
from scheduler import run_timeline_fetch, post_pending_replies, create_original_post, reset_hourly_counters, reset_daily_counters
from models import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Ensure session file exists
if not SESSION_FILE.exists():
    try:
        SESSION_FILE.touch()
        logger.info(f"Created session file: {SESSION_FILE}")
    except Exception as e:
        logger.warning(f"Could not create session file: {e}")

# Initialize Flask app
app = Flask(__name__, template_folder="../templates")

# Global state
client = None
scheduler = None


@app.route("/")
def dashboard():
    """Render main dashboard"""
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    """Get agent status"""
    from models import get_stats
    stats = get_stats()
    return jsonify({
        "status": "running",
        "stats": stats
    })


@app.route("/api/replies")
def api_replies():
    """Get recent replies"""
    from models import get_recent_replies
    replies = get_recent_replies(limit=50)
    return jsonify({"replies": replies})


@app.route("/api/queue")
def api_queue():
    """Get pending queue"""
    from models import get_pending_queue
    queue = get_pending_queue()
    return jsonify({"queue": queue})


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


def setup_scheduler():
    """Setup background scheduler for timeline fetch and reply posting"""
    global scheduler
    scheduler = BackgroundScheduler(timezone="UTC")
    
    # Fetch timeline every N minutes
    scheduler.add_job(
        run_timeline_fetch,
        trigger=IntervalTrigger(minutes=TIMELINE_FETCH_INTERVAL_MINUTES),
        id="timeline_fetch",
        name="Fetch timeline and generate replies",
        replace_existing=True
    )
    
    # Post replies every 15 minutes (fits 50/day target)
    scheduler.add_job(
        post_pending_replies,
        trigger=IntervalTrigger(minutes=15),
        id="post_replies",
        name="Post pending replies",
        replace_existing=True
    )
    
    # Create original posts every 12 hours (2/day)
    scheduler.add_job(
        create_original_post,
        trigger=IntervalTrigger(hours=12),
        id="original_post",
        name="Create original content",
        replace_existing=True
    )
    
    # Reset hourly counters
    scheduler.add_job(
        reset_hourly_counters,
        trigger=IntervalTrigger(hours=1),
        id="reset_hourly",
        name="Reset hourly counters",
        replace_existing=True
    )
    
    # Reset daily counters at midnight
    scheduler.add_job(
        reset_daily_counters,
        trigger=IntervalTrigger(hours=24),
        id="reset_daily",
        name="Reset daily counters",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started with jobs: timeline_fetch, post_replies, original_post, counters")


def main():
    """Main entry point"""
    global client
    
    logger.info("Starting Bluesky Agent...")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Login to Bluesky
    client = BlueskyClient()
    if not client.login():
        logger.error("Failed to login to Bluesky")
        sys.exit(1)
    
    # Add bot label to profile
    client.label_as_bot()
    
    # Setup scheduler
    setup_scheduler()
    
    # Run initial timeline fetch
    run_timeline_fetch()
    
    # Start Flask dashboard
    logger.info(f"Dashboard available at http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
    app.run(
        host=DASHBOARD_HOST,
        port=DASHBOARD_PORT,
        debug=False,
        use_reloader=False
    )


if __name__ == "__main__":
    main()