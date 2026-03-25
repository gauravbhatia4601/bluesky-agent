"""
LLM client for generating human-like replies
"""

import json
import logging
import requests
from typing import Optional, List

from config import LLM_ENDPOINT, LLM_MODEL, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for generating replies using Ollama/GLM-5"""
    
    def __init__(self, endpoint: str = LLM_ENDPOINT, model: str = LLM_MODEL):
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout = 60
    
    def _check_endpoint_available(self) -> bool:
        """Check if LLM endpoint is reachable"""
        try:
            response = requests.get(f"{self.endpoint}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_reply(
        self,
        post_text: str,
        author_handle: str,
        context: Optional[str] = None,
        max_length: int = 280
    ) -> Optional[str]:
        """Generate a human-like reply to a post"""
        
        prompt = f"""Post by @{author_handle}:
"{post_text}"

{f"Context: {context}" if context else ""}

Generate a brief, natural, insightful reply (under {max_length} characters).
Be conversational and authentic. Match the tone of the original post.
Avoid generic phrases. Offer specific insights or ask thoughtful questions.
Do not mention you are an AI or bot.

Reply:"""

        try:
            response = requests.post(
                f"{self.endpoint}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": SYSTEM_PROMPT,
                    "stream": False,
                    "options": {
                        "temperature": 0.8,
                        "top_p": 0.9,
                        "num_predict": 100
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                reply_text = data.get("response", "").strip()
                
                # Clean up the reply
                reply_text = self._clean_reply(reply_text, max_length)
                
                if reply_text:
                    logger.debug(f"Generated reply: {reply_text[:50]}...")
                    return reply_text
                else:
                    logger.warning("Empty reply generated")
                    return None
            else:
                logger.error(f"LLM request failed: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("LLM request timed out")
            return None
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return None
    
    def generate_multiple_options(
        self,
        post_text: str,
        author_handle: str,
        context: Optional[str] = None,
        count: int = 3
    ) -> List[str]:
        """Generate multiple reply options to choose from"""
        replies = []
        
        for _ in range(count):
            reply = self.generate_reply(post_text, author_handle, context)
            if reply:
                replies.append(reply)
        
        return replies
    
    def _clean_reply(self, text: str, max_length: int) -> str:
        """Clean and truncate reply"""
        # Remove common LLM artifacts
        text = text.strip()
        
        # Remove quotes if the model wrapped the reply
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        
        # Remove any "Reply:" prefix
        if text.lower().startswith("reply:"):
            text = text[6:].strip()
        
        # Remove any @ mentions at the start (we'll add the real one)
        if text.startswith("@"):
            # Find end of mention
            space_idx = text.find(" ")
            if space_idx > 0:
                text = text[space_idx:].strip()
        
        # Truncate to max length (soft truncate at word boundary)
        if len(text) > max_length:
            # Find last space before max_length
            last_space = text[:max_length].rfind(" ")
            if last_space > max_length - 20:  # Only truncate at word if close enough
                text = text[:last_space]
            else:
                text = text[:max_length-3] + "..."
        
        return text if len(text) > 10 else ""  # Reject very short replies
    
    def score_reply(self, reply: str, original_text: str) -> float:
        """Score a reply for quality (0.0 to 1.0)"""
        score = 1.0
        
        # Penalize very short replies
        if len(reply) < 20:
            score -= 0.3
        
        # Penalize generic phrases
        generic_phrases = [
            "great post", "i agree", "interesting", "thanks for sharing",
            "good point", "nice", "cool", "awesome"
        ]
        lower_reply = reply.lower()
        for phrase in generic_phrases:
            if phrase in lower_reply:
                score -= 0.2
        
        # Bonus for questions (engagement)
        if "?" in reply:
            score += 0.1
        
        # Bonus for technical terms
        tech_terms = ["api", "code", "build", "deploy", "server", "data",
                      "system", "framework", "library", "algorithm"]
        for term in tech_terms:
            if term in lower_reply:
                score += 0.05
        
        return max(0.0, min(1.0, score))
    
    def generate_original_post(
        self,
        topics: List[str],
        style: str = "insight"
    ) -> Optional[str]:
        """Generate original post content"""
        
        topic_str = ", ".join(topics[:3])
        
        style_prompts = {
            "insight": f"Share a specific insight or lesson learned about {topic_str}. Be concrete and opinionated.",
            "tip": f"Share a practical tip about {topic_str} that most people get wrong.",
            "opinion": f"Share a contrarian or nuanced opinion about {topic_str}. Take a stance.",
            "question": f"Ask a thought-provoking question about {topic_str} that makes people think."
        }
        
        prompt = f"""Generate a short social media post (under 280 characters).

{style_prompts.get(style, style_prompts['insight'])}

Requirements:
- Be specific, not generic
- Sound like an experienced practitioner, not a tutorial
- No hedging ("I think", "in my opinion")
- One clear idea only
- No hashtags unless genuinely useful
- No call-to-action ("What do you think?")

Post:"""

        try:
            response = requests.post(
                f"{self.endpoint}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": SYSTEM_PROMPT,
                    "stream": False,
                    "options": {
                        "temperature": 0.9,
                        "top_p": 0.95,
                        "num_predict": 80
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                post_text = data.get("response", "").strip()
                post_text = self._clean_reply(post_text, 280)
                
                if post_text and len(post_text) > 15:
                    logger.debug(f"Generated original post: {post_text[:50]}...")
                    return post_text
                else:
                    logger.warning("Original post too short or empty")
                    return None
            else:
                logger.error(f"LLM request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return None


# Global instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client