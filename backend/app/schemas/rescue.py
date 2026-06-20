"""
Rescue service schemas for requests, services, and related operations.
"""
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime


class RescueCompanyCreate(BaseModel):
    """Schema for creating a rescue company."""
    company_name: str = Field(..., min_length=1, max_length=200)
    address: str = Field(..., min_length=1)
    hotline: str = Field(..., min_length=1, max_length=20)
    business_license: str = Field(..., min_length=1, max_length=50)
    operating_area: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    service_radius_km: Optional[float] = 20.0


class RescueServiceCreate(BaseModel):
    """Schema for creating a new service."""
    service_name: str = Field(..., min_length=1, max_length=100)
    base_price: float = Field(..., ge=0)
    estimated_duration: Optional[int] = Field(0, ge=0)  # minutes
    description: Optional[str] = None
    is_active: Optional[bool] = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "service_name": "Vá lốp",
                "base_price": 150000.0,
                "estimated_duration": 30,
                "description": "Dịch vụ vá lốp xe máy và ô tô",
                "is_active": True
            }
        }

class RescueServiceUpdate(BaseModel):
    """Schema for updating a service."""
    service_name: Optional[str] = Field(None, min_length=1, max_length=100)
    base_price: Optional[float] = Field(None, ge=0)
    estimated_duration: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class RescueServiceResponse(BaseModel):
    """Schema for service response."""
    service_id: int = Field(alias="id")
    service_name: str
    base_price: float
    estimated_duration: int
    description: Optional[str]
    company_id: int
    is_active: bool
    
    class Config:
        from_attributes = True
        populate_by_name = True


class RescueRequestCreate(BaseModel):
    """Schema for creating a rescue request."""
    service_ids: List[int]
    vehicle_id: int
    company_id: Optional[int] = None   # Có thể chọn trước hoặc để hệ thống phân công
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address_description: str = Field(..., min_length=1, max_length=500)
    incident_type: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=1000)
    images: Optional[List[str]] = None
    payment_method: Optional[str] = "cash"
    
    class Config:
        json_schema_extra = {
            "example": {
                "service_ids": [1, 2],
                "vehicle_id": 1,
                "latitude": 10.762622,
                "longitude": 106.682396,
                "address_description": "Ngã tư Nguyễn Văn Linh - Nguyễn Hữu Thọ",
                "incident_type": "Tai nạn",
                "description": "Xe bị xì lốp sau, cần vá gấp",
                "images": ["image1.jpg", "image2.jpg"],
                "payment_method": "cash"
            }
        }


class RescueRequestUpdate(BaseModel):
    """Schema for updating a rescue request."""
    status: Optional[str] = None
    eta_minutes: Optional[int] = Field(None, ge=0)
    agreed_price: Optional[float] = Field(None, gt=0)
    invoice_description: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["PENDING", "ACCEPTED", "ASSIGNED", "ON_THE_WAY", "IN_PROGRESS", "COMPLETED", "REJECTED", "CANCELLED"]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {valid_statuses}")
        return v


class RescueRequestResponse(BaseModel):
    """Schema for rescue request response."""
    id: int
    user_id: int
    company_id: Optional[int]
    vehicle_id: int
    latitude: float
    longitude: float
    address_description: str
    incident_type: str
    description: str
    images: Optional[List[str]]
    status: str
    eta_minutes: Optional[int]
    actual_arrival_time: Optional[datetime]
    actual_completion_time: Optional[datetime]
    estimated_price: Optional[float]
    agreed_price: Optional[float]
    invoice_description: Optional[str]
    payment_status: str
    payment_method: Optional[str]
    feedback: Optional[str]
    rating: Optional[int]
    created_at: datetime
    updated_at: datetime

class ServiceAssignmentCreate(BaseModel):
    staff_id: int
    rescue_vehicle_id: int
    notes: Optional[str] = None

class ServiceAssignmentResponse(BaseModel):
    id: int
    request_id: int
    staff_id: int
    rescue_vehicle_id: int
    assigned_time: datetime
    notes: Optional[str]
    
    class Config:
        from_attributes = True

class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0)
    payment_method: str = Field(..., pattern="^(cash|qr|card|momo|vnpay)$")
    transaction_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class CompanyNearbyResponse(BaseModel):
    """Schema for nearby company response."""
    id: int
    company_name: str
    address: str
    hotline: str
    rating_avg: float
    distance_km: float
    estimated_price: float
    eta_minutes: int
    services: List[RescueServiceResponse]
    
    class Config:
        from_attributes = True


class CustomerVehicleCreate(BaseModel):
    """Schema for creating a customer vehicle."""
    license_plate: str = Field(..., min_length=1, max_length=20)
    brand: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=50)
    year: int = Field(..., gt=1900, le=2100)
    fuel_type: str = Field(..., min_length=1, max_length=20)
    
class CustomerVehicleUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    fuel_type: Optional[str] = None

class CustomerVehicleResponse(BaseModel):
    id: int
    customer_id: int
    license_plate: str
    brand: str
    model: str
    year: int
    fuel_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class RescueVehicleCreate(BaseModel):
    """Schema for creating a rescue vehicle."""
    plate_number: str = Field(..., min_length=1, max_length=20)
    vehicle_type: str = Field(..., min_length=1, max_length=50)
    capacity: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "plate_number": "51C-12345",
                "vehicle_type": "Xe cẩu",
                "capacity": "5 tấn"
            }
        }

class RescueVehicleUpdate(BaseModel):
    """Schema for updating a rescue vehicle."""
    plate_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    capacity: Optional[str] = None
    status: Optional[str] = None


class RescueVehicleResponse(BaseModel):
    """Schema for vehicle response."""
    id: int
    plate_number: str
    vehicle_type: str
    capacity: Optional[str]
    status: str
    company_id: int
    is_active: bool
    
    
    class Config:
        from_attributes = True

class RescueStaffCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    birth_date: date
    phone: str = Field(..., min_length=10, max_length=15)
    skill_level: str = Field(..., min_length=1, max_length=50)

    @validator('full_name')
    def normalize_full_name(cls, v):
        return " ".join(v.split())

    @validator('phone')
    def validate_phone(cls, v):
        normalized = v.replace(" ", "").replace("-", "")
        if not normalized.isdigit() or not normalized.startswith("0") or len(normalized) != 10:
            raise ValueError("Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0")
        return normalized

    @validator('birth_date')
    def validate_birth_date(cls, v):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if v.year < 1940 or age < 18:
            raise ValueError("Ngày sinh không hợp lệ hoặc nhân viên chưa đủ 18 tuổi")
        return v

class RescueStaffUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    birth_date: Optional[date] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    skill_level: Optional[str] = None
    status: Optional[str] = None

    @validator('full_name')
    def normalize_updated_full_name(cls, v):
        return " ".join(v.split()) if v is not None else v

    @validator('phone')
    def validate_updated_phone(cls, v):
        if v is None:
            return v
        normalized = v.replace(" ", "").replace("-", "")
        if not normalized.isdigit() or not normalized.startswith("0") or len(normalized) != 10:
            raise ValueError("Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0")
        return normalized

    @validator('birth_date')
    def validate_updated_birth_date(cls, v):
        if v is None:
            return v
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if v.year < 1940 or age < 18:
            raise ValueError("Ngày sinh không hợp lệ hoặc nhân viên chưa đủ 18 tuổi")
        return v

class RescueStaffResponse(BaseModel):
    id: int
    company_id: int
    full_name: Optional[str]
    birth_year: Optional[int]
    birth_date: Optional[date]
    phone: Optional[str]
    skill_level: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
