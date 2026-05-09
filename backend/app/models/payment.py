"""
Payment model for managing payment transactions.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Payment(Base):
    """Payment table for storing payment transaction records."""
    
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    rescue_request_id = Column(Integer, ForeignKey("rescue_requests.id"), unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)  # cash, momo, vnpay, card
    transaction_id = Column(String(100))  # External transaction ID from payment gateway
    status = Column(String(20), default="pending")  # pending, success, failed, refunded
    payment_url = Column(String(500))  # Payment gateway URL for online payment
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = Column(DateTime)
    
    # Relationships
    rescue_request = relationship("RescueRequest", back_populates="payment")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, request_id={self.rescue_request_id}, status='{self.status}')>"
