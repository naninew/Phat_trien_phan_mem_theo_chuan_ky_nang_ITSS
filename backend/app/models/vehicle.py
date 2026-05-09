"""
RescueVehicle model for managing rescue vehicles.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class VehicleStatus(str, enum.Enum):
    """Vehicle status enumeration."""
    AVAILABLE = "available"
    ON_MISSION = "on_mission"
    MAINTENANCE = "maintenance"


class RescueVehicle(Base):
    """Rescue vehicle table for storing company vehicles information."""
    
    __tablename__ = "rescue_vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    license_plate = Column(String(20), nullable=False, index=True)
    vehicle_type = Column(String(50), nullable=False)  # e.g., "Xe cẩu", "Xe chở", "Xe kích bình"
    capacity = Column(String(50))  # Weight capacity or description
    status = Column(String(20), default="available")  # available, on_mission, maintenance
    company_id = Column(Integer, ForeignKey("rescue_companies.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("RescueCompany", back_populates="vehicles")
    
    def __repr__(self):
        return f"<RescueVehicle(id={self.id}, plate='{self.license_plate}', type='{self.vehicle_type}')>"
