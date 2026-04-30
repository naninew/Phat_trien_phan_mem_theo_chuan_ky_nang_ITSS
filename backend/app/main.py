"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .routes import auth_routes, rescue_routes, profile_routes
from .database import init_db

# Create FastAPI application
app = FastAPI(
    title="Roadside Assistance System API",
    description="API for managing roadside assistance requests and services",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(rescue_routes.router, prefix="/api/v1")
app.include_router(profile_routes.router, prefix="/api/v1")

# Serve uploaded files statically
from fastapi.staticfiles import StaticFiles

# Mount uploads directory for serving images
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
os.makedirs(os.path.join(uploads_dir, "images"), exist_ok=True)
if os.path.exists(uploads_dir):
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    print("Database initialized successfully!")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Roadside Assistance System API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
