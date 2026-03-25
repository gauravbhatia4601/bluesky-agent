"""
Scheduler jobs for timeline fetch, reply posting, and original content
"""

import random
import logging
from datetime import datetime

from bluesky_client import get_client
from llm_client import get_llm_client
from models import add_reply, mark_posted, mark_failed, get_pending_queue, add_original_post
from config import (
    POST_DELAY_MIN_SECONDS, POST_DELAY_MAX_SECONDS,
    MAX_REPLIES_PER_HOUR, MAX_REPLIES_PER_DAY, MAX_ORIGINAL_POSTS_PER_DAY,
    AUTO_LIKE_ON_REPLY, TOPIC_KEYWORDS
)

logger = logging.getLogger(__name__)


def run_timeline_fetch():
    """Fetch timeline and generate replies"""
    logger.info("=== TIMELINE FETCH JOB STARTING ===")
    
    client = get_client()
    if not client:
        logger.error("No client available - cannot fetch timeline")
        return
    
    llm = get_llm_client()
    
    # Get timeline posts
    logger.info("Fetching timeline posts...")
    timeline_posts = client.get_timeline(limit=50)
    logger.info(f"Got {len(timeline_posts)} timeline posts")
    
    # Get topic-based posts
    logger.info("Fetching topic posts...")
    topic_posts = client.get_topic_posts()
    logger.info(f"Got {len(topic_posts)} topic posts")
    
    # Combine and deduplicate
    all_posts = {}
    for post in timeline_posts + topic_posts:
        all_posts[post["uri"]] = post
    
    posts_to_process = list(all_posts.values())
    logger.info(f"Processing {len(posts_to_process)} unique posts")
    
    # Generate replies for relevant posts
    replies_added = 0
    posts_filtered = 0
    llm_errors = 0
    
    for post in posts_to_process:
        # Skip own posts
        if client.handle and post.get("author_handle") == client.handle:
            continue
        
        # Check relevance - must contain at least one topic keyword
        post_text = post.get("text", "").lower()
        is_relevant = any(kw.lower() in post_text for kw in TOPIC_KEYWORDS)
        
        if not is_relevant:
            posts_filtered += 1
            continue
        
        # Generate reply
        logger.debug(f"Generating reply for post by @{post.get('author_handle')}: {post_text[:50]}...")
        reply_text = llm.generate_reply(
            post_text=post.get("text", ""),
            author_handle=post.get("author_handle", ""),
            context=f"Post from timeline"
        )
        
        if not reply_text:
            llm_errors += 1
            continue
        
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
        else:
            logger.debug(f"Reply score too low ({score}): {reply_text[:50]}...")
    
    logger.info(f"=== TIMELINE FETCH COMPLETE: {replies_added} replies added, {posts_filtered} posts filtered, {llm_errors} LLM errors ===")


def post_pending_replies():
    """Post pending replies with natural delays + auto-like"""
    logger.info("=== POST PENDING REPLIES JOB STARTING ===")
    
    client = get_client()
    if not client:
        logger.error("No client available - cannot post replies")
        return
    
    logger.info(f"Client rate limits - hourly: {client.hourly_count}/{MAX_REPLIES_PER_HOUR}, daily: {client.daily_count}/{MAX_REPLIES_PER_DAY}")
    
    # Check rate limit
    if not client.can_post():
        logger.warning(f"Rate limit reached (hourly: {client.hourly_count}/{MAX_REPLIES_PER_HOUR}, daily: {client.daily_count}/{MAX_REPLIES_PER_DAY}), skipping post")
        return
    
    # Get pending queue
    pending = get_pending_queue()
    
    logger.info(f"Pending queue length: {len(pending)}")
    
    if not pending:
        logger.info("No pending replies in queue - nothing to post")
        return
    
    logger.info(f"Found {len(pending)} pending replies in queue")
    
    # Post first reply in queue
    reply_data = pending[0]
    logger.info(f"Attempting to post reply ID {reply_data['id']} to @{reply_data['post_author']}")
    logger.info(f"Reply text: {reply_data['reply_text'][:100]}...")
    
    # Actually post
    try:
        reply_uri = client.post_reply(
            parent_uri=reply_data["post_uri"],
            parent_cid=reply_data["post_cid"],
            text=reply_data["reply_text"]
        )
        
        if reply_uri:
            mark_posted(reply_data["id"], reply_uri)
            logger.info(f"✓ Successfully posted reply: {reply_uri}")
            
            # Auto-like the original post after replying
            if AUTO_LIKE_ON_REPLY:
                try:
                    client.like_post(reply_data["post_uri"], reply_data["post_cid"])
                    logger.info(f"✓ Liked original post")
                except Exception as e:
                    logger.warning(f"Could not like post: {e}")
        else:
            mark_failed(reply_data["id"])
            logger.error(f"✗ Failed to post reply ID {reply_data['id']}: post_reply returned None")
    except Exception as e:
        logger.error(f"✗ Exception posting reply: {e}")
        import traceback
        logger.error(traceback.format_exc())
        mark_failed(reply_data["id"])


def create_original_post():
    """Create original content (2 posts/day)"""
    logger.info("Creating original post...")
    
    client = get_client()
    llm = get_llm_client()
    
    # Check if we've hit daily limit
    if client.daily_original_posts >= MAX_ORIGINAL_POSTS_PER_DAY:
        logger.info("Daily original post limit reached")
        return
    
    # Generate original post based on topics
    post_text = llm.generate_original_post(
        topics=TOPIC_KEYWORDS[:5],  # Use top 5 topics
        style="insight"  # insight, tip, opinion, question
    )
    
    if not post_text:
        logger.warning("Failed to generate original post")
        return
    
    # Post it
    try:
        post_uri = client.post_original(text=post_text)
        if post_uri:
            add_original_post(text=post_text, uri=post_uri)
            client.daily_original_posts += 1
            logger.info(f"Posted original content: {post_uri}")
    except Exception as e:
        logger.error(f"Failed to post original content: {e}")


def reset_hourly_counters():
    """Reset hourly counters (call from scheduler)"""
    client = get_client()
    client.reset_hourly_count()
    logger.info("Reset hourly counters")


def reset_daily_counters():
    """Reset daily counters (call from scheduler)"""
    client = get_client()
    client.reset_daily_count()
    client.daily_original_posts = 0
    logger.info("Reset daily counters")