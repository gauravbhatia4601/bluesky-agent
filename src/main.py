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

from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ThreadPoolExecutor

from config import (
    DASHBOARD_HOST, DASHBOARD_PORT, SESSION_FILE,
    TIMELINE_FETCH_INTERVAL_MINUTES, REPLY_INTERVAL_MINUTES, ORIGINAL_POST_INTERVAL_HOURS
)
from bluesky_client import BlueskyClient, get_client
from scheduler import run_timeline_fetch, post_pending_replies, create_original_post, reset_hourly_counters, reset_daily_counters
from models import init_db, add_original_post

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

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


@app.route("/api/timeline")
def api_timeline():
    """Get timeline posts"""
    client = get_client()
    if not client:
        return jsonify({"error": "Client not initialized"}), 500
    
    limit = request.args.get("limit", 20, type=int)
    posts = client.get_timeline(limit=limit)
    return jsonify({"posts": posts})


@app.route("/api/search")
def api_search():
    """Search posts"""
    client = get_client()
    if not client:
        return jsonify({"error": "Client not initialized"}), 500
    
    query = request.args.get("q", "")
    limit = request.args.get("limit", 20, type=int)
    
    if not query:
        return jsonify({"posts": []})
    
    posts = client.search_posts(query=query, limit=limit)
    return jsonify({"posts": posts})


@app.route("/api/post", methods=["POST"])
def api_post():
    """Post original content"""
    client = get_client()
    if not client:
        return jsonify({"success": False, "error": "Client not initialized"}), 500
    
    data = request.get_json()
    text = data.get("text", "").strip()
    
    if not text:
        return jsonify({"success": False, "error": "Text is required"}), 400
    
    uri = client.post_original(text=text)
    if uri:
        add_original_post(text=text, uri=uri)
        return jsonify({"success": True, "uri": uri})
    
    return jsonify({"success": False, "error": "Failed to post"}), 500


@app.route("/api/like", methods=["POST"])
def api_like():
    """Like a post"""
    client = get_client()
    if not client:
        return jsonify({"success": False, "error": "Client not initialized"}), 500
    
    data = request.get_json()
    uri = data.get("uri")
    cid = data.get("cid")
    
    if not uri or not cid:
        return jsonify({"success": False, "error": "uri and cid required"}), 400
    
    success = client.like_post(uri=uri, cid=cid)
    return jsonify({"success": success})


@app.route("/api/reply", methods=["POST"])
def api_reply():
    """Post a reply"""
    client = get_client()
    if not client:
        return jsonify({"success": False, "error": "Client not initialized"}), 500
    
    data = request.get_json()
    uri = data.get("uri")
    cid = data.get("cid")
    text = data.get("text", "").strip()
    
    if not uri or not cid or not text:
        return jsonify({"success": False, "error": "uri, cid, and text required"}), 400
    
    reply_uri = client.post_reply(parent_uri=uri, parent_cid=cid, text=text)
    if reply_uri:
        return jsonify({"success": True, "uri": reply_uri})
    
    return jsonify({"success": False, "error": "Failed to post reply"}), 500


def setup_scheduler():
    """Setup background scheduler for timeline fetch and reply posting"""
    global scheduler
    
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_executor(ThreadPoolExecutor())
    
    # Fetch timeline every N minutes
    scheduler.add_job(
        run_timeline_fetch,
        trigger=IntervalTrigger(minutes=TIMELINE_FETCH_INTERVAL_MINUTES),
        id="timeline_fetch",
        name="Fetch timeline and generate replies",
        replace_existing=True
    )
    
    # Post replies every 5 minutes
    scheduler.add_job(
        post_pending_replies,
        trigger=IntervalTrigger(minutes=REPLY_INTERVAL_MINUTES),
        id="post_replies",
        name="Post pending replies",
        replace_existing=True
    )
    
    # Create original posts every 4 hours
    scheduler.add_job(
        create_original_post,
        trigger=IntervalTrigger(hours=ORIGINAL_POST_INTERVAL_HOURS),
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
    logger.info(f"Scheduler started with jobs: timeline_fetch, post_replies (every {REPLY_INTERVAL_MINUTES}min), original_post, counters")


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
        logger.error("Failed to login to Bluesky - continuing anyway, will retry")
    
    # Add bot label to profile
    if client:
        client.label_as_bot()
    
    # Setup scheduler
    setup_scheduler()
    
    # Start Flask dashboard FIRST before timeline fetch
    # Run timeline fetch in background after Flask starts
    import threading
    def initial_fetch():
        import time
        time.sleep(5)  # Wait for Flask to start
        run_timeline_fetch()
    
    fetch_thread = threading.Thread(target=initial_fetch, daemon=True)
    fetch_thread.start()
    
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