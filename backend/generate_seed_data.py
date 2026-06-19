"""
Script tạo dữ liệu mẫu (Seed Data) cho hệ thống Rescue System.
Chạy script này sẽ XÓA TOÀN BỘ dữ liệu cũ và tạo lại schema + ~10 bản ghi mỗi bảng.
"""
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base, DATABASE_URL, _SQLITE_PATH
from app.models import (  # noqa: F401 — đăng ký toàn bộ model vào metadata
    user,
    company,
    service,
    vehicle,
    staff,
    request,
    review,
    payment,
    community,
    communication,
    report,
)
from app.models.user import User, UserRole, AccountStatus
from app.models.company import RescueCompany
from app.models.service import Service
from app.models.vehicle import Vehicle, RescueVehicle
from app.models.staff import RescueStaff, StaffStatus
from app.models.request import RescueRequest, RequestStatus, RequestService, ServiceAssignment
from app.models.payment import Payment
from app.models.communication import Message, Notification
from app.models.review import Review
from app.models.community import CommunityPost, CommunityReply
from app.models.report import Report
from app.services.auth_svc import hash_password

ROWS_PER_TABLE = 10
PASSWORD = "Pass123!"
ADMIN_PASSWORD = "Admin123!"

COMPANIES_DATA = [
    ("Cứu Hộ Thăng Long", "15 Đinh Tiên Hoàng, Hà Nội", 21.0285, 105.8542),
    ("Tây Hồ Express", "88 Xuân Thủy, Hà Nội", 21.0380, 105.7840),
    ("Hà Đông Car Service", "10 Trần Phú, Hà Đông", 20.9721, 105.7761),
    ("Long Biên Rescue 24/7", "120 Nguyễn Sơn, Long Biên", 21.0450, 105.8800),
    ("Cầu Giấy Auto Aid", "45 Phạm Hùng, Cầu Giấy", 21.0330, 105.7900),
    ("Nam Từ Liêm Cứu Hộ", "8 Mễ Trì, Nam Từ Liêm", 21.0100, 105.7700),
    ("Đống Đa Road Assist", "22 Tây Sơn, Đống Đa", 21.0150, 105.8250),
    ("Hoàng Mai Towing", "5 Tam Trinh, Hoàng Mai", 20.9700, 105.8600),
    ("Ba Đình Emergency", "1 Hoàng Diệu, Ba Đình", 21.0350, 105.8350),
    ("Thanh Xuân Quick Fix", "60 Nguyễn Trãi, Thanh Xuân", 20.9950, 105.8050),
]

SERVICE_TEMPLATES = [
    ("Kéo xe ô tô", 500_000, 60),
    ("Kích bình ắc quy", 150_000, 20),
    ("Thay lốp dự phòng", 200_000, 30),
    ("Vá lốp tại chỗ", 120_000, 25),
    ("Cấp nhiên liệu khẩn cấp", 180_000, 15),
]

RESCUE_VEHICLE_TYPES = ["Xe cẩu", "Xe bệ trượt", "Xe kích bình", "Xe chở ô tô"]
STAFF_LEVELS = ["Sơ cấp", "Trung cấp", "Cao cấp"]
CAR_BRANDS = ["Toyota", "Honda", "Kia", "Mazda", "Hyundai", "Ford", "VinFast"]
INCIDENT_TYPES = ["Thủng lốp", "Chết máy", "Hết xăng", "Tai nạn nhẹ", "Kẹt phanh"]
COMMUNITY_TITLES = [
    "Xe không nổ máy buổi sáng",
    "Đèn cảnh báo ABS sáng liên tục",
    "Nên dùng xăng A95 hay E5?",
    "Xe bị ngập nước có sửa được không?",
    "Máy phát điện mini có đủ kích bình?",
    "Lốp rung khi chạy 80km/h",
    "Bảo dưỡng định kỳ bao lâu một lần?",
    "Xe điện hết pin giữa đường",
    "Tiếng kêu lạ từ gầm xe",
    "Chọn dịch vụ cứu hộ uy tín",
]
REPORT_TYPES = [
    "revenue_summary",
    "request_volume",
    "company_performance",
    "payment_breakdown",
    "customer_activity",
    "service_usage",
    "cancellation_rate",
    "rating_overview",
    "staff_utilization",
    "monthly_dashboard",
]

# 9 hoàn thành + 1 chờ — đủ ~10 payment/review; vẫn có trạng thái PENDING để demo
REQUEST_STATUSES = (
    [RequestStatus.COMPLETED] * 9
    + [RequestStatus.PENDING]
)

