"""
Authentication routes for login, registration, and token management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.database import get_db
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from app.services import auth_svc
from app.utils.response import success_response, error_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=dict)
def register(user_data: UserRegister, db: Session = Depends(get_db)) -> dict:
    """
    Register a new user account.
    
    - **username**: Unique username (3-50 characters)
    - **password**: Password (6-128 characters)
    - **full_name**: Full name of the user
    - **phone**: Phone number
    - **email**: Valid email address
    - **role**: Optional user role (default: customer)
    - For company_staff role: company_name, business_license, address, hotline are also accepted.
    """
    # Check if username already exists
    existing_user = auth_svc.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = auth_svc.get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    from app.models.user import UserRole
    role_val = user_data.role if user_data.role else "customer"
    user = auth_svc.create_user(db, user_data, role=UserRole(role_val))
    
    response_data: dict = {"user_id": user.id, "username": user.username}

    # If registering as a company staff, auto-create a pending company profile
    if role_val == "company_staff":
        if not user_data.company_name or not user_data.business_license:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="company_name and business_license are required for company registration"
            )
        from app.services import rescue_svc
        company = rescue_svc.create_company_profile(
            db=db,
            owner_id=user.id,
            data=user_data,
            initial_status="pending",
        )
        response_data["company_id"] = company.id
        response_data["company_status"] = "pending"
        return success_response(
            data=response_data,
            message="Đăng ký công ty thành công! Vui lòng chờ quản trị viên phê duyệt."
        )

    return success_response(
        data=response_data,
        message="Registration successful"
    )


@router.post("/login", response_model=dict)
def login(credentials: UserLogin, db: Session = Depends(get_db)) -> dict:
    """
    Login and receive access tokens.
    
    - **username**: Username
    - **password**: Password

    Error codes in response detail:
    - 401 + "Tên đăng nhập hoặc mật khẩu không đúng"  → sai credentials
    - 403 + "Tài khoản đã bị khóa"                    → SUSPENDED
    - 403 + "Tài khoản chưa được kích hoạt"            → INACTIVE
    """
    from app.services.auth_svc import (
        AUTH_ERROR_WRONG_CREDENTIALS,
        AUTH_ERROR_SUSPENDED,
        AUTH_ERROR_INACTIVE,
        AUTH_ERROR_COMPANY_PENDING,
    )

    # authenticate_user trả về tuple (user | None, error_code | None)
    user, error_code = auth_svc.authenticate_user(db, credentials.username, credentials.password)

    if error_code == AUTH_ERROR_WRONG_CREDENTIALS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng",
        )
    if error_code == AUTH_ERROR_SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên để được hỗ trợ.",
        )
    if error_code == AUTH_ERROR_INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản chưa được kích hoạt. Vui lòng kiểm tra email để xác minh.",
        )
    if error_code == AUTH_ERROR_COMPANY_PENDING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản công ty của bạn đang chờ quản trị viên phê duyệt. Vui lòng thử lại sau khi được phê duyệt.",
        )

    # Generate tokens
    access_token, refresh_token = auth_svc.generate_tokens(user)

    return success_response(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value,
                "avatar_url": user.avatar_url,
            }
        },
        message="Login successful"
    )


@router.get("/me", response_model=dict)
def get_current_user(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
) -> dict:
    """
    Get current authenticated user information.
    
    Requires valid JWT token in Authorization header.
    """
    user = auth_svc.get_user_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return success_response(
        data={
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role.value,
            "status": user.status.value,
            "address": user.address
        },
        message="Success"
    )
