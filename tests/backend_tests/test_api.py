"""
API Integration Tests
Tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.fixtures import db_session, admin_user, company_user, customer_user, test_company, test_vehicle, override_get_db


class TestAuthAPI:
    """Test cases for Authentication API endpoints."""
    
    def test_register_user(self, db_session, override_get_db):
        """Test user registration endpoint."""
        from backend.main import app
        
        # Override dependency
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "role": "CUSTOMER",
                "full_name": "New User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        
        app.dependency_overrides.clear()
    
    def test_login_success(self, db_session, override_get_db, admin_user):
        """Test successful login."""
        from backend.main import app
        
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": admin_user.email,
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        app.dependency_overrides.clear()
    
    def test_login_wrong_password(self, db_session, override_get_db, admin_user):
        """Test login with wrong password."""
        from backend.main import app
        
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": admin_user.email,
                "password": "WrongPassword!"
            }
        )
        
        assert response.status_code == 401
        
        app.dependency_overrides.clear()


class TestUserAPI:
    """Test cases for User API endpoints."""
    
    def test_get_current_user(self, db_session, override_get_db, admin_user, auth_headers):
        """Test getting current user profile."""
        from backend.main import app
        
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.get(
            "/api/v1/users/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == admin_user.username
        assert data["email"] == admin_user.email
        
        app.dependency_overrides.clear()
    
    def test_update_user_profile(self, db_session, override_get_db, admin_user, auth_headers):
        """Test updating user profile."""
        from backend.main import app
        
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={
                "full_name": "Updated Name",
                "phone": "+1234567890"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["phone"] == "+1234567890"
        
        app.dependency_overrides.clear()


class TestCompanyAPI:
    """Test cases for Company API endpoints."""
    
    def test_create_company(self, db_session, override_get_db, company_user, auth_headers):
        """Test creating a company."""
        from backend.main import app
        
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/companies",
            headers=auth_headers,
            json={
                "name": "API Test Company",
                "address": "123 API Street",
                "phone": "+1112223333",
                "email": "api@company.com"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test Company"
        
        app.dependency_overrides.clear()
    
    def test_get_company_list(self, db_session, override_get_db, test_company, auth_headers):
        """Test getting list of companies."""
        from backend.main import app
        
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.get(
            "/api/v1/companies",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        app.dependency_overrides.clear()
    
    def test_get_company_by_id(self, db_session, override_get_db, test_company, auth_headers):
        """Test getting company by ID."""
        from backend.main import app
        
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.get(
            f"/api/v1/companies/{test_company.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_company.id
        assert data["name"] == test_company.name
        
        app.dependency_overrides.clear()


class TestVehicleAPI:
    """Test cases for Vehicle API endpoints."""
    
    def test_create_vehicle(self, db_session, override_get_db, test_company, auth_headers):
        """Test creating a vehicle."""
        from backend.main import app
        
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/vehicles",
            headers=auth_headers,
            json={
                "license_plate": "API-123",
                "vehicle_type": "TRUCK",
                "capacity": 1500,
                "company_id": test_company.id
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["license_plate"] == "API-123"
        
        app.dependency_overrides.clear()
    
    def test_get_vehicles_by_company(self, db_session, override_get_db, test_company, test_vehicle, auth_headers):
        """Test getting vehicles by company."""
        from backend.main import app
        
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.get(
            f"/api/v1/vehicles/company/{test_company.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        app.dependency_overrides.clear()
    
    def test_update_vehicle_status(self, db_session, override_get_db, test_vehicle, auth_headers):
        """Test updating vehicle status."""
        from backend.main import app
        
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.patch(
            f"/api/v1/vehicles/{test_vehicle.id}/status",
            headers=auth_headers,
            json={"status": "IN_SERVICE"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "IN_SERVICE"
        
        app.dependency_overrides.clear()


class TestQueueAPI:
    """Test cases for Queue API endpoints."""
    
    def test_create_queue(self, db_session, override_get_db, test_vehicle, customer_user, auth_headers):
        """Test creating a queue entry."""
        from backend.main import app
        
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/queues",
            headers=auth_headers,
            json={
                "vehicle_id": test_vehicle.id,
                "service_type": "WASH",
                "priority": "NORMAL",
                "estimated_duration": 30
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["service_type"] == "WASH"
        assert data["status"] == "WAITING"
        
        app.dependency_overrides.clear()
    
    def test_get_my_queues(self, db_session, override_get_db, test_queue, auth_headers):
        """Test getting current user's queues."""
        from backend.main import app
        
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.get(
            "/api/v1/queues/my",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        app.dependency_overrides.clear()
    
    def test_update_queue_status(self, db_session, override_get_db, test_queue, auth_headers):
        """Test updating queue status."""
        from backend.main import app
        
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.patch(
            f"/api/v1/queues/{test_queue.id}/status",
            headers=auth_headers,
            json={"status": "IN_PROGRESS"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "IN_PROGRESS"
        
        app.dependency_overrides.clear()
    
    def test_get_queue_position(self, db_session, override_get_db, test_queue, auth_headers):
        """Test getting queue position."""
        from backend.main import app
        
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        response = client.get(
            f"/api/v1/queues/{test_queue.id}/position",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "position" in data
        assert data["position"] >= 1
        
        app.dependency_overrides.clear()
