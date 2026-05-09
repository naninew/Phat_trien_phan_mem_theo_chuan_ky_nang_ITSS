"""
Routes package initialization.
"""
from app.routes.auth_routes import router as auth_router
from app.routes.rescue_routes import router as rescue_router
from app.routes.profile_routes import router as profile_router
from app.routes.admin_routes import router as admin_router

__all__ = ["auth_router", "rescue_router", "profile_router", "admin_router"]
