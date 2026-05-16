"""
Database configuration and session management.
Supports SQLite (default for dev) and PostgreSQL (for production).
Switch by setting DATABASE_URL environment variable.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator

# ─── Database URL ───────────────────────────────────────────────────────────
# Default: SQLite stored alongside this file (no setup required)
# For PostgreSQL: set DATABASE_URL=postgresql://user:pass@host:5432/dbname
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SQLITE_PATH = os.path.join(_BASE_DIR, "rescue_system.db")

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{_SQLITE_PATH}"
)

# ─── Engine args (SQLite needs check_same_thread=False) ─────────────────────
_connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
)

# ─── Session factory ─────────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ─── Declarative base ────────────────────────────────────────────────────────
Base = declarative_base()


# ─── Dependency ──────────────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency: yields a database session and closes it after use.
    Works with both SQLite and PostgreSQL without any code changes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Create all tables. Safe to call multiple times (idempotent).
    Run once on startup; existing tables are NOT dropped.
    """
    # Import all models so metadata is populated before create_all
    from app.models import user, company, service, vehicle, staff, request, review, payment, community, communication, report  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print(f"[DB] Connected to: {DATABASE_URL[:50]}...")
    print("[DB] Tables created/verified.")


if __name__ == "__main__":
    init_db()
