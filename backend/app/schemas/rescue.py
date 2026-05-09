"""
Rescue service schemas for requests, services, and related operations.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class ServiceCreate(BaseModel):
    """Schema for creating a new service."""
    service_name: str = Field(..., min_length=1, max_length=100)
    base_price: float = Field(..., gt=0)
    description: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "service_name": "Vá lốp",
                "base_price": 150000.0,
                "description": "Dịch vụ vá lốp xe máy và ô tô"
            }
        }


class ServiceResponse(BaseModel):
    """Schema for service response."""
    id: int
    service_name: str
    base_price: float
    description: Optional[str]
    company_id: int
    is_active: bool
    
    class Config:
        from_attributes = True


class RescueRequestCreate(BaseModel):
    """Schema for creating a rescue request."""
    service_id: int
    company_id: Optional[int] = None   # Có thể chọn trước hoặc để hệ thống phân công
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address_description: str = Field(..., min_length=1, max_length=500)
    car_issue_detail: str = Field(..., min_length=1, max_length=1000)
    images: Optional[List[str]] = None
    payment_method: Optional[str] = "cash"

    
    class Config:
        json_schema_extra = {
            "example": {
                "service_id": 1,
                "latitude": 10.762622,
                "longitude": 106.682396,
                "address_description": "Ngã tư Nguyễn Văn Linh - Nguyễn Hữu Thọ",
                "car_issue_detail": "Xe bị xì lốp sau, cần vá gấp",
                "images": ["image1.jpg", "image2.jpg"],
                "payment_method": "cash"
            }
        }


class RescueRequestUpdate(BaseModel):
    """Schema for updating a rescue request."""
    status: Optional[str] = None
    eta_minutes: Optional[int] = Field(None, ge=0)
    vehicle_id: Optional[int] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["pending", "accepted", "en_route", "on_site", "completed", "cancelled"]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {valid_statuses}")
        return v


class RescueRequestResponse(BaseModel):
    """Schema for rescue request response."""
    id: int
    user_id: int
    company_id: Optional[int]
    service_id: int
    vehicle_id: Optional[int]
    latitude: float
    longitude: float
    address_description: str
    car_issue_detail: str
    images: Optional[List[str]]
    status: str
    eta_minutes: Optional[int]
    total_cost: Optional[float]
    payment_status: str
    payment_method: Optional[str]
    feedback: Optional[str]
    rating: Optional[int]
    created_at: datetime
    updated_at: datetime
    
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
    services: List[ServiceResponse]
    
    class Config:
        from_attributes = True


class VehicleCreate(BaseModel):
    """Schema for creating a rescue vehicle."""
    license_plate: str = Field(..., min_length=1, max_length=20)
    vehicle_type: str = Field(..., min_length=1, max_length=50)
    capacity: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "license_plate": "51C-12345",
                "vehicle_type": "Xe cẩu",
                "capacity": "5 tấn"
            }
        }


class VehicleResponse(BaseModel):
    """Schema for vehicle response."""
    id: int
    license_plate: str
    vehicle_type: str
    capacity: Optional[str]
    status: str
    company_id: int
    is_active: bool
    
    class Config:
        from_attributes = True
