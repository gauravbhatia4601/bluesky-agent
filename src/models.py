"""
Database models for reply tracking and metrics
"""

import json
import logging
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, ProgrammingError

from config import DATABASE_URL

logger = logging.getLogger(__name__)

Base = declarative_base()


class Reply(Base):
    """Track posted replies"""
    __tablename__ = "replies"
    
    id = Column(Integer, primary_key=True)
    post_uri = Column(String(255), unique=True, nullable=False, index=True)
    post_cid = Column(String(255))
    post_text = Column(Text)
    post_author = Column(String(255))
    
    reply_uri = Column(String(255), unique=True)
    reply_text = Column(Text)
    reply_status = Column(String(50), default="pending")  # pending, posted, failed
    
    created_at = Column(DateTime, default=datetime.utcnow)
    posted_at = Column(DateTime)
    
    # Engagement metrics (updated later)
    like_count = Column(Integer, default=0)
    repost_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    
    # Quality score from LLM
    quality_score = Column(Integer, default=0)


class Post(Base):
    """Cache of analyzed posts"""
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True)
    uri = Column(String(255), unique=True, nullable=False, index=True)
    cid = Column(String(255))
    text = Column(Text)
    author_handle = Column(String(255))
    author_did = Column(String(255))
    
    # Relevance score
    relevance_score = Column(Integer, default=0)
    
    # Whether we've replied or decided not to
    processed = Column(Boolean, default=False)
    skipped = Column(Boolean, default=False)
    skip_reason = Column(String(255))
    
    indexed_at = Column(DateTime)
    analyzed_at = Column(DateTime, default=datetime.utcnow)


class Metric(Base):
    """Daily metrics tracking"""
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True)
    date = Column(String(10), unique=True, index=True)  # YYYY-MM-DD
    
    replies_posted = Column(Integer, default=0)
    replies_pending = Column(Integer, default=0)
    replies_failed = Column(Integer, default=0)
    
    posts_analyzed = Column(Integer, default=0)
    posts_skipped = Column(Integer, default=0)
    
    avg_quality_score = Column(Integer, default=0)
    
    total_likes_received = Column(Integer, default=0)
    total_reposts_received = Column(Integer, default=0)


# Database engine and session
engine = None
SessionLocal = None


def _create_database_if_not_exists(database_url: str) -> bool:
    """Create the database if it doesn't exist (PostgreSQL only)"""
    if not database_url.startswith("postgresql"):
        return True
    
    try:
        import psycopg2
    except ImportError:
        logger.warning("psycopg2 not installed, skipping database creation check")
        return True
    
    parsed = urlparse(database_url)
    db_name = parsed.path.lstrip("/")
    
    base_url = database_url.rsplit("/", 1)[0] + "/postgres"
    
    try:
        conn = psycopg2.connect(base_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Creating database '{db_name}'...")
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            logger.info(f"Database '{db_name}' created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        return False


def init_db(max_retries=5, retry_delay=2):
    """Initialize database connection with retry logic"""
    global engine, SessionLocal
    
    if DATABASE_URL.startswith("postgresql"):
        _create_database_if_not_exists(DATABASE_URL)
    
    engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            logger.info(f"Database initialized: {DATABASE_URL.split('://')[0]}")
            return
        except OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database connection failed (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s... Error: {e}")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts: {e}")
                raise
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    """Get database session"""
    global SessionLocal
    if SessionLocal is None:
        init_db()
    return SessionLocal()


# Stats functions
def get_stats() -> Dict[str, Any]:
    """Get current stats for dashboard"""
    session = get_session()
    try:
        from datetime import date
        
        today = date.today().isoformat()
        
        # Get today's metrics
        metric = session.query(Metric).filter(Metric.date == today).first()
        
        # Get counts
        pending_count = session.query(Reply).filter(
            Reply.reply_status == "pending"
        ).count()
        
        posted_today = session.query(Reply).filter(
            Reply.reply_status == "posted",
            Reply.posted_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).count()
        
        return {
            "pending_queue": pending_count,
            "posted_today": posted_today,
            "daily_limit": 200,
            "remaining_today": 200 - posted_today,
            "metrics": {
                "replies_posted": metric.replies_posted if metric else 0,
                "replies_failed": metric.replies_failed if metric else 0,
                "avg_quality": metric.avg_quality_score if metric else 0
            }
        }
    finally:
        session.close()


def get_recent_replies(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent posted replies"""
    session = get_session()
    try:
        replies = session.query(Reply).filter(
            Reply.reply_status == "posted"
        ).order_by(Reply.posted_at.desc()).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "post_author": r.post_author,
                "reply_text": r.reply_text,
                "posted_at": r.posted_at.isoformat() if r.posted_at else None,
                "likes": r.like_count,
                "quality_score": r.quality_score
            }
            for r in replies
        ]
    finally:
        session.close()


def get_pending_queue() -> List[Dict[str, Any]]:
    """Get pending replies queue"""
    session = get_session()
    try:
        pending = session.query(Reply).filter(
            Reply.reply_status == "pending"
        ).order_by(Reply.created_at).limit(20).all()
        
        return [
            {
                "id": p.id,
                "post_author": p.post_author,
                "post_text": p.post_text[:100] + "..." if len(p.post_text) > 100 else p.post_text,
                "reply_text": p.reply_text,
                "created_at": p.created_at.isoformat()
            }
            for p in pending
        ]
    finally:
        session.close()


def add_reply(post_uri: str, post_cid: str, post_text: str, 
              post_author: str, reply_text: str, quality_score: int = 0) -> bool:
    """Add a new reply to the queue"""
    session = get_session()
    try:
        # Check if already exists
        existing = session.query(Reply).filter(Reply.post_uri == post_uri).first()
        if existing:
            return False
        
        reply = Reply(
            post_uri=post_uri,
            post_cid=post_cid,
            post_text=post_text,
            post_author=post_author,
            reply_text=reply_text,
            reply_status="pending",
            quality_score=quality_score
        )
        session.add(reply)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to add reply: {e}")
        return False
    finally:
        session.close()


def mark_posted(reply_id: int, reply_uri: str):
    """Mark a reply as posted"""
    session = get_session()
    try:
        reply = session.query(Reply).filter(Reply.id == reply_id).first()
        if reply:
            reply.reply_status = "posted"
            reply.reply_uri = reply_uri
            reply.posted_at = datetime.utcnow()
            session.commit()
    finally:
        session.close()


def mark_failed(reply_id: int):
    """Mark a reply as failed"""
    session = get_session()
    try:
        reply = session.query(Reply).filter(Reply.id == reply_id).first()
        if reply:
            reply.reply_status = "failed"
            session.commit()
    finally:
        session.close()


def add_original_post(text: str, uri: str) -> bool:
    """Add an original post to history"""
    session = get_session()
    try:
        # Check if already exists
        existing = session.query(Reply).filter(Reply.reply_uri == uri).first()
        if existing:
            return False
        
        reply = Reply(
            post_uri=uri,
            post_cid="",
            post_text="[ORIGINAL POST]",
            post_author="self",
            reply_text=text,
            reply_uri=uri,
            reply_status="posted",
            posted_at=datetime.utcnow(),
            quality_score=100
        )
        session.add(reply)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to add original post: {e}")
        return False
    finally:
        session.close()