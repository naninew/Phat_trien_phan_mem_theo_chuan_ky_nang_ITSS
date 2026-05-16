"""
Authentication schemas for login and registration.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re


class UserRegister(BaseModel):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    email: EmailStr
    role: Optional[str] = "customer"
    
    @validator('phone')
    def validate_phone(cls, v):
        if not re.match(r'^\+?[\d\s-]{10,20}$', v):
            raise ValueError('Invalid phone number format')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "nguyenvana",
                "password": "securepass123",
                "full_name": "Nguyen Van A",
                "phone": "0912345678",
                "email": "nguyenvana@example.com"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "nguyenvana",
                "password": "securepass123"
            }
        }


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 3600


class UserResponse(BaseModel):
    """Schema for user information response."""
    id: int
    username: str
    full_name: str
    phone: str
    email: str
    role: str
    status: str
    address: Optional[str] = None
    
    class Config:
        from_attributes = True
