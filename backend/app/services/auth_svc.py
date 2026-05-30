"""
Authentication service for user management, login, and registration.
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from passlib.context import CryptContext
from typing import Optional, Tuple

from app.models.user import User, UserRole, AccountStatus
from app.schemas.auth import UserRegister
from app.utils.jwt_helper import create_access_token, create_refresh_token, get_current_user_from_token


# Password hashing context - Use pbkdf2_sha256 for better compatibility on Python 3.14
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
    
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get a user by username.
    
    Args:
        db: Database session
        username: Username to search for
    
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by email.
    
    Args:
        db: Database session
        email: Email to search for
    
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Get a user by ID.
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user with username and password.
    
    Args:
        db: Database session
        username: Username
        password: Plain text password
    
    Returns:
        User object if authenticated successfully, None otherwise
    """
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if user.status != AccountStatus.ACTIVE:
        return None
    return user


def create_user(db: Session, user_data: UserRegister, role: UserRole = UserRole.CUSTOMER) -> User:
    """
    Create a new user in the database.
    
    Args:
        db: Database session
        user_data: User registration data
        role: User role (default: CUSTOMER)
    
    Returns:
        Created User object
    """
    hashed_password = hash_password(user_data.password)
    
    db_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        phone=user_data.phone,
        email=user_data.email,
        role=role,
        status=AccountStatus.ACTIVE
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def generate_tokens(user: User) -> Tuple[str, str]:
    """
    Generate access and refresh tokens for a user.
    
    Args:
        user: User object
    
    Returns:
        Tuple of (access_token, refresh_token)
    """
    token_data = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role.value
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return access_token, refresh_token


def update_user_status(db: Session, user_id: int, status: AccountStatus) -> Optional[User]:
    """
    Update user active status.
    
    Args:
        db: Database session
        user_id: User ID
        status: New account status
    
    Returns:
        Updated User object if found, None otherwise
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    user.status = status
    db.commit()
    db.refresh(user)
    

def update_user_password(db: Session, user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
    """
    Update user password after verifying current password.
    
    Args:
        db: Database session
        user_id: User ID
        current_password: Current password (plain text)
        new_password: New password (plain text)
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return False, "User not found"
    
    # Verify current password
    if not verify_password(current_password, user.password_hash):
        return False, "Current password is incorrect"
    
    # Hash and update new password
    user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(user)
    
    return True, "Password updated successfully"
