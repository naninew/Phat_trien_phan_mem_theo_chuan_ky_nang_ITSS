"""
Community models for managing community posts and comments.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class CommunityPost(Base):
    """Community post table for storing user questions and discussions."""
    
    __tablename__ = "community_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    images = Column(Text)  # Comma-separated image URLs
    incident_type = Column(String(100), nullable=True)
    is_closed = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=True)  # For admin moderation
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    replies = relationship("CommunityReply", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CommunityPost(id={self.id}, title='{self.title}')>"


class CommunityReply(Base):
    """Community Reply table for storing responses to community posts."""
    
    __tablename__ = "community_replies"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=True)  # For admin moderation
    is_helpful = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    post = relationship("CommunityPost", back_populates="replies")
    user = relationship("User")
    
    def __repr__(self):
        return f"<CommunityReply(id={self.id}, post_id={self.post_id})>"
