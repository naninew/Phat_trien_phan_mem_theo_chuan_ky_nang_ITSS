"""
ChatMessage model for communication between customer and company.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class ChatMessage(Base):
    """Table for storing chat messages related to a rescue request."""
    
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    rescue_request_id = Column(Integer, ForeignKey("rescue_requests.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    rescue_request = relationship("RescueRequest", foreign_keys=[rescue_request_id])
    sender = relationship("User", foreign_keys=[sender_id])

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, request_id={self.rescue_request_id}, sender_id={self.sender_id})>"
