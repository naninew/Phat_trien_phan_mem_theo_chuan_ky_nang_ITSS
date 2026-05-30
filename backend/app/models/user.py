"""
User model for authentication and user management.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User roles enumeration."""
    CUSTOMER = "customer"
    COMPANY_STAFF = "company_staff"
    ADMIN = "admin"


class AccountStatus(str, enum.Enum):
    """Account status enumeration."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class User(Base):
    """User table for storing all system users."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    status = Column(SQLEnum(AccountStatus), nullable=False, default=AccountStatus.ACTIVE)
    address = Column(String(200), nullable=True)
    avatar_url = Column(String(500), nullable=True)  # Profile picture URL
    suspend_reason = Column(String(500), nullable=True) # Reason if suspended
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rescue_requests = relationship("RescueRequest", back_populates="user", foreign_keys="RescueRequest.user_id")
    company = relationship("RescueCompany", back_populates="owner", uselist=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
