"""
Test Fixtures and Configuration
Provides shared fixtures, database setup, and test utilities.
"""

import os
import sys
import pytest
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.session import get_db, Base
from backend.models.user import User, UserRole
from backend.models.company import Company
from backend.models.vehicle import Vehicle
from backend.models.queue import Queue, QueueStatus
from backend.schemas.user import UserCreate
from backend.services.user_service import UserService
from backend.services.company_service import CompanyService
from backend.services.vehicle_service import VehicleService
from backend.services.queue_service import QueueService

# Test Database URL (SQLite in-memory for fast unit tests)
TEST_DATABASE_URL = "sqlite:///:memory:"

# For integration tests with PostgreSQL (uncomment and configure if needed)
# TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://test:test@localhost:5432/test_db")


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {},
        poolclass=StaticPool if "sqlite" in TEST_DATABASE_URL else None,
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
def admin_user(db_session: Session) -> User:
    """Create a test admin user."""
    user_data = UserCreate(
        username="admin_test",
        email="admin@test.com",
        password="SecurePass123!",
        role=UserRole.ADMIN,
        full_name="Test Admin"
    )
    user = UserService.create_user(db_session, user_data)
    db_session.commit()
    return user


@pytest.fixture
def company_user(db_session: Session) -> User:
    """Create a test company staff user."""
    user_data = UserCreate(
        username="company_test",
        email="company@test.com",
        password="SecurePass123!",
        role=UserRole.COMPANY_STAFF,
        full_name="Test Company Staff"
    )
    user = UserService.create_user(db_session, user_data)
    db_session.commit()
    return user


@pytest.fixture
def customer_user(db_session: Session) -> User:
    """Create a test customer user."""
    user_data = UserCreate(
        username="customer_test",
        email="customer@test.com",
        password="SecurePass123!",
        role=UserRole.CUSTOMER,
        full_name="Test Customer"
    )
    user = UserService.create_user(db_session, user_data)
    db_session.commit()
    return user


@pytest.fixture
def test_company(db_session: Session, company_user: User) -> Company:
    """Create a test company."""
    company_data = {
        "name": "Test Transport Company",
        "address": "123 Test Street",
        "phone": "+1234567890",
        "email": "company@test.com",
        "owner_id": company_user.id
    }
    company = CompanyService.create_company(db_session, **company_data)
    db_session.commit()
    return company


@pytest.fixture
def test_vehicle(db_session: Session, test_company: Company) -> Vehicle:
    """Create a test vehicle."""
    vehicle_data = {
        "license_plate": "ABC-123",
        "vehicle_type": "TRUCK",
        "capacity": 1000,
        "company_id": test_company.id,
        "status": "AVAILABLE"
    }
    vehicle = VehicleService.create_vehicle(db_session, **vehicle_data)
    db_session.commit()
    return vehicle


@pytest.fixture
def test_queue(db_session: Session, customer_user: User, test_vehicle: Vehicle) -> Queue:
    """Create a test queue entry."""
    queue_data = {
        "customer_id": customer_user.id,
        "vehicle_id": test_vehicle.id,
        "service_type": "WASH",
        "priority": "NORMAL",
        "estimated_duration": 30
    }
    queue = QueueService.create_queue(db_session, **queue_data)
    db_session.commit()
    return queue


@pytest.fixture
def auth_headers(admin_user: User) -> dict:
    """Generate authentication headers for API tests."""
    # In real implementation, this would generate a JWT token
    # For now, we'll use a simple token format
    return {"Authorization": f"Bearer test_token_{admin_user.id}"}
