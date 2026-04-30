"""
Routes package initialization.
"""
from .auth_routes import router as auth_router
from .rescue_routes import router as rescue_router
from .profile_routes import router as profile_router

__all__ = ["auth_router", "rescue_router", "profile_router"]
