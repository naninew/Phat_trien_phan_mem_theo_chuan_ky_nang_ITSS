"""
Authentication and session management for NiceGUI frontend.
"""
from nicegui import app, ui
from typing import Optional, Dict, Any

from .config import (
    SESSION_TOKEN_KEY,
    SESSION_USER_KEY,
    SESSION_ROLE_KEY,
    LOGIN_PAGE,
    CUSTOMER_DASHBOARD,
    COMPANY_DASHBOARD,
    ADMIN_DASHBOARD,
)


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current user from session storage."""
    return app.storage.user.get(SESSION_USER_KEY)


def get_access_token() -> Optional[str]:
    """Get access token from session storage."""
    return app.storage.user.get(SESSION_TOKEN_KEY)


def get_user_role() -> Optional[str]:
    """Get user role from session storage."""
    return app.storage.user.get(SESSION_ROLE_KEY)


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return get_access_token() is not None


def login_user(token: str, user_info: Dict[str, Any], role: str) -> None:
    """
    Store user authentication data in session.
    
    Args:
        token: Access token
        user_info: User information dictionary
        role: User role
    """
    app.storage.user[SESSION_TOKEN_KEY] = token
    app.storage.user[SESSION_USER_KEY] = user_info
    app.storage.user[SESSION_ROLE_KEY] = role


def logout_user() -> None:
    """Clear user session and redirect to login."""
    app.storage.user.clear()
    ui.navigate.to(LOGIN_PAGE)


def require_auth():
    """Decorator-like function to require authentication on a page."""
    if not is_authenticated():
        ui.navigate.to(LOGIN_PAGE)
        return False
    return True


def require_role(required_role: str):
    """
    Check if user has the required role.
    
    Args:
        required_role: Role required to access the page
    
    Returns:
        True if user has the role, False otherwise
    """
    if not is_authenticated():
        ui.navigate.to(LOGIN_PAGE)
        return False
    
    user_role = get_user_role()
    if user_role != required_role and user_role != "admin":
        ui.notify("You don't have permission to access this page", color="negative")
        ui.navigate.to(CUSTOMER_DASHBOARD)
        return False
    
    return True


def get_redirect_url_for_role(role: str) -> str:
    """
    Get the default dashboard URL for a given role.
    
    Args:
        role: User role
    
    Returns:
        Redirect URL string
    """
    if role == "customer":
        return CUSTOMER_DASHBOARD
    elif role == "company_staff":
        return COMPANY_DASHBOARD
    elif role == "admin":
        return ADMIN_DASHBOARD
    return CUSTOMER_DASHBOARD
