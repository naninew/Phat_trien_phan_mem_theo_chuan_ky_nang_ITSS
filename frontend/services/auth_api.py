"""
Authentication API service for login and registration.
"""
from typing import Dict, Any, Optional
from .api_client import api_client


async def login(username: str, password: str) -> Dict[str, Any]:
    """
    Login user and return authentication data.
    
    Args:
        username: Username
        password: Password
    
    Returns:
        Dictionary with access_token, user info, etc.
    """
    response = await api_client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )
    return response.get("data", {})


async def register(
    username: str,
    password: str,
    full_name: str,
    phone: str,
    email: str,
) -> Dict[str, Any]:
    """
    Register a new user.
    
    Args:
        username: Username
        password: Password
        full_name: Full name
        phone: Phone number
        email: Email address
    
    Returns:
        Dictionary with registration result
    """
    response = await api_client.post(
        "/auth/register",
        data={
            "username": username,
            "password": password,
            "full_name": full_name,
            "phone": phone,
            "email": email,
        },
    )
    return response.get("data", {})


async def get_current_user(token: str) -> Optional[Dict[str, Any]]:
    """
    Get current authenticated user information.
    
    Args:
        token: Access token
    
    Returns:
        User information dictionary or None
    """
    try:
        response = await api_client.get("/auth/me", token=token)
        return response.get("data")
    except Exception:
        return None