ASSIGNMENT_STATUSES = {
    RequestStatus.ASSIGNED,
    RequestStatus.ON_THE_WAY,
    RequestStatus.IN_PROGRESS,
    RequestStatus.COMPLETED,
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def reset_db() -> None:
    print("INFO: Dang xoa du lieu cu...")
    if DATABASE_URL.startswith("sqlite") and os.path.isfile(_SQLITE_PATH):
        engine.dispose()
        os.remove(_SQLITE_PATH)
        print("INFO: Da xoa file SQLite cu (bao gom bang legacy).")
    else:
        Base.metadata.drop_all(bind=engine)
    print("INFO: Dang tao lai cau truc co so du lieu...")
    Base.metadata.create_all(bind=engine)


def _unique_plates(count: int, prefix: str) -> list[str]:
    plates = set()
    while len(plates) < count:
        plates.add(f"{prefix}-{random.randint(10000, 99999)}")
    return list(plates)


def seed_data() -> None:
    print(f"START: Tao du lieu mau (~{ROWS_PER_TABLE} dong/bang)...")
    reset_db()
    db = SessionLocal()

    try:
        # ── users: 1 admin + 10 customers + 10 company_staff = 21 (can bang FK cong ty) ──
        admin = User(
            username="admin",
            password_hash=hash_password(ADMIN_PASSWORD),
            full_name="Tổng Quản Trị",
            phone="0900000000",
            email="admin@rescue.vn",
            role=UserRole.ADMIN,
            status=AccountStatus.ACTIVE,
            address="Hà Nội",
        )
        db.add(admin)

        customers: list[User] = []
        for i in range(1, ROWS_PER_TABLE + 1):
            c = User(
                username=f"customer{i}",
                password_hash=hash_password(PASSWORD),
                full_name=f"Khách Hàng {i}",
                phone=f"0912000{i:04d}",
                email=f"customer{i}@example.com",
                role=UserRole.CUSTOMER,
                status=AccountStatus.ACTIVE,
                address=f"Quận {(i % 12) + 1}, Hà Nội",
            )
            db.add(c)
            customers.append(c)
        db.flush()

        company_owners: list[User] = []
        for i in range(1, ROWS_PER_TABLE + 1):
            owner = User(
                username=f"company{i}",
                password_hash=hash_password(PASSWORD),
                full_name=f"Quản Lý Công Ty {i}",
                phone=f"0988000{i:04d}",
                email=f"staff{i}@cuuho.vn",
                role=UserRole.COMPANY_STAFF,
                status=AccountStatus.ACTIVE,
                address=COMPANIES_DATA[i - 1][1],
            )
            db.add(owner)
            company_owners.append(owner)
        db.flush()

        # ── vehicles (khách hàng): 10 ──
        customer_plates = _unique_plates(ROWS_PER_TABLE, "30A")
        vehicles: list[Vehicle] = []
        for i, c in enumerate(customers):
            v = Vehicle(
                customer_id=c.id,
                license_plate=customer_plates[i],
                brand=random.choice(CAR_BRANDS),
                model=random.choice(["Sedan", "SUV", "Hatchback"]),
                year=random.randint(2015, 2024),
                fuel_type=random.choice(["Xăng", "Dầu", "Điện", "Hybrid"]),
            )
            db.add(v)
            vehicles.append(v)
        db.flush()

        # ── rescue_companies: 10 ──
        companies: list[RescueCompany] = []
        for i, (name, addr, lat, lng) in enumerate(COMPANIES_DATA[:ROWS_PER_TABLE], 1):
            owner = company_owners[i - 1]
            comp = RescueCompany(
                company_name=name,
                representative_name=owner.full_name,
                address=addr,
                hotline=f"1900-{1000 + i}",
                business_license=f"GPKD-2024-{i:04d}",
                operating_area="Hà Nội",
                description=f"Dịch vụ cứu hộ nhanh tại {addr}",
                latitude=lat,
                longitude=lng,
                service_radius_km=20.0 + (i % 5),
                status="active",
                is_verified=i % 4 != 0,
                owner_id=owner.id,
                rating_avg=round(3.5 + random.random() * 1.5, 1),
                rating_count=random.randint(5, 50),
            )
            db.add(comp)
            companies.append(comp)
        db.flush()

        # ── services: 10 (1 dịch vụ / công ty cho 10 công ty đầu) ──
        all_services: list[Service] = []
        for i, comp in enumerate(companies):
            s_name, price, dur = SERVICE_TEMPLATES[i % len(SERVICE_TEMPLATES)]
            svc = Service(
                company_id=comp.id,
                service_name=s_name,
                base_price=price,
                estimated_duration=dur,
                description=f"{s_name} — {comp.company_name}",
                is_active=True,
            )
            db.add(svc)
            all_services.append(svc)
        db.flush()

        # ── rescue_vehicles: 10 ──
        rescue_plates = _unique_plates(ROWS_PER_TABLE, "29C")
        all_rescue_vehicles: list[RescueVehicle] = []
        for i in range(ROWS_PER_TABLE):
            comp = companies[i % len(companies)]
            rveh = RescueVehicle(
                plate_number=rescue_plates[i],
                vehicle_type=RESCUE_VEHICLE_TYPES[i % len(RESCUE_VEHICLE_TYPES)],
                capacity=f"{3 + (i % 5)} tấn",
                status="available",
                company_id=comp.id,
                is_active=True,
            )
            db.add(rveh)
            all_rescue_vehicles.append(rveh)
        db.flush()

        # ── rescue_staff: 10 ──
        all_rescue_staff: list[RescueStaff] = []
        for i in range(ROWS_PER_TABLE):
            comp = companies[i % len(companies)]
            rstaff = RescueStaff(
                company_id=comp.id,
                full_name=f"Nhân viên cứu hộ {i + 1}",
                birth_date=date(1988 + (i % 12), (i % 12) + 1, (i % 27) + 1),
                phone=f"091000{i + 1:04d}",
                skill_level=STAFF_LEVELS[i % len(STAFF_LEVELS)],
                status=StaffStatus.AVAILABLE if i % 3 else StaffStatus.BUSY,
            )
            db.add(rstaff)
            all_rescue_staff.append(rstaff)
        db.flush()

        # ── rescue_requests + request_services: 10 ──
        print("INFO: Dang tao yeu cau cuu ho...")
        all_requests: list[RescueRequest] = []
        completed_requests: list[RescueRequest] = []
        for i in range(ROWS_PER_TABLE):
            customer = customers[i % len(customers)]
            vehicle = vehicles[i % len(vehicles)]
            company = companies[i % len(companies)]
            service = all_services[i % len(all_services)]
            status = REQUEST_STATUSES[i % len(REQUEST_STATUSES)]
            created_at = _utc_now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))

            has_company = status != RequestStatus.PENDING
            req = RescueRequest(
                user_id=customer.id,
                company_id=company.id if has_company else None,
                vehicle_id=vehicle.id,
                latitude=company.latitude + random.uniform(-0.03, 0.03),
                longitude=company.longitude + random.uniform(-0.03, 0.03),
                address_description=f"Vị trí gần {company.address}",
                incident_type=INCIDENT_TYPES[i % len(INCIDENT_TYPES)],
                description=f"Cần hỗ trợ: {service.service_name}",
                status=status.value,
                agreed_price=service.base_price,
                created_at=created_at,
                payment_status="paid" if status == RequestStatus.COMPLETED else "unpaid",
            )
            db.add(req)
            all_requests.append(req)
            db.flush()

            db.add(
                RequestService(
                    request_id=req.id,
                    service_id=service.id,
                    quantity=1,
                    unit_price=service.base_price,
                )
            )

            if status in ASSIGNMENT_STATUSES:
                c_staff = [s for s in all_rescue_staff if s.company_id == company.id]
                c_veh = [v for v in all_rescue_vehicles if v.company_id == company.id]
                if not c_staff:
                    c_staff = all_rescue_staff
                if not c_veh:
                    c_veh = all_rescue_vehicles
                db.add(
                    ServiceAssignment(
                        request_id=req.id,
                        staff_id=random.choice(c_staff).id,
                        rescue_vehicle_id=random.choice(c_veh).id,
                        assigned_time=created_at + timedelta(minutes=5),
                        notes="Phân công tự động từ seed",
                    )
                )

            if status == RequestStatus.COMPLETED:
                req.actual_arrival_time = created_at + timedelta(minutes=20)
                req.actual_completion_time = req.actual_arrival_time + timedelta(minutes=45)
                completed_requests.append(req)

        db.flush()

        # ── payments: 10 (moi yeu cau COMPLETED co 1 payment) ──
        payment_methods = ["cash", "momo", "vnpay", "card"]
        for i, req in enumerate(completed_requests[:ROWS_PER_TABLE]):
            db.add(
                Payment(
                    rescue_request_id=req.id,
                    amount=req.agreed_price or 0,
                    payment_method=payment_methods[i % len(payment_methods)],
                    status="success",
                    transaction_id=f"TXN-{req.id:06d}",
                    paid_at=(req.actual_completion_time or _utc_now()) + timedelta(minutes=5),
                )
            )

        # ── reviews: 10 ──
        for i, req in enumerate(completed_requests[:ROWS_PER_TABLE]):
            db.add(
                Review(
                    rescue_request_id=req.id,
                    user_id=req.user_id,
                    company_id=req.company_id,
                    rating=random.randint(3, 5),
                    comment=random.choice(
                        ["Dịch vụ tốt", "Nhanh chóng", "Nhân viên nhiệt tình", "Giá hợp lý"]
                    ),
                    is_approved=i % 5 != 0,
                )
            )

        # ── messages + notifications: 10 ──
        notif_types = ["SYSTEM", "REQUEST_UPDATE", "PAYMENT", "CHAT"]
        for i, req in enumerate(all_requests[:ROWS_PER_TABLE]):
            company = (
                next(c for c in companies if c.id == req.company_id)
                if req.company_id
                else companies[i % len(companies)]
            )
            db.add(
                Message(
                    request_id=req.id,
                    sender_id=req.user_id,
                    receiver_id=company.owner_id,
                    sender_type="Customer",
                    content=f"Tin nhắn mẫu #{i + 1}: cần hỗ trợ gấp",
                    is_read=i % 2 == 0,
                )
            )
            db.add(
                Notification(
                    receiver_id=req.user_id,
                    request_id=req.id,
                    title="Cập nhật yêu cầu",
                    content=f"Yêu cầu #{req.id} — trạng thái {req.status}",
                    notification_type=notif_types[i % len(notif_types)],
                    is_read=False,
                )
            )

        # ── community_posts + community_replies: 10 + 10 ──
        print("INFO: Dang tao du lieu cong dong...")
        posts: list[CommunityPost] = []
        for i in range(ROWS_PER_TABLE):
            post = CommunityPost(
                user_id=customers[i % len(customers)].id,
                title=COMMUNITY_TITLES[i],
                content=f"Nội dung bài viết mẫu #{i + 1} — thảo luận về sự cố xe.",
                incident_type=INCIDENT_TYPES[i % len(INCIDENT_TYPES)],
                is_closed=i % 7 == 0,
                is_approved=True,
            )
            db.add(post)
            posts.append(post)
        db.flush()

        for i in range(ROWS_PER_TABLE):
            db.add(
                CommunityReply(
                    post_id=posts[i % len(posts)].id,
                    user_id=customers[(i + 1) % len(customers)].id,
                    content=f"Trả lời mẫu #{i + 1}: bạn nên kiểm tra ắc quy và lốp.",
                    is_helpful=i % 3 == 0,
                    is_approved=True,
                )
            )

        # ── reports: 10 ──
        now = _utc_now()
        for i in range(ROWS_PER_TABLE):
            from_date = now - timedelta(days=30 * (i + 1))
            to_date = from_date + timedelta(days=28)
            db.add(
                Report(
                    admin_id=admin.id,
                    report_type=REPORT_TYPES[i],
                    from_date=from_date,
                    to_date=to_date,
                    filters=f'{{"company_id": null, "period": "month_{i + 1}"}}',
                    generated_at=to_date + timedelta(hours=1),
                )
            )

        db.commit()
        _print_summary()

    except Exception as e:
        db.rollback()
        print(f"ERROR: Loi khi tao du lieu: {e}")
        import traceback

        traceback.print_exc()
        raise
    finally:
        db.close()


def _print_summary() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        print("SUCCESS: Khoi tao du lieu mau thanh cong!")
        return
    import sqlite3

    conn = sqlite3.connect(_SQLITE_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    print("\nSUCCESS: So dong tung bang:")
    for (table,) in cur.fetchall():
        if table.startswith("sqlite_"):
            continue
        cur.execute(f"SELECT COUNT(*) FROM [{table}]")
        print(f"  {table}: {cur.fetchone()[0]}")
    conn.close()
    print("\nTai khoan: admin / Admin123! | customer1..10, company1..10 / Pass123!")


if __name__ == "__main__":
    seed_data()
