"""
Main FastAPI application entry point.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sys
from pathlib import Path

# Đảm bảo thư mục backend nằm trong sys.path để import absolute 'app.x' hoạt động
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.routes import auth_routes, rescue_routes, profile_routes, admin_routes, chat_routes, community_routes
from app.database import init_db

app = FastAPI(
    title="Hệ Thống Hỗ Trợ Sự Cố Xe Trên Đường – API",
    description="API kết nối người dùng bị sự cố với các công ty cứu hộ chuyên nghiệp.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS – cho phép NiceGUI frontend gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Production: thay bằng domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_routes.router,      prefix="/api/v1")
app.include_router(rescue_routes.router,    prefix="/api/v1")
app.include_router(profile_routes.router,   prefix="/api/v1")
app.include_router(admin_routes.router,     prefix="/api/v1")
app.include_router(chat_routes.router,      prefix="/api/v1")
app.include_router(community_routes.router, prefix="/api/v1")

# Static files (uploaded images)
_uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(os.path.join(_uploads_dir, "images"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
async def root():
    return {"message": "Roadside Assistance API v2.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
