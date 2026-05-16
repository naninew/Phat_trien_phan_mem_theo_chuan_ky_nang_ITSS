from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class StaffStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"


class RescueStaff(Base):
    __tablename__ = "rescue_staff"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("rescue_companies.id"), nullable=False)
    skill_level = Column(String(50), nullable=False)  # Sơ cấp/Trung cấp/Cao cấp
    status = Column(SQLEnum(StaffStatus), nullable=False, default=StaffStatus.AVAILABLE)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("RescueCompany", backref="staff")
    
    def __repr__(self):
        return f"<RescueStaff(id={self.id}, company_id={self.company_id})>"
