"""
RescueCompany model for managing rescue service companies.
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class RescueCompany(Base):
    """Rescue company table for storing company information."""
    
    __tablename__ = "rescue_companies"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(200), nullable=False)
    address = Column(Text, nullable=False)
    hotline = Column(String(20), nullable=False)
    license_number = Column(String(50), unique=True, nullable=False)
    rating_avg = Column(Float, default=0.0)
    status = Column(String(20), default="active")  # active, suspended
    service_radius_km = Column(Float, default=10.0)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="company")
    services = relationship("Service", back_populates="company", cascade="all, delete-orphan")
    vehicles = relationship("RescueVehicle", back_populates="company", cascade="all, delete-orphan")
    rescue_requests = relationship("RescueRequest", back_populates="company")
    
    def __repr__(self):
        return f"<RescueCompany(id={self.id}, name='{self.company_name}', status='{self.status}')>"
