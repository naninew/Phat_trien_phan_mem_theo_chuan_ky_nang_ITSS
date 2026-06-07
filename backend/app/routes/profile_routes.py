"""
User profile routes for managing user and company profiles.
Includes image upload functionality.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Any, Optional
import os
import uuid
from datetime import datetime

from app.database import get_db
from app.services import auth_svc, rescue_svc
from app.utils.response import success_response, error_response
from app.utils.jwt_helper import get_current_user_from_token
from pydantic import BaseModel
from app.schemas.rescue import CustomerVehicleCreate, CustomerVehicleUpdate, CustomerVehicleResponse
from app.schemas.auth import PasswordUpdate

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class CompanyProfileCreate(BaseModel):
    company_name: str
    business_license: str
    address: str
    hotline: str
    operating_area: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None

class CompanyProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    business_license: Optional[str] = None
    address: Optional[str] = None
    hotline: Optional[str] = None
    operating_area: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None

router = APIRouter(prefix="/profile", tags=["Profile Management"])

# Upload directory configuration
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads", "images")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def validate_file_extension(filename: str) -> bool:
    """Validate file extension is allowed."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def save_uploaded_file(file: UploadFile, user_id: int) -> str:
    """
    Save uploaded file and return the relative path.
    
    Args:
        file: Uploaded file object
        user_id: ID of the user uploading
        
    Returns:
        Relative path to saved file
    """
    # Create unique filename
    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    unique_filename = f"{user_id}_{uuid.uuid4().hex}{ext}"
    
    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Save file
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    
    # Return relative path for storage in database
    relative_path = f"/uploads/images/{unique_filename}"
    return relative_path


@router.get("/me", response_model=dict)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
) -> dict:
    """
    Get current user's profile information.
    """
    user_id = current_user["user_id"]
    user = auth_svc.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get company info if user is company staff
    company_info = None
    if user.role.value == "company_staff":
        company = rescue_svc.get_company_by_owner_id(db, user_id)
        if company:
            company_info = {
                "id": company.id,
                "company_name": company.company_name,
                "address": company.address,
                "hotline": company.hotline,
                "business_license": company.business_license,
                "is_verified": company.is_verified,
                "status": company.status,
                "service_radius_km": company.service_radius_km,
            }
    
    return success_response(
        data={
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "phone": user.phone,
            "email": user.email,
            "role": user.role.value,
            "status": user.status.value,
            "address": user.address,
            "avatar_url": getattr(user, 'avatar_url', None),
            "company": company_info,
            "created_at": user.created_at.isoformat(),
        },
        message="Success"
    )


@router.put("/me", response_model=dict)
def update_my_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
) -> dict:
    """
    Update current user's profile information.
    """
    user_id = current_user["user_id"]
    user = auth_svc.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if profile_data.full_name is not None:
        user.full_name = profile_data.full_name
    if profile_data.phone is not None:
        user.phone = profile_data.phone
    if profile_data.email is not None:
        # Check if email is already taken by another user
        existing = auth_svc.get_user_by_email(db, profile_data.email)
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        user.email = profile_data.email
    if profile_data.address is not None:
        user.address = profile_data.address
    
    db.commit()
    db.refresh(user)
    
    return success_response(
        data={
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "phone": user.phone,
            "email": user.email,
            "address": user.address,
        },
        message="Profile updated successfully"
    )


@router.post("/me/avatar", response_model=dict)
def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
) -> dict:
    """
    Upload user avatar image.
    
    - **file**: Image file (jpg, jpeg, png, gif, webp, max 5MB)
    """
    user_id = current_user["user_id"]
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Save file
    avatar_path = save_uploaded_file(file, user_id)
    
    # Update user record with avatar URL
    user = auth_svc.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.avatar_url = avatar_path
    db.commit()
    db.refresh(user)
    
    return success_response(
        data={"avatar_url": avatar_path},
        message="Avatar uploaded successfully"
    )


