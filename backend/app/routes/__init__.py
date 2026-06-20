"""
Routes package initialization.
"""
from app.routes.auth_routes import router as auth_router
from app.routes.rescue_routes import router as rescue_router
from app.routes.profile_routes import router as profile_router
from app.routes.admin_routes import router as admin_router
from app.routes.chat_routes import router as chat_router
from app.routes.community_routes import router as community_router
from app.routes.ws_routes import router as ws_router

__all__ = ["auth_router", "rescue_router", "profile_router", "admin_router", "chat_router", "community_router", "ws_router"]
