"""
Review model for managing customer reviews and ratings.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Review(Base):
    """Review table for storing customer reviews and ratings."""
    
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    rescue_request_id = Column(Integer, ForeignKey("rescue_requests.id"), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("rescue_companies.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text)
    is_approved = Column(Boolean, default=True)  # For admin moderation
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rescue_request = relationship("RescueRequest", back_populates="review")
    user = relationship("User")
    company = relationship("RescueCompany")
    
    def __repr__(self):
        return f"<Review(id={self.id}, request_id={self.rescue_request_id}, rating={self.rating})>"
