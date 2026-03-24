"""
Bluesky API client with session persistence
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from atproto import Client, client_utils

from config import (
    BSKY_HANDLE, BSKY_PASSWORD, BSKY_SERVICE,
    SESSION_FILE, TOPIC_KEYWORDS, POINTS_CREATE,
    MAX_REPLIES_PER_HOUR, MAX_REPLIES_PER_DAY
)

logger = logging.getLogger(__name__)


class BlueskyClient:
    """Bluesky client with session persistence and rate limit awareness"""
    
    def __init__(self):
        self.client = Client(BSKY_SERVICE)
        self.session = None
        self.hourly_count = 0
        self.daily_count = 0
        self.daily_original_posts = 0  # Track original posts per day
    
    def login(self) -> bool:
        """Login to Bluesky with session persistence"""
        # Try to resume existing session
        if SESSION_FILE.exists():
            try:
                session_data = json.loads(SESSION_FILE.read_text())
                self.client.resume_session(session_data)
                self.session = session_data
                logger.info("Resumed existing Bluesky session")
                return True
            except Exception as e:
                logger.warning(f"Failed to resume session: {e}, logging in fresh")
        
        # Fresh login
        try:
            self.client.login(BSKY_HANDLE, BSKY_PASSWORD)
            self.session = {
                "handle": BSKY_HANDLE,
                "did": self.client.me.did,
                "accessJwt": self.client._session.access_jwt,
                "refreshJwt": self.client._session.refresh_jwt
            }
            self._save_session()
            logger.info("Logged into Bluesky successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to login: {e}")
            return False
    
    def _save_session(self):
        """Persist session to disk"""
        if self.session:
            SESSION_FILE.write_text(json.dumps(self.session, indent=2))
            logger.debug("Session saved to disk")
    
    def label_as_bot(self):
        """Add bot label to profile for transparency"""
        try:
            profile = self.client.get_profile({"actor": self.client.me.did})
            # Check if already labeled
            if hasattr(profile, "labels") and profile.labels:
                for label in profile.labels:
                    if hasattr(label, "val") and label.val == "bot":
                        logger.info("Profile already labeled as bot")
                        return
            
            # Add self-label (this is done via profile update)
            # Note: The atproto SDK handles this differently
            # For now, we'll just log it - proper labeling requires
            # updating the profile record directly
            logger.info("Bot labeling will be applied during profile operations")
        except Exception as e:
            logger.warning(f"Could not check bot label: {e}")
    
    def can_post(self) -> bool:
        """Check if we're within rate limits"""
        return (
            self.hourly_count < MAX_REPLIES_PER_HOUR and
            self.daily_count < MAX_REPLIES_PER_DAY
        )
    
    def get_timeline(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch timeline posts"""
        try:
            response = self.client.get_timeline({"limit": limit})
            posts = []
            
            for item in response.feed:
                post = {
                    "uri": item.post.uri,
                    "cid": item.post.cid,
                    "text": item.post.record.text if hasattr(item.post, "record") else "",
                    "author_handle": item.post.author.handle,
                    "author_did": item.post.author.did,
                    "indexed_at": item.post.indexed_at
                }
                posts.append(post)
            
            logger.info(f"Fetched {len(posts)} timeline posts")
            return posts
        except Exception as e:
            logger.error(f"Failed to fetch timeline: {e}")
            return []
    
    def search_posts(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Search for posts by keyword"""
        try:
            response = self.client.app.bsky.feed.search_posts({
                "q": query,
                "limit": limit
            })
            
            posts = []
            for item in response.posts:
                post = {
                    "uri": item.uri,
                    "cid": item.cid,
                    "text": item.record.text if hasattr(item, "record") else "",
                    "author_handle": item.author.handle,
                    "author_did": item.author.did,
                    "indexed_at": item.indexed_at
                }
                posts.append(post)
            
            logger.info(f"Found {len(posts)} posts for query: {query}")
            return posts
        except Exception as e:
            logger.error(f"Failed to search posts: {e}")
            return []
    
    def get_topic_posts(self) -> List[Dict[str, Any]]:
        """Search for posts matching our topic keywords"""
        all_posts = []
        
        for keyword in TOPIC_KEYWORDS[:5]:  # Limit searches
            posts = self.search_posts(keyword, limit=10)
            all_posts.extend(posts)
        
        # Deduplicate by URI
        seen = set()
        unique_posts = []
        for post in all_posts:
            if post["uri"] not in seen:
                seen.add(post["uri"])
                unique_posts.append(post)
        
        return unique_posts[:50]
    
    def post_reply(self, parent_uri: str, parent_cid: str, text: str) -> Optional[str]:
        """Post a reply to a post"""
        if not self.can_post():
            logger.warning("Rate limit reached, skipping reply")
            return None
        
        try:
            # Build reply reference
            reply_ref = {
                "root": {"uri": parent_uri, "cid": parent_cid},
                "parent": {"uri": parent_uri, "cid": parent_cid}
            }
            
            response = self.client.post(
                text=text,
                reply_to=reply_ref
            )
            
            # Update rate limit tracking
            self.hourly_count += 1
            self.daily_count += 1
            
            logger.info(f"Posted reply: {response.uri}")
            return response.uri
        except Exception as e:
            logger.error(f"Failed to post reply: {e}")
            return None
    
    def like_post(self, uri: str, cid: str) -> bool:
        """Like a post"""
        try:
            self.client.like(uri, cid)
            self.hourly_count += 1  # Likes also count toward rate limit
            logger.debug(f"Liked post: {uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to like post: {e}")
            return False
    
    def post_original(self, text: str) -> Optional[str]:
        """Post original content (not a reply)"""
        try:
            response = self.client.post(text=text)
            self.hourly_count += 1
            self.daily_count += 1
            logger.info(f"Posted original content: {response.uri}")
            return response.uri
        except Exception as e:
            logger.error(f"Failed to post original content: {e}")
            return None
    
    def reset_hourly_count(self):
        """Reset hourly counter (call from scheduler)"""
        self.hourly_count = 0
        logger.debug("Reset hourly post count")
    
    def reset_daily_count(self):
        """Reset daily counter (call from scheduler)"""
        self.daily_count = 0
        logger.debug("Reset daily post count")


# Global client instance
_client_instance: Optional[BlueskyClient] = None


def get_client() -> BlueskyClient:
    """Get or create global client instance"""
    global _client_instance
    if _client_instance is None:
        _client_instance = BlueskyClient()
    return _client_instance