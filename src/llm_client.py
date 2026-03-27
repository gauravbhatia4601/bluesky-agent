"""
LLM client for generating human-like replies
"""

import json
import logging
import time
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
        max_length: int = 280,
        max_retries: int = 2
    ) -> Optional[str]:
        """Generate a human-like reply to a post"""
        
        # Check if endpoint is available first
        if not self._check_endpoint_available():
            logger.warning(f"LLM endpoint {self.endpoint} not available")
            return None
        
        # Check if post is in English (basic check)
        if not self._is_english_text(post_text):
            logger.info(f"Skipping non-English post from @{author_handle}")
            return None
        
        prompt = f"""Post by @{author_handle}:
"{post_text}"

{f"Context: {context}" if context else ""}

Write a thoughtful, conversational reply (under {max_length} characters).
- Do NOT use any emojis
- Use simple everyday language
- Avoid dashes or bullet points
- Write in complete sentences
- Share specific technical insights
- Be direct and opinionated
- Never mention being an AI

Reply:"""

        for attempt in range(max_retries):
            try:
                logger.info(f"Calling LLM {self.model} (attempt {attempt + 1}/{max_retries})...")
                
                response = requests.post(
                    f"{self.endpoint}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                        # No num_predict cap - let LLM generate naturally
                    },
                    timeout=self.timeout
                )
                
                logger.info(f"LLM response status: {response.status_code}")
                
                if response.status_code == 404:
                    logger.error(f"Model '{self.model}' not found at {self.endpoint}")
                    logger.error(f"Full response: {response.text}")
                    return None
                
                if response.status_code != 200:
                    logger.error(f"LLM request failed: {response.status_code}")
                    logger.error(f"Full response: {response.text}")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in 2 seconds...")
                        time.sleep(2)
                        continue
                    return None
                
                data = response.json()
                raw_text = data.get("response", "")
                logger.info(f"Raw LLM response ({len(raw_text)} chars)")
                
                # Extract only the final 'response' channel from gpt-oss
                # gpt-oss uses channel markers:
                #   <|start|>assistant<|channel|>analysis<|message|> ... <|end|>
                #   <|start|>assistant<|channel|>response<|message|> ... <|end|>
                # We want only the response channel, not analysis/thinking
                
                import re
                
                # Pattern to match response channel
                response_pattern = r"<\|start\|>assistant<\|channel\|>response<\|message\|>(.*?)<\|end\|>"
                response_match = re.search(response_pattern, raw_text, flags=re.DOTALL | re.IGNORECASE)
                
                if response_match:
                    reply_text = response_match.group(1).strip()
                    logger.info(f"Extracted response channel ({len(reply_text)} chars)")
                else:
                    # No explicit response channel found, use raw text
                    reply_text = raw_text.strip()
                    logger.info(f"No response channel found, using raw text")
                
                logger.info(f"Final reply text: {reply_text[:200]}...")
                
                if not reply_text:
                    logger.warning(f"Empty response from LLM model {self.model}")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in 2 seconds...")
                        time.sleep(2)
                        continue
                    return None
                
                # Clean up the reply (truncation, artifact removal)
                reply_text = self._clean_reply(reply_text, max_length)
                
                if reply_text and len(reply_text) >= 10:
                    logger.info(f"Generated reply: {reply_text}")
                    return reply_text
                else:
                    logger.warning(f"Reply too short or empty after cleaning: '{reply_text}'")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in 2 seconds...")
                        time.sleep(2)
                        continue
                    return None
                    
            except requests.exceptions.Timeout:
                logger.error(f"LLM request timed out after {self.timeout}s")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in 2 seconds...")
                    time.sleep(2)
                    continue
                return None
            except requests.exceptions.ConnectionError:
                logger.error(f"Cannot connect to LLM endpoint: {self.endpoint}")
                return None
            except Exception as e:
                logger.error(f"LLM error: {e}")
                import traceback
                logger.error(traceback.format_exc())
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in 2 seconds...")
                    time.sleep(2)
                    continue
                return None
        
        return None
    
    def _is_english_text(self, text: str) -> bool:
        """Basic check if text is primarily English"""
        if not text:
            return False
        
        # Common non-English character ranges
        non_english_chars = [
            ord(c) for c in text 
            if ord(c) > 127 and ord(c) < 256  # Latin extended (European languages)
            or ord(c) >= 1024  # Cyrillic, Greek, etc.
        ]
        
        # If more than 20% non-ASCII chars, likely not English
        if len(non_english_chars) > len(text) * 0.2:
            return False
        
        # Common English words check
        english_indicators = ['the', 'is', 'are', 'was', 'were', 'have', 'has', 'this', 'that', 'with', 'for', 'and', 'but', 'not']
        text_lower = text.lower()
        
        # If at least one common English word found, consider it English
        for word in english_indicators:
            if f" {word} " in f" {text_lower} ":
                return True
        
        # If no non-English chars detected, assume English
        if len(non_english_chars) == 0:
            return True
        
        return False
    
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
        """Generate original post content - developer sharing insights on tech"""
        
        prompt = """You are a software developer sharing your thoughts on social media.

Write an original post about something tech-related that's on your mind. Could be:
- A recent tech trend or viral topic you have thoughts on
- Something you learned while building
- A problem you solved and what you discovered
- Your take on a tool, framework, or approach people are talking about
- A lesson from your experience building software

Keep it casual and human. Write like you're talking to other developers. No corporate speak. No tutorials. Just your genuine thoughts.

Make it 300-400 characters. Long enough to share real insight, short enough to read quickly.

Post:"""

        try:
            logger.info("Generating original post...")
            
            response = requests.post(
                f"{self.endpoint}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": SYSTEM_PROMPT,  # Add system prompt
                    "stream": False
                    # No num_predict cap - let LLM generate naturally
                },
                timeout=self.timeout
            )
            
            if response.status_code == 404:
                logger.error(f"Model '{self.model}' not found")
                return None
            
            if response.status_code != 200:
                logger.error(f"LLM request failed: {response.status_code}")
                return None
            
            data = response.json()
            raw_text = data.get("response", "")
            
            # Extract response channel for gpt-oss (same as reply generation)
            import re
            response_pattern = r"<\|start\|>assistant<\|channel\|>response<\|message\|>(.*?)<\|end\|>"
            response_match = re.search(response_pattern, raw_text, flags=re.DOTALL | re.IGNORECASE)
            
            if response_match:
                post_text = response_match.group(1).strip()
                logger.info(f"Extracted post from response channel ({len(post_text)} chars)")
            else:
                post_text = raw_text.strip()
                logger.info(f"No response channel, using raw text ({len(post_text)} chars)")
            
            logger.info(f"Generated post: {post_text[:200]}...")
            
            # Clean but allow longer posts (300-400 chars target)
            post_text = self._clean_reply(post_text, 400)
            
            if post_text and len(post_text) > 50:
                logger.info(f"Final post ({len(post_text)} chars): {post_text}")
                return post_text
            else:
                logger.warning(f"Generated post too short: {len(post_text)} chars")
                return None
                
        except Exception as e:
            logger.error(f"LLM error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None


# Global instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client