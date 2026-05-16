"""
Communication models for managing messages and notifications.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class Message(Base):
    """Message table for chat between customer and company."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("rescue_requests.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_type = Column(String(50), nullable=False)  # Customer / Company
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    sent_time = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    request = relationship("RescueRequest", backref="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])

class Notification(Base):
    """Notification table for system alerts."""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_id = Column(Integer, ForeignKey("rescue_requests.id"), nullable=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    sent_time = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    receiver = relationship("User", foreign_keys=[receiver_id])
    request = relationship("RescueRequest", backref="notifications")
