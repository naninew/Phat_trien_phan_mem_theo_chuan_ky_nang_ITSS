"""
RescueRequest model for managing rescue service requests.
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..database import Base


class RequestStatus(str, enum.Enum):
    """Rescue request status enumeration."""
    PENDING = "pending"  # Chờ tiếp nhận
    ACCEPTED = "accepted"  # Đã tiếp nhận
    EN_ROUTE = "en_route"  # Đang di chuyển
    ON_SITE = "on_site"  # Đang xử lý
    COMPLETED = "completed"  # Hoàn thành
    CANCELLED = "cancelled"  # Đã hủy


class RescueRequest(Base):
    """Rescue request table for storing customer rescue requests."""
    
    __tablename__ = "rescue_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("rescue_companies.id"), nullable=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("rescue_vehicles.id"), nullable=True)
    
    # Location information
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address_description = Column(Text, nullable=False)
    
    # Issue details
    car_issue_detail = Column(Text, nullable=False)
    images = Column(JSON)  # List of image URLs
    
    # Status and tracking
    status = Column(String(20), default="pending")
    eta_minutes = Column(Integer)  # Estimated time of arrival in minutes
    actual_arrival_time = Column(DateTime)
    actual_completion_time = Column(DateTime)
    
    # Payment
    total_cost = Column(Float)
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
    service = relationship("Service", back_populates="rescue_requests")
    vehicle = relationship("RescueVehicle")
    payment = relationship("Payment", back_populates="rescue_request", uselist=False)
    review = relationship("Review", back_populates="rescue_request", uselist=False)
    
    def __repr__(self):
        return f"<RescueRequest(id={self.id}, user_id={self.user_id}, status='{self.status}')>"
