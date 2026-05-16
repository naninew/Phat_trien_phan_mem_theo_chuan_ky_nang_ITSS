import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Fix path to import app correctly
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.abspath(os.path.join(current_dir, "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.main import app
from app.database import Base, get_db
from app.utils.jwt_helper import create_access_token

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_e2e.db"
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

def test_full_rescue_lifecycle():
    # 1. Register Users
    # Customer
    res = client.post("/api/v1/auth/register", json={
        "username": "e2e_cust", "email": "e2e_cust@test.com", "password": "password",
        "full_name": "E2E Customer", "phone": "0911111111", "role": "customer"
    })
    assert res.status_code == 200
    cust_id = res.json()["data"]["user_id"]
    cust_token = create_access_token(data={"sub": "e2e_cust@test.com", "role": "customer", "user_id": cust_id, "username": "e2e_cust"})

    # Company
    res = client.post("/api/v1/auth/register", json={
        "username": "e2e_comp", "email": "e2e_comp@test.com", "password": "password",
        "full_name": "E2E Company Owner", "phone": "0922222222", "role": "company_staff"
    })
    assert res.status_code == 200
    owner_id = res.json()["data"]["user_id"]
    comp_token = create_access_token(data={"sub": "e2e_comp@test.com", "role": "company_staff", "user_id": owner_id, "username": "e2e_comp"})

    # Admin
    admin_token = create_access_token(data={"sub": "admin@test.com", "role": "admin", "user_id": 1, "username": "admin"})

    # 2. Setup Company Profile
    res = client.post("/api/v1/rescue/company/profile", json={
        "company_name": "E2E Rescue Service", "address": "123 E2E St", "hotline": "115",
        "business_license": "E2E-LIC-001",
        "description": "Fast rescue", "latitude": 21.0, "longitude": 105.0, "service_radius_km": 50
    }, headers={"Authorization": f"Bearer {comp_token}"})
    assert res.status_code == 200
    comp_id = res.json()["data"]["id"]

    # 3. Admin verifies Company
    res = client.put(f"/api/v1/admin/companies/{comp_id}/status?status=active", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200

    # 4. Customer adds Vehicle
    res = client.post("/api/v1/profile/vehicles", json={
        "license_plate": "30A-12345", "brand": "Toyota", "model": "Vios", "year": 2022, "fuel_type": "Petrol"
    }, headers={"Authorization": f"Bearer {cust_token}"})
    assert res.status_code == 200
    v_id = res.json()["data"]["id"]

    # 5. Customer creates Rescue Request
    res = client.post("/api/v1/rescue/requests", json={
        "vehicle_id": v_id, "latitude": 21.01, "longitude": 105.01, "address_description": "Near E2E lake",
        "incident_type": "Engine Failure", "description": "Smokes from hood", "service_ids": []
    }, headers={"Authorization": f"Bearer {cust_token}"})
    assert res.status_code == 200
    req_id = res.json()["data"]["id"]

    # 6. Company accepts Request
    res = client.put(f"/api/v1/rescue/requests/{req_id}/accept?eta_minutes=20", headers={"Authorization": f"Bearer {comp_token}"})
    assert res.status_code == 200

    # 7. Company adds Staff and Vehicle, then assigns
    res = client.post("/api/v1/rescue/staff", json={"skill_level": "Trung cấp"}, headers={"Authorization": f"Bearer {comp_token}"})
    assert res.status_code == 200
    staff_id = res.json()["data"]["id"]
    
    res = client.post("/api/v1/rescue/vehicles", json={"plate_number": "RES-001", "vehicle_type": "Xe cẩu", "capacity": "5 tấn"}, headers={"Authorization": f"Bearer {comp_token}"})
    assert res.status_code == 200
    rv_id = res.json()["data"]["id"]
    
    res = client.post(f"/api/v1/rescue/requests/{req_id}/assign", json={"staff_id": staff_id, "rescue_vehicle_id": rv_id, "notes": "Hurry up"}, headers={"Authorization": f"Bearer {comp_token}"})
    assert res.status_code == 200

    # 8. Update workflow
    client.put(f"/api/v1/rescue/requests/{req_id}/status", json={"status": "ON_THE_WAY"}, headers={"Authorization": f"Bearer {comp_token}"})
    client.put(f"/api/v1/rescue/requests/{req_id}/status", json={"status": "IN_PROGRESS"}, headers={"Authorization": f"Bearer {comp_token}"})
    
    # 9. Complete and Pay
    res = client.post(f"/api/v1/rescue/requests/{req_id}/complete", json={"agreed_price": 450000}, headers={"Authorization": f"Bearer {comp_token}"})
    assert res.status_code == 200
    
    res = client.post(f"/api/v1/rescue/requests/{req_id}/payment", json={"amount": 450000, "payment_method": "cash"}, headers={"Authorization": f"Bearer {cust_token}"})
    assert res.status_code == 200

    # 10. Customer reviews
    res = client.post(f"/api/v1/rescue/requests/{req_id}/review?rating=5&comment=Excellent%20e2e!", headers={"Authorization": f"Bearer {cust_token}"})
    assert res.status_code == 200

    # 11. Admin verifies stats
    res = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.json()["data"]["total_revenue"] >= 450000

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