@router.get("/company", response_model=dict)
def get_company_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
) -> dict:
    """
    Get company profile (for company staff users only).
    """
    user_id = current_user["user_id"]
    user = auth_svc.get_user_by_id(db, user_id)
    
    if not user or user.role.value != "company_staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company staff can access company profile"
        )
    
    company = rescue_svc.get_company_by_owner_id(db, user_id)
    if not company or company.status in ["deleted", "inactive"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    return success_response(
        data={
            "id": company.id,
            "company_name": company.company_name,
            "business_license": company.business_license,
            "address": company.address,
            "hotline": company.hotline,
            "operating_area": company.operating_area,
            "latitude": company.latitude,
            "longitude": company.longitude,
            "rating_avg": company.rating_avg,
            "description": company.description,
            "is_verified": company.is_verified,
            "status": company.status,
        },
        message="Success"
    )

@router.post("/company", response_model=dict)
def create_company_profile(
    profile_data: CompanyProfileCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
) -> dict:
    """
    Create company profile.
    """
    user_id = current_user["user_id"]
    user = auth_svc.get_user_by_id(db, user_id)
    
    if not user or user.role.value != "company_staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company staff can create company profile"
        )
    
    existing = rescue_svc.get_company_by_owner_id(db, user_id)
    if existing and existing.status not in ["deleted", "inactive"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company profile already exists"
        )
    
    # If exists but deleted, we might want to restore or create a new one.
    # For now, we just create.
    company = rescue_svc.create_company_profile(db, user_id, profile_data)
    
    return success_response(
        data={
            "id": company.id,
            "company_name": company.company_name,
            "business_license": company.business_license,
            "address": company.address,
            "hotline": company.hotline,
            "operating_area": company.operating_area,
            "latitude": company.latitude,
            "longitude": company.longitude,
            "rating_avg": company.rating_avg,
            "description": company.description,
            "is_verified": company.is_verified,
            "status": company.status,
        },
        message="Company profile created successfully"
    )

