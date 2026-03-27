"""
Scheduler jobs for timeline fetch, reply posting, and original content
"""

import random
import logging
import time
from datetime import datetime

from bluesky_client import get_client
from llm_client import get_llm_client
from models import add_reply, mark_posted, mark_failed, get_pending_queue, add_original_post
from config import (
    POST_DELAY_MIN_SECONDS, POST_DELAY_MAX_SECONDS,
    MAX_REPLIES_PER_HOUR, MAX_REPLIES_PER_DAY, MAX_ORIGINAL_POSTS_PER_DAY,
    AUTO_LIKE_ON_REPLY, TOPIC_KEYWORDS, LLM_REQUEST_DELAY_SECONDS, MAX_REPLIES_PER_GENERATION
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
    already_replied = 0
    
    for post in posts_to_process:
        # Stop if we've generated enough replies
        if replies_added >= MAX_REPLIES_PER_GENERATION:
            logger.info(f"Reached max replies per generation ({MAX_REPLIES_PER_GENERATION}), stopping")
            break
        
        # Skip own posts
        if client.handle and post.get("author_handle") == client.handle:
            continue
        
        # Check relevance - must contain at least one topic keyword
        post_text = post.get("text", "").lower()
        is_relevant = any(kw.lower() in post_text for kw in TOPIC_KEYWORDS)
        
        if not is_relevant:
            posts_filtered += 1
            continue
        
        # Check if we already replied to this post
        from models import get_session, Reply
        session = get_session()
        existing_reply = session.query(Reply).filter(Reply.post_uri == post["uri"]).first()
        session.close()
        
        if existing_reply:
            already_replied += 1
            logger.debug(f"Already replied to post by @{post.get('author_handle')}")
            continue
        
        # Generate reply with delay between requests
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
                
                # Add delay between LLM requests to avoid rate limiting
                if replies_added < MAX_REPLIES_PER_GENERATION:
                    logger.debug(f"Waiting {LLM_REQUEST_DELAY_SECONDS}s before next LLM request...")
                    time.sleep(LLM_REQUEST_DELAY_SECONDS)
        else:
            logger.debug(f"Reply score too low ({score}): {reply_text[:50]}...")
    
    logger.info(f"=== TIMELINE FETCH COMPLETE: {replies_added} replies added, {posts_filtered} filtered, {llm_errors} LLM errors, {already_replied} already replied ===")


def post_pending_replies():
    """Post pending replies aggressively"""
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
    
    # Post up to 10 replies per run with 3 second delays
    posts_to_make = min(10, len(pending))
    logger.info(f"Will post {posts_to_make} replies this run")
    
    posted_count = 0
    for i in range(posts_to_make):
        reply_data = pending[i]
        logger.info(f"Posting reply {i+1}/{posts_to_make} - ID {reply_data['id']} to @{reply_data['post_author']}")
        
        # Check rate limit before each post
        if not client.can_post():
            logger.warning(f"Rate limit reached after {posted_count} posts")
            break
        
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
                posted_count += 1
                
                # Auto-like the original post after replying
                if AUTO_LIKE_ON_REPLY:
                    try:
                        client.like_post(reply_data["post_uri"], reply_data["post_cid"])
                    except Exception as e:
                        logger.debug(f"Could not like post: {e}")
            else:
                mark_failed(reply_data["id"])
                logger.error(f"✗ Failed to post reply ID {reply_data['id']}")
        except Exception as e:
            logger.error(f"✗ Exception posting reply: {e}")
            mark_failed(reply_data["id"])
        
        # Add 3 second delay between posts (except after last one)
        if i < posts_to_make - 1:
            time.sleep(3)
    
    logger.info(f"=== POST PENDING REPLIES COMPLETE: Posted {posted_count} replies ===")


def create_original_post():
    """Create original content (2 posts/day)"""
    logger.info("=== CREATING ORIGINAL POST JOB STARTING ===")
    
    client = get_client()
    llm = get_llm_client()
    
    logger.info(f"Current daily original posts: {client.daily_original_posts}/{MAX_ORIGINAL_POSTS_PER_DAY}")
    
    # Check if we've hit daily limit
    if client.daily_original_posts >= MAX_ORIGINAL_POSTS_PER_DAY:
        logger.info("Daily original post limit reached, skipping")
        return
    
    logger.info("Generating original post content...")
    # Generate original post based on topics
    post_text = llm.generate_original_post(
        topics=TOPIC_KEYWORDS[:5],  # Use top 5 topics
        style="insight"  # insight, tip, opinion, question
    )
    
    if not post_text:
        logger.warning("Failed to generate original post - LLM returned empty")
        return
    
    logger.info(f"Generated post content ({len(post_text)} chars): {post_text[:100]}...")
    
    # Post it
    try:
        logger.info("Attempting to post original content to Bluesky...")
        post_uri = client.post_original(text=post_text)
        if post_uri:
            add_original_post(text=post_text, uri=post_uri)
            client.daily_original_posts += 1
            logger.info(f"✓ Successfully posted original content: {post_uri}")
            logger.info(f"Daily original post count now: {client.daily_original_posts}")
        else:
            logger.error("post_original returned None - post failed")
    except Exception as e:
        logger.error(f"✗ Failed to post original content: {e}")
        import traceback
        logger.error(traceback.format_exc())


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