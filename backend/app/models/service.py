"""
Service model for managing rescue services offered by companies.
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Service(Base):
    """Service table for storing rescue service types and pricing."""
    
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(100), nullable=False)  # e.g., "Vá lốp", "Kéo xe", "Kích bình"
    base_price = Column(Float, nullable=False)
    description = Column(Text)
    company_id = Column(Integer, ForeignKey("rescue_companies.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("RescueCompany", back_populates="services")
    rescue_requests = relationship("RescueRequest", back_populates="service")
    
    def __repr__(self):
        return f"<Service(id={self.id}, name='{self.service_name}', price={self.base_price})>"
