"""
Test Fixtures and Configuration
Provides shared fixtures, database setup, and test utilities.
"""

import os
import sys
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add backend directory to path
from pathlib import Path
backend_dir = str(Path(__file__).resolve().parent.parent.parent / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import Base, get_db
from app.models.user import User, UserRole
from app.models.company import RescueCompany
from app.models.vehicle import RescueVehicle
from app.models.service import Service
from app.models.request import RescueRequest
from app.services import auth_svc

# Test Database URL (SQLite in-memory for fast unit tests)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def override_get_db(db_session: Session):
    """Override the get_db dependency for FastAPI tests."""
    def _get_db():
        try:
            yield db_session
        finally:
            pass
    return _get_db


@pytest.fixture
def test_admin(db_session: Session) -> User:
    """Create a test admin user."""
    import uuid
    suffix = str(uuid.uuid4())[:8]
    user = User(
        username=f"admin_{suffix}",
        password_hash=auth_svc.hash_password("Pass123!"),
        full_name="Test Admin",
        phone="0900000001",
        email=f"admin_{suffix}@test.com",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    db_session.flush()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_customer(db_session: Session) -> User:
    """Create a test customer user."""
    import uuid
    suffix = str(uuid.uuid4())[:8]
    user = User(
        username=f"customer_{suffix}",
        password_hash=auth_svc.hash_password("Pass123!"),
        full_name="Test Customer",
        phone="0900000002",
        email=f"customer_{suffix}@test.com",
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db_session.add(user)
    db_session.flush()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_company_staff(db_session: Session) -> User:
    """Create a test company staff user."""
    import uuid
    suffix = str(uuid.uuid4())[:8]
    user = User(
        username=f"staff_{suffix}",
        password_hash=auth_svc.hash_password("Pass123!"),
        full_name="Test Staff",
        phone="0900000003",
        email=f"staff_{suffix}@test.com",
        role=UserRole.COMPANY_STAFF,
        is_active=True
    )
    db_session.add(user)
    db_session.flush()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_company(db_session: Session, test_company_staff: User) -> RescueCompany:
    """Create a test rescue company."""
    import uuid
    suffix = str(uuid.uuid4())[:8]
    company = RescueCompany(
        company_name=f"Test Rescue Co {suffix}",
        address="123 Test St, Hanoi",
        hotline="1900-1111",
        license_number=f"TEST-{suffix}",
        latitude=21.0285,
        longitude=105.8542,
        owner_id=test_company_staff.id,
        status="active",
        is_verified=True
    )
    db_session.add(company)
    db_session.flush()
    db_session.refresh(company)
    return company


@pytest.fixture
def test_service(db_session: Session, test_company: RescueCompany) -> Service:
    """Create a test service for a company."""
    svc = Service(
        service_name="Vá lốp test",
        base_price=100000.0,
        description="Test service",
        company_id=test_company.id,
        is_active=True
    )
    db_session.add(svc)
    db_session.flush()
    db_session.refresh(svc)
    return svc


@pytest.fixture
def test_vehicle(db_session: Session, test_company: RescueCompany) -> RescueVehicle:
    """Create a test vehicle for a company."""
    import uuid
    suffix = str(uuid.uuid4())[:8]
    v = RescueVehicle(
        license_plate=f"29A-{suffix}",
        vehicle_type="Xe cẩu",
        capacity="2 tấn",
        company_id=test_company.id,
        status="available",
        is_active=True
    )
    db_session.add(v)
    db_session.flush()
    db_session.refresh(v)
    return v
