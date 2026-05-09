"""
Script tạo dữ liệu mẫu (Seed Data) chuẩn từ đầu cho hệ thống Rescue System.
Chạy script này sẽ XÓA TOÀN BỘ dữ liệu cũ và tạo lại từ đầu các bảng kèm data mẫu hoàn chỉnh.
Data bao gồm:
- Admin
- Customers (Khách hàng)
- Companies (Công ty cứu hộ)
- Services (Dịch vụ: Ô tô & Xe máy)
- Vehicles (Phương tiện cứu hộ)
- Requests (Yêu cầu cứu hộ kèm Chat, Thanh toán, Đánh giá)
"""
import sys
import os
import random
from datetime import datetime, timedelta

# Thêm thư mục backend vào path để có thể import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.company import RescueCompany
from app.models.service import Service
from app.models.vehicle import RescueVehicle
from app.models.request import RescueRequest, RequestStatus
from app.models.payment import Payment
from app.models.chat import ChatMessage
from app.models.review import Review
from app.services.auth_svc import hash_password

def reset_db():
    print("INFO: Dang xoa du lieu cu...")
    Base.metadata.drop_all(bind=engine)
    print("INFO: Dang tao lai cau truc co so du lieu...")
    Base.metadata.create_all(bind=engine)

def seed_data():
    print("START: Bat dau tao du lieu mau chuan tu dau...")
    reset_db()
    db = SessionLocal()

    try:
        # ─── 1. Admin ────────────────────────────────────────────────────────────
        admin = User(
            username="admin",
            password_hash=hash_password("Admin123!"),
            full_name="Tổng Quản Trị",
            phone="0900000000",
            email="admin@rescue.vn",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)

        # ─── 2. Customers ────────────────────────────────────────────────────────
        customers = []
        for i in range(1, 6):
            c = User(
                username=f"customer{i}",
                password_hash=hash_password("Pass123!"),
                full_name=f"Khách Hàng {i}",
                phone=f"091200000{i}",
                email=f"customer{i}@example.com",
                role=UserRole.CUSTOMER,
                is_active=True,
            )
            db.add(c)
            customers.append(c)

        db.flush()

        # ─── 3. Companies & Staff ───────────────────────────────────────────────
        companies_data = [
            ("Cứu Hộ Ô Tô Thăng Long", "15 Đinh Tiên Hoàng, Hoàn Kiếm", 21.0285, 105.8542),
            ("Tây Hồ Express (Auto & Bike)", "88 Xuân Thủy, Cầu Giấy", 21.0380, 105.7840),
            ("Hà Đông Car Service", "10 Trần Phú, Hà Đông", 20.9721, 105.7761),
            ("Cứu Hộ 24/7 Hoàng Mai", "123 Giải Phóng, Hoàng Mai", 20.9855, 105.8405),
            ("Bắc Từ Liêm Moto Care", "45 Phạm Văn Đồng, Bắc Từ Liêm", 21.0655, 105.7725),
        ]

        companies = []
        for i, (name, addr, lat, lng) in enumerate(companies_data, 1):
            staff = User(
                username=f"company{i}",
                password_hash=hash_password("Pass123!"),
                full_name=f"Quản Lý {name}",
                phone=f"098800000{i}",
                email=f"staff{i}@cuuho.vn",
                role=UserRole.COMPANY_STAFF,
                is_active=True,
            )
            db.add(staff)
            db.flush()
            
            comp = RescueCompany(
                company_name=name,
                address=addr,
                hotline=f"1900-1{i:03d}",
                license_number=f"GPKD-00{i}",
                description=f"Dịch vụ cứu hộ nhanh chóng, chuyên nghiệp tại khu vực {addr}",
                latitude=lat,
                longitude=lng,
                service_radius_km=random.uniform(10.0, 30.0),
                status="active",
                is_verified=True,
                owner_id=staff.id,
                rating_avg=round(random.uniform(4.0, 5.0), 1),
                rating_count=random.randint(10, 100)
            )
            db.add(comp)
            companies.append(comp)

        db.flush()

        # ─── 4. Services ─────────────────────────────────────────────────────────
        # Phân chia rõ ràng Ô Tô và Xe Máy
        car_services = [
            ("Kéo xe ô tô", 500000, "Sử dụng xe sàn trượt an toàn, chuyên nghiệp"),
            ("Kích bình ắc quy ô tô", 150000, "Kích nổ ắc quy tận nơi trong vòng 15 phút"),
            ("Thay lốp/vá lốp ô tô", 200000, "Thay lốp dự phòng, vá lốp ô tô tận nơi"),
            ("Cứu hộ ô tô sa lầy", 800000, "Cứu hộ xe rơi xuống mương, sa lầy"),
            ("Mở khóa cửa xe ô tô", 300000, "Mở khóa chuyên nghiệp không làm xước xe")
        ]

        bike_services = [
            ("Vận chuyển xe máy", 150000, "Vận chuyển xe máy về tận cửa hàng/gara"),
            ("Vá săm/thay lốp xe máy", 50000, "Vá xe lưu động, thay săm lốp tận nơi"),
            ("Tiếp nhiên liệu/Hết xăng", 80000, "Mang xăng khẩn cấp đến tận nơi"),
            ("Sửa chữa lưu động xe máy", 100000, "Bảo dưỡng, sửa chữa nhẹ tại chỗ")
        ]

        all_services = []
        for i, comp in enumerate(companies):
            # Tuỳ theo tên công ty mà gán dịch vụ (Moto Care chỉ có xe máy, Car Service chỉ ô tô, các công ty khác có cả 2)
            c_svcs = []
            if "Moto" in comp.company_name:
                c_svcs = bike_services
            elif "Car" in comp.company_name:
                c_svcs = car_services
            else:
                # Cung cấp toàn bộ dịch vụ để đảm bảo độ phủ cao trong kết quả tìm kiếm
                c_svcs = car_services + bike_services
            
            for s_name, price, desc in c_svcs:
                svc = Service(
                    company_id=comp.id,
                    service_name=s_name,
                    base_price=price,
                    description=desc,
                    is_active=True
                )
                db.add(svc)
                all_services.append(svc)

        db.flush()

        # ─── 5. Vehicles ─────────────────────────────────────────────────────────
        for comp in companies:
            if "Moto" in comp.company_name:
                types = ["Xe bán tải hỗ trợ", "Xe máy dịch vụ"]
            elif "Car" in comp.company_name:
                types = ["Xe kéo cẩu", "Xe bệ trượt"]
            else:
                types = ["Xe cẩu", "Xe bán tải", "Xe bệ trượt"]
            
            for t in types:
                veh = RescueVehicle(
                    license_plate=f"29A-{random.randint(10000,99999)}",
                    vehicle_type=t,
                    status="available",
                    company_id=comp.id
                )
                db.add(veh)

        db.commit()

        # ─── 6. Rescue Requests & Workflow Data ─────────────────────────────────
        statuses = [
            RequestStatus.COMPLETED, RequestStatus.COMPLETED, RequestStatus.COMPLETED,
            RequestStatus.COMPLETED, RequestStatus.CANCELLED, RequestStatus.PENDING, 
            RequestStatus.ACCEPTED, RequestStatus.EN_ROUTE, RequestStatus.ON_SITE
        ]
        
        print("INFO: Dang tao 50 yeu cau cuu ho mau (kem Chat, Payment, Review)...")
        for _ in range(50):
            customer = random.choice(customers)
            company = random.choice(companies)
            comp_services = [s for s in all_services if s.company_id == company.id]
            if not comp_services:
                continue
            service = random.choice(comp_services)
            status = random.choice(statuses)
            
            created_at = datetime.utcnow() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23), minutes=random.randint(0, 59))
            
            req = RescueRequest(
                user_id=customer.id,
                company_id=company.id,
                service_id=service.id,
                latitude=company.latitude + random.uniform(-0.05, 0.05),
                longitude=company.longitude + random.uniform(-0.05, 0.05),
                address_description=f"Địa điểm bất kỳ quanh {company.company_name}",
                car_issue_detail=f"Sự cố: {service.service_name}",
                status=status.value,
                total_cost=service.base_price + random.randint(20000, 100000),
                created_at=created_at,
                payment_status="paid" if status == RequestStatus.COMPLETED else "unpaid",
                payment_method=random.choice(["cash", "banking", "momo"])
            )
            
            # Workflow timestamps
            if status in [RequestStatus.ACCEPTED, RequestStatus.EN_ROUTE, RequestStatus.ON_SITE, RequestStatus.COMPLETED]:
                req.accepted_at = created_at + timedelta(minutes=random.randint(1, 5))
            if status in [RequestStatus.ON_SITE, RequestStatus.COMPLETED]:
                req.actual_arrival_time = req.accepted_at + timedelta(minutes=random.randint(10, 30))
            if status == RequestStatus.COMPLETED:
                req.actual_completion_time = req.actual_arrival_time + timedelta(minutes=random.randint(15, 60))
            
            db.add(req)
            db.flush()

            # Chat
            msg1 = ChatMessage(
                rescue_request_id=req.id,
                sender_id=customer.id,
                message="Tôi đang ở lề đường, cần hỗ trợ gấp.",
                created_at=created_at + timedelta(minutes=1)
            )
            msg2 = ChatMessage(
                rescue_request_id=req.id,
                sender_id=company.owner_id,
                message="Chúng tôi đã nhận yêu cầu. Đội ngũ sẽ có mặt trong 15 phút.",
                created_at=created_at + timedelta(minutes=3)
            )
            db.add_all([msg1, msg2])

            # Payment & Review (Only if completed)
            if status == RequestStatus.COMPLETED:
                pay = Payment(
                    rescue_request_id=req.id,
                    amount=req.total_cost,
                    payment_method=req.payment_method,
                    status="success",
                    paid_at=req.actual_completion_time + timedelta(minutes=random.randint(1, 5))
                )
                db.add(pay)
                
                # Random chance to leave a review
                if random.random() > 0.3:
                    rev = Review(
                        rescue_request_id=req.id,
                        user_id=customer.id,
                        company_id=company.id,
                        rating=random.randint(3, 5),
                        comment=random.choice(["Dịch vụ rất tốt", "Hỗ trợ nhanh chóng", "Thái độ chuyên nghiệp", "Hơi lâu nhưng chấp nhận được"]),
                        created_at=req.actual_completion_time + timedelta(hours=random.randint(1, 24))
                    )
                    db.add(rev)

        db.commit()
        print("SUCCESS: Khoi tao du lieu thanh cong!")

    except Exception as e:
        db.rollback()
        print(f"ERROR: Loi khi tao du lieu: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
