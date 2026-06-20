import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.company import RescueCompany
from app.models.service import Service
from app.models.vehicle import RescueVehicle, Vehicle
from app.models.staff import RescueStaff
from app.utils.jwt_helper import create_access_token

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_rescue_system.db"
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
        username="customer_test",
        email="customer_test@example.com",
        password_hash="hashed_pw",
        full_name="Customer Test",
        phone="0123456789",
        role="customer",
        status="ACTIVE"
    )
    company_owner = User(
        username="company_owner_test",
        email="company_test@example.com",
        password_hash="hashed_pw",
        full_name="Company Test",
        phone="0987654321",
        role="company_staff",
        status="ACTIVE"
    )
    db.add(customer)
    db.add(company_owner)
    db.commit()
    db.refresh(customer)
    db.refresh(company_owner)
    
    # 2. Create Company
    company = RescueCompany(
        owner_id=company_owner.id,
        company_name="Rescue Test Co",
        business_license="GP123456",
        address="123 Test St",
        hotline="19001234",
        status="active",
        is_verified=True,
        latitude=10.0,
        longitude=10.0,
        service_radius_km=50
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    
    # 3. Create Services
    service1 = Service(company_id=company.id, service_name="Vá lốp", base_price=50000, estimated_duration=30, is_active=True)
    service2 = Service(company_id=company.id, service_name="Kéo xe", base_price=500000, estimated_duration=60, is_active=True)
    db.add(service1)
    db.add(service2)
    db.commit()
    db.refresh(service1)
    db.refresh(service2)
    
    # 4. Create Staff and Rescue Vehicle
    staff = RescueStaff(company_id=company.id, skill_level="expert", status="AVAILABLE")
    r_vehicle = RescueVehicle(company_id=company.id, plate_number="59A-12345", vehicle_type="xe_keo", capacity=2.0, status="available")
    db.add(staff)
    db.add(r_vehicle)
    db.commit()
    db.refresh(staff)
    db.refresh(r_vehicle)
    
    # 5. Create Customer Vehicle
    c_vehicle = Vehicle(customer_id=customer.id, license_plate="60B-67890", brand="Honda", model="Civic", year=2020, fuel_type="Xăng")
    db.add(c_vehicle)
    db.commit()
    db.refresh(c_vehicle)
    
    # Generate tokens
    customer_token = create_access_token(data={"sub": customer.email, "role": customer.role, "user_id": customer.id, "username": customer.username})
    company_token = create_access_token(data={"sub": company_owner.email, "role": company_owner.role, "user_id": company_owner.id, "username": company_owner.username})
    
    yield {
        "customer_token": customer_token,
        "company_token": company_token,
        "company_id": company.id,
        "service1_id": service1.id,
        "service2_id": service2.id,
        "customer_vehicle_id": c_vehicle.id,
        "staff_id": staff.id,
        "rescue_vehicle_id": r_vehicle.id
    }
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)

def test_full_rescue_workflow(setup_data):
    # Setup headers
    customer_headers = {"Authorization": f"Bearer {setup_data['customer_token']}"}
    company_headers = {"Authorization": f"Bearer {setup_data['company_token']}"}
    
    # 1. Customer matching
    res = client.get(f"/api/v1/rescue/companies/nearby?latitude=10.0&longitude=10.0&service_ids={setup_data['service1_id']}&service_ids={setup_data['service2_id']}", headers=customer_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) > 0
    assert data[0]["company_name"] == "Rescue Test Co"
    
    # 2. Customer create request
    req_payload = {
        "service_ids": [setup_data["service1_id"], setup_data["service2_id"]],
        "vehicle_id": setup_data["customer_vehicle_id"],
        "latitude": 10.01,
        "longitude": 10.01,
        "address_description": "Ngã tư Test",
        "incident_type": "Tai nạn",
        "description": "Cần kéo xe và vá lốp",
        "payment_method": "cash"
    }
    res = client.post("/api/v1/rescue/requests", json=req_payload, headers=customer_headers)
    assert res.status_code == 200
    request_id = res.json()["data"]["id"]
    
    # 3. Company checks queue
    res = client.get("/api/v1/rescue/queue", headers=company_headers)
    assert res.status_code == 200
    
    # 4. Company accepts
    res = client.put(f"/api/v1/rescue/requests/{request_id}/accept?eta_minutes=15", headers=company_headers)
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "ACCEPTED"
    
    # 5. Company assigns
    assign_payload = {
        "staff_id": setup_data["staff_id"],
        "rescue_vehicle_id": setup_data["rescue_vehicle_id"],
        "notes": "Đi nhanh"
    }
    res = client.post(f"/api/v1/rescue/requests/{request_id}/assign", json=assign_payload, headers=company_headers)
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "ASSIGNED"
    
    # 6. Company update status to IN_PROGRESS
    status_payload = {"status": "IN_PROGRESS", "eta_minutes": 0}
    res = client.put(f"/api/v1/rescue/requests/{request_id}/status", json=status_payload, headers=company_headers)
    assert res.status_code == 200
    
    # 7. Company update status to COMPLETED
    status_payload = {"status": "COMPLETED", "agreed_price": 550000}
    res = client.put(f"/api/v1/rescue/requests/{request_id}/status", json=status_payload, headers=company_headers)
    assert res.status_code == 200
    
    # 8. Customer payments
    payment_payload = {
        "amount": 550000,
        "payment_method": "momo",
        "transaction_id": "MOMO123"
    }
    res = client.post(f"/api/v1/rescue/requests/{request_id}/payment", json=payment_payload, headers=customer_headers)
    assert res.status_code == 200
    assert res.json()["data"]["payment_status"] == "paid"
    
    print("All assertions passed!")
    
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
