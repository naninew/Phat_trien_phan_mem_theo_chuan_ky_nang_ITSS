"""
RescueCompany model – thêm latitude/longitude để tính khoảng cách thực tế.
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class RescueCompany(Base):
    """Rescue company table."""

    __tablename__ = "rescue_companies"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(200), nullable=False)
    address = Column(Text, nullable=False)
    hotline = Column(String(20), nullable=False)
    business_license = Column(String(50), unique=True, nullable=False)
    operating_area = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)

    # ── Vị trí công ty (cần để tính khoảng cách Haversine) ──────────────────
    latitude = Column(Float, nullable=True)   # vĩ độ
    longitude = Column(Float, nullable=True)  # kinh độ

    rating_avg = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    status = Column(String(20), default="active")  # active | suspended | pending
    service_radius_km = Column(Float, default=20.0)
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
        return f"<RescueCompany(id={self.id}, name='{self.company_name}')>"
