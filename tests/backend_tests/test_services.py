"""
Backend Unit Tests
Tests for services, models, and business logic.
"""

import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from tests.fixtures import db_session, admin_user, company_user, customer_user, test_company, test_vehicle


class TestUserService:
    """Test cases for User Service."""
    
    def test_create_admin_user(self, db_session: Session):
        """Test creating an admin user."""
        from backend.schemas.user import UserCreate
        from backend.services.user_service import UserService
        from backend.models.user import UserRole
        
        user_data = UserCreate(
            username="test_admin",
            email="test_admin@example.com",
            password="SecurePass123!",
            role=UserRole.ADMIN,
            full_name="Test Admin User"
        )
        
        user = UserService.create_user(db_session, user_data)
        
        assert user is not None
        assert user.username == "test_admin"
        assert user.email == "test_admin@example.com"
        assert user.role == UserRole.ADMIN
        assert user.full_name == "Test Admin User"
        assert user.is_active is True
        assert user.password_hash is not None
        assert user.password_hash != "SecurePass123!"  # Password should be hashed
    
    def test_create_duplicate_user(self, db_session: Session, admin_user):
        """Test creating a user with duplicate email."""
        from backend.schemas.user import UserCreate
        from backend.services.user_service import UserService
        from backend.models.user import UserRole
        
        user_data = UserCreate(
            username="duplicate_admin",
            email=admin_user.email,  # Same email as existing user
            password="SecurePass123!",
            role=UserRole.ADMIN,
            full_name="Duplicate Admin"
        )
        
        with pytest.raises(ValueError) as exc_info:
            UserService.create_user(db_session, user_data)
        
        assert "already exists" in str(exc_info.value).lower()
    
    def test_authenticate_user_success(self, db_session: Session, admin_user):
        """Test successful user authentication."""
        from backend.services.user_service import UserService
        
        authenticated_user = UserService.authenticate_user(
            db_session, 
            admin_user.email, 
            "SecurePass123!"
        )
        
        assert authenticated_user is not None
        assert authenticated_user.id == admin_user.id
        assert authenticated_user.username == admin_user.username
    
    def test_authenticate_user_wrong_password(self, db_session: Session, admin_user):
        """Test authentication with wrong password."""
        from backend.services.user_service import UserService
        
        authenticated_user = UserService.authenticate_user(
            db_session, 
            admin_user.email, 
            "WrongPassword123!"
        )
        
        assert authenticated_user is None
    
    def test_get_user_by_id(self, db_session: Session, admin_user):
        """Test getting user by ID."""
        from backend.services.user_service import UserService
        
        user = UserService.get_user_by_id(db_session, admin_user.id)
        
        assert user is not None
        assert user.id == admin_user.id
        assert user.username == admin_user.username
    
    def test_update_user(self, db_session: Session, admin_user):
        """Test updating user information."""
        from backend.schemas.user import UserUpdate
        from backend.services.user_service import UserService
        
        update_data = UserUpdate(
            full_name="Updated Admin Name",
            phone="+9876543210"
        )
        
        updated_user = UserService.update_user(db_session, admin_user.id, update_data)
        
        assert updated_user.full_name == "Updated Admin Name"
        assert updated_user.phone == "+9876543210"
        assert updated_user.username == admin_user.username  # Unchanged
    
    def test_deactivate_user(self, db_session: Session, admin_user):
        """Test deactivating a user."""
        from backend.services.user_service import UserService
        
        deactivated_user = UserService.deactivate_user(db_session, admin_user.id)
        
        assert deactivated_user.is_active is False


class TestCompanyService:
    """Test cases for Company Service."""
    
    def test_create_company(self, db_session: Session, company_user):
        """Test creating a company."""
        from backend.services.company_service import CompanyService
        
        company_data = {
            "name": "New Transport Co",
            "address": "456 New Street",
            "phone": "+1112223333",
            "email": "new@company.com",
            "owner_id": company_user.id
        }
        
        company = CompanyService.create_company(db_session, **company_data)
        
        assert company is not None
        assert company.name == "New Transport Co"
        assert company.address == "456 New Street"
        assert company.owner_id == company_user.id
        assert company.is_active is True
    
    def test_get_company_by_id(self, db_session: Session, test_company):
        """Test getting company by ID."""
        from backend.services.company_service import CompanyService
        
        company = CompanyService.get_company_by_id(db_session, test_company.id)
        
        assert company is not None
        assert company.id == test_company.id
        assert company.name == test_company.name
    
    def test_update_company(self, db_session: Session, test_company):
        """Test updating company information."""
        from backend.services.company_service import CompanyService
        
        updated_company = CompanyService.update_company(
            db_session, 
            test_company.id,
            name="Updated Company Name",
            phone="+9998887777"
        )
        
        assert updated_company.name == "Updated Company Name"
        assert updated_company.phone == "+9998887777"
    
    def test_get_companies_by_owner(self, db_session: Session, company_user):
        """Test getting all companies owned by a user."""
        from backend.services.company_service import CompanyService
        
        # Create another company
        CompanyService.create_company(
            db_session,
            name="Second Company",
            address="789 Second St",
            phone="+5556667777",
            email="second@company.com",
            owner_id=company_user.id
        )
        
        companies = CompanyService.get_companies_by_owner(db_session, company_user.id)
        
        assert len(companies) >= 2


