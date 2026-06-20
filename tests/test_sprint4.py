import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Fix path to import app correctly
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.company import RescueCompany
from app.models.service import Service
from app.models.vehicle import RescueVehicle, Vehicle
from app.models.staff import RescueStaff
from app.models.request import RescueRequest
from app.utils.jwt_helper import create_access_token

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_sprint4.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_data():
    db = TestingSessionLocal()
    
    # 1. Create users
    customer = User(
        username="customer_s4",
        email="customer_s4@example.com",
        password_hash="hashed",
        full_name="Customer S4",
        phone="0111222333",
        role="customer",
        status="ACTIVE"
    )
    company_owner = User(
        username="company_s4",
        email="company_s4@example.com",
        password_hash="hashed",
        full_name="Company S4",
        phone="0444555666",
        role="company_staff",
        status="ACTIVE"
    )
    admin_user = User(
        username="admin_s4",
        email="admin_s4@example.com",
        password_hash="hashed",
        full_name="Admin S4",
        phone="0999888777",
        role="admin",
        status="ACTIVE"
    )
    db.add_all([customer, company_owner, admin_user])
    db.commit()
    for u in [customer, company_owner, admin_user]: db.refresh(u)
    
    # 2. Create Company
    company = RescueCompany(
        owner_id=company_owner.id,
        company_name="Company S4 Ltd",
        business_license="S4-LIC-001",
        address="S4 Test Road",
        hotline="18001111",
        status="active",
        is_verified=True,
        latitude=10.0,
        longitude=10.0
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    
    # 5. Create Customer Vehicle
    c_vehicle = Vehicle(customer_id=customer.id, license_plate="60B-S4", brand="Honda", model="Civic", year=2020, fuel_type="Xăng")
    db.add(c_vehicle)
    db.commit()
    db.refresh(c_vehicle)
    
    # 3. Create a Request (needed for chat)
    request = RescueRequest(
        user_id=customer.id,
        company_id=company.id,
        vehicle_id=c_vehicle.id,
        status="ACCEPTED",
        latitude=10.01,
        longitude=10.01,
        address_description="S4 Test Address",
        incident_type="Other",
        description="Sprint 4 Test"
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    
    # Generate tokens
    customer_token = create_access_token(data={"sub": customer.email, "role": customer.role, "user_id": customer.id, "username": customer.username})
    company_token = create_access_token(data={"sub": company_owner.email, "role": company_owner.role, "user_id": company_owner.id, "username": company_owner.username})
    admin_token = create_access_token(data={"sub": admin_user.email, "role": admin_user.role, "user_id": admin_user.id, "username": admin_user.username})
    
    yield {
        "customer_token": customer_token,
        "company_token": company_token,
        "admin_token": admin_token,
        "request_id": request.id,
        "customer_id": customer.id,
        "company_owner_id": company_owner.id
    }
    
    # Base.metadata.drop_all(bind=engine)

def test_chat_workflow(setup_data):
    headers = {"Authorization": f"Bearer {setup_data['customer_token']}"}
    
    # 1. Send Message
    payload = {
        "request_id": setup_data["request_id"],
        "content": "Hello from customer",
        "receiver_id": setup_data["company_owner_id"],
        "sender_type": "customer"
    }
    res = client.post("/api/v1/chat/messages", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["content"] == "Hello from customer"
    
    # 2. Get Messages
    res = client.get(f"/api/v1/chat/messages/{setup_data['request_id']}", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) >= 1

def test_notification_workflow(setup_data):
    headers = {"Authorization": f"Bearer {setup_data['admin_token']}"}
    
    # Manual insertion of notification since we don't have automatic triggers yet
    db = TestingSessionLocal()
    from app.services import chat_svc
    chat_svc.create_notification(db, setup_data["customer_id"], "Test Title", "Test Content")
    
    # Get Notifications
    c_headers = {"Authorization": f"Bearer {setup_data['customer_token']}"}
    res = client.get("/api/v1/chat/notifications", headers=c_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) >= 1
    notif_id = data[0]["id"]
    
    # Mark as read
    res = client.put(f"/api/v1/chat/notifications/{notif_id}/read", headers=c_headers)
    assert res.status_code == 200

def test_community_workflow(setup_data):
    headers = {"Authorization": f"Bearer {setup_data['customer_token']}"}
    
    # 1. Create Post
    payload = {
        "title": "My car won't start",
        "content": "I tried everything but it still won't start. Any advice?",
        "incident_type": "Dead Battery"
    }
    res = client.post("/api/v1/community/posts", json=payload, headers=headers)
    assert res.status_code == 200
    post_id = res.json()["data"]["id"]
    
    # 2. List Posts
    res = client.get("/api/v1/community/posts")
    assert res.status_code == 200
    assert len(res.json()["data"]) >= 1
    
    # 3. Reply to Post
    reply_payload = {"content": "Check your battery terminals!"}
    res = client.post(f"/api/v1/community/posts/{post_id}/replies", json=reply_payload, headers=headers)
    assert res.status_code == 200
    
    # 4. Get Post Details
    res = client.get(f"/api/v1/community/posts/{post_id}")
    assert res.status_code == 200
    assert len(res.json()["data"]["replies"]) >= 1

def test_reporting_workflow(setup_data):
    headers = {"Authorization": f"Bearer {setup_data['admin_token']}"}
    
    # 1. Admin Stats
    res = client.get("/api/v1/admin/stats", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "total_users" in data
    assert "total_requests" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
