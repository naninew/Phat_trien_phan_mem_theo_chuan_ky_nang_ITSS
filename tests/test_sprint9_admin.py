"""
Sprint 9 — Kiểm thử API Admin (Task 9.8.1).
"""
import os
import sys
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.abspath(os.path.join(current_dir, "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.main import app
from app.database import Base, get_db
from app.models.user import User, AccountStatus, UserRole
from app.models.company import RescueCompany
from app.models.request import RescueRequest, RequestStatus
from app.models.review import Review
from app.models.vehicle import Vehicle
from app.models.communication import Notification
from app.services import auth_svc
from app.services.notification_svc import NotificationType
from app.utils.jwt_helper import create_access_token

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_sprint9.db"
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

PASSWORD = "Pass123!"


def _admin_token(admin: User) -> str:
    return create_access_token(
        data={"user_id": admin.id, "username": admin.username, "role": admin.role.value}
    )


@pytest.fixture(scope="module")
def setup_sprint9_data():
    db = TestingSessionLocal()
    pwd_hash = auth_svc.hash_password(PASSWORD)

    admin = User(
        username="admin9",
        email="admin9@test.com",
        password_hash=pwd_hash,
        full_name="Admin 9",
        phone="0900000001",
        role=UserRole.ADMIN,
        status=AccountStatus.ACTIVE,
    )
    suspended_user = User(
        username="suspended9",
        email="suspended9@test.com",
        password_hash=pwd_hash,
        full_name="Suspended User",
        phone="0900000002",
        role=UserRole.CUSTOMER,
        status=AccountStatus.SUSPENDED,
    )
    customer_active = User(
        username="cust9",
        email="cust9@test.com",
        password_hash=pwd_hash,
        full_name="Customer 9",
        phone="0900000003",
        role=UserRole.CUSTOMER,
        status=AccountStatus.ACTIVE,
    )
    customer_clear = User(
        username="cust9b",
        email="cust9b@test.com",
        password_hash=pwd_hash,
        full_name="Customer 9b",
        phone="0900000004",
        role=UserRole.CUSTOMER,
        status=AccountStatus.ACTIVE,
    )
    pending_owner = User(
        username="owner9",
        email="owner9@test.com",
        password_hash=pwd_hash,
        full_name="Owner Pending",
        phone="0900000005",
        role=UserRole.COMPANY_STAFF,
        status=AccountStatus.ACTIVE,
    )
    reject_owner = User(
        username="owner9b",
        email="owner9b@test.com",
        password_hash=pwd_hash,
        full_name="Owner Reject",
        phone="0900000006",
        role=UserRole.COMPANY_STAFF,
        status=AccountStatus.ACTIVE,
    )
    review_customer = User(
        username="cust9c",
        email="cust9c@test.com",
        password_hash=pwd_hash,
        full_name="Customer Reviews",
        phone="0900000007",
        role=UserRole.CUSTOMER,
        status=AccountStatus.ACTIVE,
    )
    db.add_all(
        [
            admin,
            suspended_user,
            customer_active,
            customer_clear,
            pending_owner,
            reject_owner,
            review_customer,
        ]
    )
    db.commit()

    cust_vehicle = Vehicle(
        customer_id=customer_active.id,
        license_plate="29A-S9-001",
        brand="Toyota",
        model="Vios",
        year=2020,
        fuel_type="Xăng",
    )
    review_vehicle = Vehicle(
        customer_id=review_customer.id,
        license_plate="29A-S9-002",
        brand="Honda",
        model="City",
        year=2021,
        fuel_type="Xăng",
    )
    db.add_all([cust_vehicle, review_vehicle])
    db.commit()

    active_company = RescueCompany(
        owner_id=pending_owner.id,
        company_name="Active Co 9",
        address="1 Active St",
        business_license="S9-ACTIVE-001",
        hotline="111",
        status="active",
        is_verified=True,
        rating_avg=0.0,
        rating_count=0,
    )
    pending_company = RescueCompany(
        owner_id=pending_owner.id,
        company_name="Pending Co 9",
        address="2 Pending St",
        business_license="S9-PEND-001",
        hotline="222",
        status="pending",
        is_verified=False,
    )
    reject_company = RescueCompany(
        owner_id=reject_owner.id,
        company_name="Reject Co 9",
        address="3 Reject St",
        business_license="S9-REJ-001",
        hotline="333",
        status="pending",
        is_verified=False,
    )
    rating_company = RescueCompany(
        owner_id=pending_owner.id,
        company_name="Rating Co 9",
        address="4 Rating St",
        business_license="S9-RATE-001",
        hotline="444",
        status="active",
        is_verified=True,
        rating_avg=4.0,
        rating_count=2,
    )
    db.add_all([active_company, pending_company, reject_company, rating_company])
    db.commit()

    pending_req = RescueRequest(
        user_id=customer_active.id,
        company_id=active_company.id,
        vehicle_id=cust_vehicle.id,
        status=RequestStatus.PENDING.value,
        incident_type="Flat Tire",
        description="Need help",
        address_description="Hanoi",
        latitude=21.0,
        longitude=105.0,
    )
    now = datetime.utcnow()
    old_req = RescueRequest(
        user_id=review_customer.id,
        company_id=rating_company.id,
        vehicle_id=review_vehicle.id,
        status=RequestStatus.COMPLETED.value,
        incident_type="Battery",
        description="Old request",
        address_description="Hanoi",
        latitude=21.0,
        longitude=105.0,
        created_at=now - timedelta(days=30),
    )
    recent_req = RescueRequest(
        user_id=review_customer.id,
        company_id=rating_company.id,
        vehicle_id=review_vehicle.id,
        status=RequestStatus.COMPLETED.value,
        incident_type="Battery",
        description="Recent request",
        address_description="Hanoi",
        latitude=21.0,
        longitude=105.0,
        created_at=now - timedelta(days=2),
    )
    db.add_all([pending_req, old_req, recent_req])
    db.commit()

    rev_high = Review(
        user_id=review_customer.id,
        company_id=rating_company.id,
        rescue_request_id=old_req.id,
        rating=5,
        comment="Great",
    )
    rev_low = Review(
        user_id=review_customer.id,
        company_id=rating_company.id,
        rescue_request_id=recent_req.id,
        rating=3,
        comment="OK",
    )
    db.add_all([rev_high, rev_low])
    db.commit()

    data = {
        "admin_token": _admin_token(admin),
        "admin_id": admin.id,
        "suspended_username": suspended_user.username,
        "customer_with_pending_id": customer_active.id,
        "customer_clear_id": customer_clear.id,
        "pending_company_id": pending_company.id,
        "pending_owner_id": pending_owner.id,
        "reject_company_id": reject_company.id,
        "reject_owner_id": reject_owner.id,
        "rating_company_id": rating_company.id,
        "review_to_delete_id": rev_high.id,
        "old_request_date": (now - timedelta(days=30)).strftime("%Y-%m-%d"),
        "recent_request_date": (now - timedelta(days=2)).strftime("%Y-%m-%d"),
        "today": now.strftime("%Y-%m-%d"),
    }
    db.close()
    yield data


def test_login_suspended_vs_wrong_password(setup_sprint9_data):
    d = setup_sprint9_data

    wrong = client.post(
        "/api/v1/auth/login",
        json={"username": d["suspended_username"], "password": "WrongPassword!"},
    )
    assert wrong.status_code == 401
    assert "Tên đăng nhập hoặc mật khẩu không đúng" in wrong.json()["detail"]

    suspended = client.post(
        "/api/v1/auth/login",
        json={"username": d["suspended_username"], "password": PASSWORD},
    )
    assert suspended.status_code == 403
    assert "khóa" in suspended.json()["detail"].lower()
    assert suspended.json()["detail"] != wrong.json()["detail"]


def test_suspend_user_missing_reason_returns_422(setup_sprint9_data):
    headers = {"Authorization": f"Bearer {setup_sprint9_data['admin_token']}"}
    user_id = setup_sprint9_data["customer_clear_id"]

    res = client.put(f"/api/v1/admin/users/{user_id}/suspend", headers=headers, json={})
    assert res.status_code == 422


def test_suspend_user_with_pending_request_returns_400(setup_sprint9_data):
    headers = {"Authorization": f"Bearer {setup_sprint9_data['admin_token']}"}
    user_id = setup_sprint9_data["customer_with_pending_id"]

    res = client.put(
        f"/api/v1/admin/users/{user_id}/suspend",
        headers=headers,
        json={"reason": "Vi phạm quy định hệ thống"},
    )
    assert res.status_code == 400
    assert "yêu cầu" in res.json()["detail"].lower()


def test_approve_company_creates_notification(setup_sprint9_data):
    d = setup_sprint9_data
    headers = {"Authorization": f"Bearer {d['admin_token']}"}
    company_id = d["pending_company_id"]
    owner_id = d["pending_owner_id"]

    db = TestingSessionLocal()
    before = (
        db.query(Notification)
        .filter(
            Notification.receiver_id == owner_id,
            Notification.notification_type == NotificationType.ACCOUNT_VERIFIED,
        )
        .count()
    )
    db.close()

    res = client.put(f"/api/v1/admin/companies/{company_id}/approve", headers=headers)
    assert res.status_code == 200

    db = TestingSessionLocal()
    after = (
        db.query(Notification)
        .filter(
            Notification.receiver_id == owner_id,
            Notification.notification_type == NotificationType.ACCOUNT_VERIFIED,
        )
        .count()
    )
    db.close()
    assert after == before + 1


def test_reject_company_notification_includes_reason(setup_sprint9_data):
    d = setup_sprint9_data
    headers = {"Authorization": f"Bearer {d['admin_token']}"}
    company_id = d["reject_company_id"]
    owner_id = d["reject_owner_id"]
    reason = "Giấy phép kinh doanh không hợp lệ"

    res = client.put(
        f"/api/v1/admin/companies/{company_id}/reject",
        headers=headers,
        json={"reason": reason},
    )
    assert res.status_code == 200

    db = TestingSessionLocal()
    notif = (
        db.query(Notification)
        .filter(
            Notification.receiver_id == owner_id,
            Notification.notification_type == NotificationType.ACCOUNT_REJECTED,
        )
        .order_by(Notification.id.desc())
        .first()
    )
    db.close()
    assert notif is not None
    assert reason in notif.content


def test_delete_review_recalculates_rating_avg(setup_sprint9_data):
    d = setup_sprint9_data
    headers = {"Authorization": f"Bearer {d['admin_token']}"}
    review_id = d["review_to_delete_id"]
    company_id = d["rating_company_id"]

    res = client.request(
        "DELETE",
        f"/api/v1/admin/reviews/{review_id}",
        headers=headers,
        json={"reason": "Nội dung không phù hợp quy định"},
    )
    assert res.status_code == 200

    db = TestingSessionLocal()
    company = db.query(RescueCompany).filter(RescueCompany.id == company_id).first()
    remaining = db.query(Review).filter(Review.company_id == company_id).count()
    db.close()

    assert remaining == 1
    assert company.rating_avg == 3.0
    assert company.rating_count == 1


def test_reports_requests_date_range_filter(setup_sprint9_data):
    d = setup_sprint9_data
    headers = {"Authorization": f"Bearer {d['admin_token']}"}

    res = client.get(
        "/api/v1/admin/reports/requests",
        headers=headers,
        params={
            "from_date": d["recent_request_date"],
            "to_date": d["today"],
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_requests"] >= 1
    assert len(data["by_date"]) >= 1

    res_old = client.get(
        "/api/v1/admin/reports/requests",
        headers=headers,
        params={
            "from_date": d["old_request_date"],
            "to_date": (datetime.utcnow() - timedelta(days=20)).strftime("%Y-%m-%d"),
        },
    )
    assert res_old.status_code == 200
    assert res_old.json()["data"]["total_requests"] >= 1


def test_reports_export_excel_returns_xlsx(setup_sprint9_data):
    headers = {"Authorization": f"Bearer {setup_sprint9_data['admin_token']}"}

    res = client.get(
        "/api/v1/admin/reports/export/excel",
        headers=headers,
        params={"report_type": "requests"},
    )
    assert res.status_code == 200
    assert (
        res.headers.get("content-type", "")
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert res.content[:2] == b"PK"
