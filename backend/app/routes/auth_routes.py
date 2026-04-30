"""
Authentication routes for login, registration, and token management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from ..database import get_db
from ..schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from ..services import auth_svc
from ..utils.response import success_response, error_response

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
    user = auth_svc.create_user(db, user_data)
    
    return success_response(
        data={"user_id": user.id, "username": user.username},
        message="Registration successful"
    )


@router.post("/login", response_model=dict)
def login(credentials: UserLogin, db: Session = Depends(get_db)) -> dict:
    """
    Login and receive access tokens.
    
    - **username**: Username
    - **password**: Password
    """
    # Authenticate user
    user = auth_svc.authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
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
                "role": user.role.value
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
    return success_response(
        data=current_user,
        message="Success"
    )
