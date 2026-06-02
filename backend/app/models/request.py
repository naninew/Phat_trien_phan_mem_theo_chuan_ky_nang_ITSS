"""
RescueRequest model for managing rescue service requests, services, and assignments.
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class RequestStatus(str, enum.Enum):
    """Rescue request status enumeration."""
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    ASSIGNED = "ASSIGNED"
    ON_THE_WAY = "ON_THE_WAY"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class RescueRequest(Base):
    """Rescue request table for storing customer rescue requests."""
    
    __tablename__ = "rescue_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("rescue_companies.id"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False) # Refers to customer's vehicle

    # Location information
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address_description = Column(Text, nullable=False)
    
    # Issue details
    incident_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    images = Column(JSON)  # List of image URLs
    
    # Status and tracking
    status = Column(String(20), default="PENDING")
    eta_minutes = Column(Integer)  # Estimated time of arrival in minutes
    actual_arrival_time = Column(DateTime)
    actual_completion_time = Column(DateTime)
    
    # Payment
    agreed_price = Column(Float)
    invoice_description = Column(Text, nullable=True)
    payment_status = Column(String(20), default="unpaid")  # unpaid, paid, refunded
    payment_method = Column(String(50))  # cash, momo, vnpay, card
    
    # Feedback
    feedback = Column(Text)
    rating = Column(Integer)  # 1-5 stars
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="rescue_requests", foreign_keys=[user_id])
    company = relationship("RescueCompany", back_populates="rescue_requests")
    vehicle = relationship("Vehicle")
    payment = relationship("Payment", back_populates="rescue_request", uselist=False)
    review = relationship("Review", back_populates="rescue_request", uselist=False)

    request_services = relationship("RequestService", back_populates="request", cascade="all, delete-orphan")
    assignment = relationship("ServiceAssignment", back_populates="request", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<RescueRequest(id={self.id}, user_id={self.user_id}, status='{self.status}')>"


class RequestService(Base):
    """Association table for many-to-many relationship between RescueRequest and Service."""
    __tablename__ = "request_services"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("rescue_requests.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    
    request = relationship("RescueRequest", back_populates="request_services")
    service = relationship("Service")


class ServiceAssignment(Base):
    """Assignment table linking a request to specific staff and vehicle."""
    __tablename__ = "service_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("rescue_requests.id"), nullable=False, unique=True)
    staff_id = Column(Integer, ForeignKey("rescue_staff.id"), nullable=False)
    rescue_vehicle_id = Column(Integer, ForeignKey("rescue_vehicles.id"), nullable=False)
    assigned_time = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    
    request = relationship("RescueRequest", back_populates="assignment")
    staff = relationship("RescueStaff")
    rescue_vehicle = relationship("RescueVehicle")
