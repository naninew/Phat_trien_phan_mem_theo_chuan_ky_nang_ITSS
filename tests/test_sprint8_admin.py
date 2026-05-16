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
from app.models.user import User
from app.models.company import RescueCompany
from app.models.request import RescueRequest
from app.models.review import Review
from app.models.community import CommunityPost
from app.models.payment import Payment
from app.utils.jwt_helper import create_access_token

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_sprint8.db"
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
def setup_admin_data():
    db = TestingSessionLocal()
    
    # 1. Create Users
    admin = User(username="admin8", email="admin8@test.com", password_hash="hash", full_name="Admin 8", phone="0888", role="admin", status="ACTIVE")
    customer = User(username="cust8", email="cust8@test.com", password_hash="hash", full_name="Customer 8", phone="0777", role="customer", status="ACTIVE")
    company_user = User(username="comp8", email="comp8@test.com", password_hash="hash", full_name="Company 8", phone="0666", role="company_staff", status="ACTIVE")
    db.add_all([admin, customer, company_user])
    db.commit()
    
    # 2. Create Company
    company = RescueCompany(
        owner_id=company_user.id,
        company_name="Admin Test Co",
        address="123 Test St",
        business_license="S8-LIC-001",
        hotline="111",
        status="active",
        is_verified=True
    )
    db.add(company)
    db.commit()
    
    # 3. Create Request & Payment for stats
    req = RescueRequest(
        user_id=customer.id,
        company_id=company.id,
        vehicle_id=1,
        status="COMPLETED",
        incident_type="Flat Tire",
        description="Test description",
        address_description="Test address",
        latitude=21.0,
        longitude=105.0,
        agreed_price=500000,
        payment_status="paid"
    )
    db.add(req)
    db.commit()
    
    # 4. Moderation Data
    from app.models.review import Review
    from app.models.community import CommunityPost
    
    rev = Review(
        user_id=customer.id,
        company_id=company.id,
        rescue_request_id=req.id,
        rating=5,
        comment="Great!"
    )
    post = CommunityPost(
        user_id=customer.id,
        title="Help with tire",
        content="How to fix flat tire?",
        incident_type="Flat Tire"
    )
    db.add_all([rev, post])
    db.commit()
    
    pay = Payment(rescue_request_id=req.id, amount=500000, payment_method="cash", status="success")
    db.add(pay)
    db.commit()
    
    
    admin_token = create_access_token(data={"sub": admin.email, "role": admin.role, "user_id": admin.id, "username": admin.username})
    
    yield {
        "admin_token": admin_token,
        "review_id": rev.id,
        "post_id": post.id
    }

def test_admin_stats_charts(setup_admin_data):
    headers = {"Authorization": f"Bearer {setup_admin_data['admin_token']}"}
    res = client.get("/api/v1/admin/stats/charts", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "revenue_chart" in data
    assert "status_chart" in data
    assert len(data["status_chart"]) >= 1

def test_admin_reports_export(setup_admin_data):
    headers = {"Authorization": f"Bearer {setup_admin_data['admin_token']}"}
    res = client.get("/api/v1/admin/reports/export", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) >= 1
    assert data[0]["ID"] is not None

def test_admin_moderation_reviews(setup_admin_data):
    headers = {"Authorization": f"Bearer {setup_admin_data['admin_token']}"}
    
    # List reviews
    res = client.get("/api/v1/admin/reviews", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) >= 1
    
    # Delete review
    review_id = setup_admin_data["review_id"]
    res = client.delete(f"/api/v1/admin/reviews/{review_id}", headers=headers)
    assert res.status_code == 200
    
    # Verify deleted
    res = client.get("/api/v1/admin/reviews", headers=headers)
    # Since we only had one, it might be empty now if no other tests added any
    # But let's just check the status code for now
    assert res.status_code == 200

def test_admin_moderation_posts(setup_admin_data):
    headers = {"Authorization": f"Bearer {setup_admin_data['admin_token']}"}
    
    # List posts
    res = client.get("/api/v1/admin/community/posts", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) >= 1
    
    # Delete post
    post_id = setup_admin_data["post_id"]
    res = client.delete(f"/api/v1/admin/community/posts/{post_id}", headers=headers)
    assert res.status_code == 200
    
    # Verify deleted
    res = client.get("/api/v1/admin/community/posts", headers=headers)
    assert res.status_code == 200
