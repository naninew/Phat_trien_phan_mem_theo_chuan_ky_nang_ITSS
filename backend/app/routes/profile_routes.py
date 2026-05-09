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

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class CompanyProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    address: Optional[str] = None
    hotline: Optional[str] = None
    service_radius_km: Optional[float] = None

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
                "license_number": company.license_number,
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
    
    db.commit()
    db.refresh(user)
    
    return success_response(
        data={
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "phone": user.phone,
            "email": user.email,
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


@router.put("/company", response_model=dict)
def update_company_profile(
    profile_data: CompanyProfileUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
) -> dict:
    """
    Update company profile (for company staff users only).
    """
    user_id = current_user["user_id"]
    user = auth_svc.get_user_by_id(db, user_id)
    
    if not user or user.role.value != "company_staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company staff can update company profile"
        )
    
    company = rescue_svc.get_company_by_owner_id(db, user_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    # Update fields if provided
    if profile_data.company_name is not None:
        company.company_name = profile_data.company_name
    if profile_data.address is not None:
        company.address = profile_data.address
    if profile_data.hotline is not None:
        company.hotline = profile_data.hotline
    if profile_data.service_radius_km is not None:
        company.service_radius_km = profile_data.service_radius_km
    
    db.commit()
    db.refresh(company)
    
    return success_response(
        data={
            "id": company.id,
            "company_name": company.company_name,
            "address": company.address,
            "hotline": company.hotline,
            "service_radius_km": company.service_radius_km,
        },
        message="Company profile updated successfully"
    )


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