@router.put("/company", response_model=dict)
def update_company_profile(
    profile_data: CompanyProfileUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
) -> dict:
    """
    Update company profile.
    """
    user_id = current_user["user_id"]
    user = auth_svc.get_user_by_id(db, user_id)
    
    if not user or user.role.value != "company_staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company staff can update company profile"
        )
    
    company = rescue_svc.get_company_by_owner_id(db, user_id)
    if not company or company.status in ["deleted", "inactive"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    # Update fields if provided
    if profile_data.company_name is not None:
        company.company_name = profile_data.company_name
    if profile_data.business_license is not None:
        company.business_license = profile_data.business_license
    if profile_data.address is not None:
        company.address = profile_data.address
    if profile_data.hotline is not None:
        company.hotline = profile_data.hotline
    if profile_data.operating_area is not None:
        company.operating_area = profile_data.operating_area
    if profile_data.latitude is not None:
        company.latitude = profile_data.latitude
    if profile_data.longitude is not None:
        company.longitude = profile_data.longitude
    if profile_data.description is not None:
        company.description = profile_data.description
    
    db.commit()
    db.refresh(company)
    
    return success_response(
        data={
            "id": company.id,
            "company_name": company.company_name,
            "business_license": company.business_license,
            "address": company.address,
            "hotline": company.hotline,
            "operating_area": company.operating_area,
            "latitude": company.latitude,
            "longitude": company.longitude,
            "rating_avg": company.rating_avg,
            "description": company.description,
            "is_verified": company.is_verified,
            "status": company.status,
        },
        message="Company profile updated successfully"
    )

@router.delete("/company", response_model=dict)
def delete_company_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
) -> dict:
    """
    Soft delete company profile.
    """
    user_id = current_user["user_id"]
    user = auth_svc.get_user_by_id(db, user_id)
    
    if not user or user.role.value != "company_staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company staff can delete company profile"
        )
    
    company = rescue_svc.get_company_by_owner_id(db, user_id)
    if not company or company.status in ["deleted", "inactive"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
        
    rescue_svc.soft_delete_company(db, company.id)
    
    return success_response(
        data={},
        message="Company profile deleted successfully"
    )

# ──────────────────────────────────────────────────────────────────────────────
# Customer Vehicles
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/vehicles", response_model=dict)
def list_my_vehicles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """Get list of customer's vehicles."""
    vehicles = rescue_svc.get_customer_vehicles(db, current_user["user_id"])
    return success_response(
        data=[
            {
                "id": v.id,
                "license_plate": v.license_plate,
                "brand": v.brand,
                "model": v.model,
                "year": v.year,
                "fuel_type": v.fuel_type,
            } for v in vehicles
        ],
        message="Success"
    )

@router.post("/vehicles", response_model=dict)
def create_my_vehicle(
    vehicle_data: CustomerVehicleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """Add a new vehicle for customer."""
    v = rescue_svc.create_customer_vehicle(db, current_user["user_id"], vehicle_data)
    return success_response(
        data={
            "id": v.id,
            "license_plate": v.license_plate,
            "brand": v.brand,
            "model": v.model,
        },
        message="Vehicle added successfully"
    )

@router.put("/vehicles/{vehicle_id}", response_model=dict)
def update_my_vehicle(
    vehicle_id: int,
    vehicle_data: CustomerVehicleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """Update customer vehicle."""
    v = rescue_svc.update_customer_vehicle(db, current_user["user_id"], vehicle_id, vehicle_data)
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found or not owned by you")
    return success_response(
        data={
            "id": v.id,
            "license_plate": v.license_plate,
        },
        message="Vehicle updated successfully"
    )

@router.delete("/vehicles/{vehicle_id}", response_model=dict)
def delete_my_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """Delete customer vehicle."""
    if rescue_svc.customer_vehicle_has_unfinished_requests(db, current_user["user_id"], vehicle_id):
        raise HTTPException(
            status_code=400,
            detail="Cannot delete vehicle with unfinished rescue requests",
        )
    ok = rescue_svc.delete_customer_vehicle(db, current_user["user_id"], vehicle_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Vehicle not found or not owned by you")
    return success_response(data={}, message="Vehicle deleted successfully")

@router.post("/chat/{request_id}/image", response_model=dict)
def upload_chat_image(
    request_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
) -> dict:
    """
    Upload image to chat for a specific rescue request.
    
    - **request_id**: ID of the rescue request
    - **file**: Image file to upload
    """
    user_id = current_user["user_id"]
    
    # Validate request exists and user has access
    request = rescue_svc.get_request_by_id(db, request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rescue request not found"
        )
    
    # Check authorization: only user who created request or assigned company can upload
    if request.user_id != user_id:
        if not request.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload images to this request"
            )
        company = rescue_svc.get_company_by_id(db, request.company_id)
        if not company or company.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload images to this request"
            )
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Save file
    image_path = save_uploaded_file(file, user_id)
    
    # In production, you might want to store this in a ChatMessage table
    # For now, return the path for frontend to use
    return success_response(
        data={
            "image_url": image_path,
            "request_id": request_id,
            "uploaded_at": datetime.utcnow().isoformat(),
        },
        message="Image uploaded successfully"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Password Management
# ──────────────────────────────────────────────────────────────────────────────
@router.put("/me/password", response_model=dict)
def update_password(
    password_data: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
) -> dict:
    """
    Update user password.
    
    Requires:
    - current_password: User's current password
    - new_password: New password (6-128 characters)
    - confirm_password: Confirmation of new password (must match new_password)
    """
    user_id = current_user["user_id"]
    
    # Call service to update password
    success, message = auth_svc.update_user_password(
        db, user_id, password_data.current_password, password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return success_response(
        data={"message": message},
        message="Password updated successfully"
    )
