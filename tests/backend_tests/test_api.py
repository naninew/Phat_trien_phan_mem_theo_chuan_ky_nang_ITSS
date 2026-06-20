"""
API Integration Tests
Tests for FastAPI endpoints matching the current backend architecture.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from tests.fixtures import (
    db_session, test_engine, override_get_db, 
    test_admin, test_customer, test_company_staff, 
    test_company, test_service, test_vehicle
)


class TestAuthAPI:
    """Test cases for Authentication API endpoints."""
    
    def test_register_user(self, db_session, override_get_db):
        """Test user registration."""
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        
        payload = {
            "username": "tester123",
            "password": "Password123!",
            "full_name": "Test User",
            "phone": "0988888888",
            "email": "tester@example.com"
        }
        
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["username"] == "tester123"
        
        app.dependency_overrides.clear()

    def test_login_success(self, db_session, override_get_db, test_customer):
        """Test successful login."""
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        
        payload = {
            "username": test_customer.username,
            "password": "Pass123!" # Khớp với fixture
        }
        
        response = client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["data"]
        assert data["data"]["user"]["username"] == test_customer.username
        
        app.dependency_overrides.clear()


class TestRescueAPI:
    """Test cases for Rescue operations."""

    def test_get_services(self, db_session, override_get_db, test_service):
        """Test getting list of services."""
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        
        response = client.get("/api/v1/rescue/services")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1
        assert data["data"][0]["service_name"] == test_service.service_name
        
        app.dependency_overrides.clear()

    def test_find_nearby_companies(self, db_session, override_get_db, test_company, test_service):
        """Test searching for nearby companies."""
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        
        # Vị trí gần Hồ Hoàn Kiếm (khớp với fixture)
        params = {
            "latitude": 21.028,
            "longitude": 105.854,
            "service_id": test_service.id,
            "radius_km": 10.0
        }
        
        response = client.get("/api/v1/rescue/companies/nearby", params=params)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1
        assert data["data"][0]["company_name"] == test_company.company_name
        
        app.dependency_overrides.clear()

    def test_create_rescue_request(self, db_session, override_get_db, test_customer, test_service, test_company):
        """Test creating a new rescue request."""
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        
        # Login để lấy token
        login_res = client.post("/api/v1/auth/login", json={"username": test_customer.username, "password": "Pass123!"})
        token = login_res.json()["data"]["access_token"]
        
        payload = {
            "service_id": test_service.id,
            "company_id": test_company.id,
            "latitude": 21.028,
            "longitude": 105.854,
            "address_description": "Ngã tư Tràng Tiền",
            "car_issue_detail": "Xe bị xịt lốp",
            "payment_method": "cash"
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/v1/rescue/requests", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "pending"
        assert data["data"]["address_description"] == payload["address_description"]
        
        app.dependency_overrides.clear()


class TestCompanyWorkflow:
    """Test cases for company staff operations."""

    def test_get_company_queue(self, db_session, override_get_db, test_company_staff, test_company):
        """Test getting the queue for a company."""
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        
        # Login as staff
        login_res = client.post("/api/v1/auth/login", json={"username": test_company_staff.username, "password": "Pass123!"})
        token = login_res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/rescue/queue", headers=headers)
        assert response.status_code == 200
        assert "data" in response.json()
        
        app.dependency_overrides.clear()

    def test_accept_request(self, db_session, override_get_db, test_company_staff, test_vehicle):
        """Test accepting a request (Requires an existing request)."""
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        
        # 1. Tạo request trước (bằng customer)
        from app.models.user import UserRole
        from app.models.request import RescueRequest
        
        # Mock request trực tiếp vào DB để nhanh
        req = RescueRequest(
            user_id=1, # Mock ID
            company_id=test_vehicle.company_id,
            service_id=1,
            latitude=21.0, longitude=105.0,
            address_description="Test", car_issue_detail="Test",
            status="pending"
        )
        db_session.add(req)
        db_session.flush()
        db_session.refresh(req)
        
        # 2. Login as staff
        login_res = client.post("/api/v1/auth/login", json={"username": test_company_staff.username, "password": "Pass123!"})
        token = login_res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Chấp nhận
        params = {"eta_minutes": 20, "vehicle_id": test_vehicle.id}
        response = client.post(f"/api/v1/rescue/requests/{req.id}/accept", params=params, headers=headers)
        
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "accepted"
        
        app.dependency_overrides.clear()


class TestAdminAPI:
    """Test cases for admin management."""

    def test_get_stats(self, db_session, override_get_db, test_admin):
        """Test getting system stats."""
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        
        login_res = client.post("/api/v1/auth/login", json={"username": test_admin.username, "password": "Pass123!"})
        token = login_res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/admin/stats", headers=headers)
        assert response.status_code == 200
        assert "total_users" in response.json()["data"]
        
        app.dependency_overrides.clear()
