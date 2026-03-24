"""
Scheduler jobs for timeline fetch and reply posting
"""

import random
import logging
from datetime import datetime

from bluesky_client import get_client
from llm_client import get_llm_client
from models import add_reply, mark_posted, mark_failed, get_pending_queue
from config import (
    POST_DELAY_MIN_SECONDS, POST_DELAY_MAX_SECONDS,
    MAX_REPLIES_PER_HOUR
)

logger = logging.getLogger(__name__)


def run_timeline_fetch():
    """Fetch timeline and generate replies"""
    logger.info("Running timeline fetch...")
    
    client = get_client()
    llm = get_llm_client()
    
    # Get timeline posts
    timeline_posts = client.get_timeline(limit=50)
    
    # Get topic-based posts
    topic_posts = client.get_topic_posts()
    
    # Combine and deduplicate
    all_posts = {}
    for post in timeline_posts + topic_posts:
        all_posts[post["uri"]] = post
    
    posts_to_process = list(all_posts.values())
    logger.info(f"Processing {len(posts_to_process)} unique posts")
    
    # Generate replies for relevant posts
    replies_added = 0
    
    for post in posts_to_process:
        # Skip own posts
        if post.get("author_handle") == client.session.get("handle"):
            continue
        
        # Check relevance
        post_text = post.get("text", "").lower()
        
        # Generate reply
        reply_text = llm.generate_reply(
            post_text=post.get("text", ""),
            author_handle=post.get("author_handle", ""),
            context=f"Post from timeline"
        )
        
        if reply_text:
            # Score the reply
            score = llm.score_reply(reply_text, post.get("text", ""))
            
            # Only queue if score is good enough
            if score >= 0.5:
                success = add_reply(
                    post_uri=post["uri"],
                    post_cid=post["cid"],
                    post_text=post["text"],
                    post_author=post["author_handle"],
                    reply_text=reply_text,
                    quality_score=int(score * 100)
                )
                if success:
                    replies_added += 1
                    logger.debug(f"Queued reply for post by {post['author_handle']}")
    
    logger.info(f"Added {replies_added} replies to queue")


def post_pending_replies():
    """Post pending replies with natural delays"""
    logger.info("Posting pending replies...")
    
    client = get_client()
    
    # Check rate limit
    if not client.can_post():
        logger.warning("Rate limit reached, skipping post")
        return
    
    # Get pending queue
    pending = get_pending_queue()
    
    if not pending:
        logger.debug("No pending replies")
        return
    
    # Post first reply in queue
    reply_data = pending[0]
    
    # Add random delay (simulated by just posting)
    import time
    delay = random.randint(POST_DELAY_MIN_SECONDS, POST_DELAY_MAX_SECONDS)
    logger.info(f"Posting reply after {delay}s delay (simulated)")
    
    # Actually post
    reply_uri = client.post_reply(
        parent_uri=reply_data["post_uri"],
        parent_cid=reply_data["post_cid"],
        text=reply_data["reply_text"]
    )
    
    if reply_uri:
        mark_posted(reply_data["id"], reply_uri)
        logger.info(f"Successfully posted reply: {reply_uri}")
    else:
        mark_failed(reply_data["id"])
        logger.error(f"Failed to post reply: {reply_data['id']}")


def reset_hourly_counters():
    """Reset hourly counters (call from scheduler)"""
    client = get_client()
    client.reset_hourly_count()
    logger.info("Reset hourly counters")


def reset_daily_counters():
    """Reset daily counters (call from scheduler)"""
    client = get_client()
    client.reset_daily_count()
    logger.info("Reset daily counters")