class TestVehicleService:
    """Test cases for Vehicle Service."""
    
    def test_create_vehicle(self, db_session: Session, test_company):
        """Test creating a vehicle."""
        from backend.services.vehicle_service import VehicleService
        
        vehicle_data = {
            "license_plate": "XYZ-789",
            "vehicle_type": "VAN",
            "capacity": 500,
            "company_id": test_company.id,
            "status": "AVAILABLE"
        }
        
        vehicle = VehicleService.create_vehicle(db_session, **vehicle_data)
        
        assert vehicle is not None
        assert vehicle.license_plate == "XYZ-789"
        assert vehicle.vehicle_type == "VAN"
        assert vehicle.capacity == 500
        assert vehicle.company_id == test_company.id
    
    def test_get_vehicle_by_id(self, db_session: Session, test_vehicle):
        """Test getting vehicle by ID."""
        from backend.services.vehicle_service import VehicleService
        
        vehicle = VehicleService.get_vehicle_by_id(db_session, test_vehicle.id)
        
        assert vehicle is not None
        assert vehicle.id == test_vehicle.id
        assert vehicle.license_plate == test_vehicle.license_plate
    
    def test_update_vehicle_status(self, db_session: Session, test_vehicle):
        """Test updating vehicle status."""
        from backend.services.vehicle_service import VehicleService
        
        updated_vehicle = VehicleService.update_vehicle_status(
            db_session, 
            test_vehicle.id, 
            "IN_SERVICE"
        )
        
        assert updated_vehicle.status == "IN_SERVICE"
    
    def test_get_vehicles_by_company(self, db_session: Session, test_company):
        """Test getting all vehicles for a company."""
        from backend.services.vehicle_service import VehicleService
        
        # Create another vehicle
        VehicleService.create_vehicle(
            db_session,
            license_plate="DEF-456",
            vehicle_type="TRUCK",
            capacity=2000,
            company_id=test_company.id,
            status="AVAILABLE"
        )
        
        vehicles = VehicleService.get_vehicles_by_company(db_session, test_company.id)
        
        assert len(vehicles) >= 2


class TestQueueService:
    """Test cases for Queue Service."""
    
    def test_create_queue(self, db_session: Session, customer_user, test_vehicle):
        """Test creating a queue entry."""
        from backend.services.queue_service import QueueService
        
        queue_data = {
            "customer_id": customer_user.id,
            "vehicle_id": test_vehicle.id,
            "service_type": "MAINTENANCE",
            "priority": "HIGH",
            "estimated_duration": 60
        }
        
        queue = QueueService.create_queue(db_session, **queue_data)
        
        assert queue is not None
        assert queue.customer_id == customer_user.id
        assert queue.vehicle_id == test_vehicle.id
        assert queue.service_type == "MAINTENANCE"
        assert queue.priority == "HIGH"
        assert queue.status == "WAITING"
    
    def test_get_queue_by_id(self, db_session: Session, test_queue):
        """Test getting queue by ID."""
        from backend.services.queue_service import QueueService
        
        queue = QueueService.get_queue_by_id(db_session, test_queue.id)
        
        assert queue is not None
        assert queue.id == test_queue.id
        assert queue.status == test_queue.status
    
    def test_update_queue_status(self, db_session: Session, test_queue):
        """Test updating queue status."""
        from backend.services.queue_service import QueueService
        
        updated_queue = QueueService.update_queue_status(
            db_session, 
            test_queue.id, 
            "IN_PROGRESS"
        )
        
        assert updated_queue.status == "IN_PROGRESS"
    
    def test_get_queues_by_customer(self, db_session: Session, customer_user, test_vehicle):
        """Test getting all queues for a customer."""
        from backend.services.queue_service import QueueService
        
        # Create another queue
        QueueService.create_queue(
            db_session,
            customer_id=customer_user.id,
            vehicle_id=test_vehicle.id,
            service_type="INSPECTION",
            priority="NORMAL",
            estimated_duration=45
        )
        
        queues = QueueService.get_queues_by_customer(db_session, customer_user.id)
        
        assert len(queues) >= 2
    
    def test_get_queues_by_status(self, db_session: Session, test_queue):
        """Test getting queues by status."""
        from backend.services.queue_service import QueueService
        
        queues = QueueService.get_queues_by_status(db_session, "WAITING")
        
        assert len(queues) >= 1
        assert all(q.status == "WAITING" for q in queues)
    
    def test_calculate_queue_position(self, db_session: Session, test_queue):
        """Test calculating queue position."""
        from backend.services.queue_service import QueueService
        
        position = QueueService.calculate_queue_position(
            db_session, 
            test_queue.id,
            test_queue.vehicle_id
        )
        
        assert position >= 1
