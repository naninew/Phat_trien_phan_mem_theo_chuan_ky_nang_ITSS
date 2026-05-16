"""
Script tạo dữ liệu mẫu (Seed Data) chuẩn từ đầu cho hệ thống Rescue System.
Chạy script này sẽ XÓA TOÀN BỘ dữ liệu cũ và tạo lại từ đầu các bảng kèm data mẫu hoàn chỉnh.
"""
import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
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
        # 1. Admin
        admin = User(
            username="admin",
            password_hash=hash_password("Admin123!"),
            full_name="Tổng Quản Trị",
            phone="0900000000",
            email="admin@rescue.vn",
            role=UserRole.ADMIN,
            status=AccountStatus.ACTIVE,
            address="Hà Nội"
        )
        db.add(admin)

        # 2. Customers
        customers = []
        for i in range(1, 6):
            c = User(
                username=f"customer{i}",
                password_hash=hash_password("Pass123!"),
                full_name=f"Khách Hàng {i}",
                phone=f"091200000{i}",
                email=f"customer{i}@example.com",
                role=UserRole.CUSTOMER,
                status=AccountStatus.ACTIVE,
                address=f"Quận {i}, Hà Nội"
            )
            db.add(c)
            customers.append(c)
        db.flush()

        # 3. Customer Vehicles
        vehicles = []
        for i, c in enumerate(customers):
            v = Vehicle(
                customer_id=c.id,
                license_plate=f"30A-{random.randint(10000,99999)}",
                brand=random.choice(["Toyota", "Honda", "Kia", "Mazda"]),
                model="Sedan",
                year=random.randint(2015, 2023),
                fuel_type=random.choice(["Xăng", "Dầu"])
            )
            db.add(v)
            vehicles.append(v)
        db.flush()

        # 4. Companies & Staff Users
        companies_data = [
            ("Cứu Hộ Thăng Long", "15 Đinh Tiên Hoàng", 21.0285, 105.8542),
            ("Tây Hồ Express", "88 Xuân Thủy", 21.0380, 105.7840),
            ("Hà Đông Car Service", "10 Trần Phú", 20.9721, 105.7761)
        ]

        companies = []
        all_services = []
        all_rescue_staff = []
        all_rescue_vehicles = []
        
        for i, (name, addr, lat, lng) in enumerate(companies_data, 1):
            staff_user = User(
                username=f"company{i}",
                password_hash=hash_password("Pass123!"),
                full_name=f"Quản Lý {name}",
                phone=f"098800000{i}",
                email=f"staff{i}@cuuho.vn",
                role=UserRole.COMPANY_STAFF,
                status=AccountStatus.ACTIVE,
                address=addr
            )
            db.add(staff_user)
            db.flush()
            
            comp = RescueCompany(
                company_name=name,
                address=addr,
                hotline=f"1900-1{i:03d}",
                business_license=f"GPKD-00{i}",
                operating_area="Hà Nội",
                description=f"Dịch vụ cứu hộ nhanh chóng tại {addr}",
                latitude=lat,
                longitude=lng,
                service_radius_km=20.0,
                status="active",
                is_verified=True,
                owner_id=staff_user.id,
                rating_avg=4.5,
                rating_count=20
            )
            db.add(comp)
            companies.append(comp)
            db.flush()

            # Services
            services_info = [
                ("Kéo xe ô tô", 500000, 60),
                ("Kích bình ắc quy", 150000, 20),
                ("Thay lốp dự phòng", 200000, 30)
            ]
            comp_services = []
            for s_name, price, dur in services_info:
                svc = Service(
                    company_id=comp.id,
                    service_name=s_name,
                    base_price=price,
                    estimated_duration=dur,
                    description=f"Dịch vụ {s_name} chuyên nghiệp"
                )
                db.add(svc)
                comp_services.append(svc)
                all_services.append(svc)
            
            # Rescue Vehicles
            for t in ["Xe cẩu", "Xe bệ trượt"]:
                rveh = RescueVehicle(
                    plate_number=f"29C-{random.randint(10000,99999)}",
                    vehicle_type=t,
                    status="available",
                    company_id=comp.id
                )
                db.add(rveh)
                all_rescue_vehicles.append(rveh)
                
            # Rescue Staff
            for j in range(2):
                rstaff = RescueStaff(
                    company_id=comp.id,
                    skill_level="Cao cấp" if j==0 else "Trung cấp",
                    status=StaffStatus.AVAILABLE
                )
                db.add(rstaff)
                all_rescue_staff.append(rstaff)

        db.flush()

        # 5. Rescue Requests & Workflow
        statuses = [
            RequestStatus.COMPLETED, RequestStatus.COMPLETED, RequestStatus.COMPLETED,
            RequestStatus.CANCELLED, RequestStatus.PENDING, 
            RequestStatus.ACCEPTED, RequestStatus.ASSIGNED, RequestStatus.ON_THE_WAY, RequestStatus.IN_PROGRESS
        ]
        
        print("INFO: Dang tao yeu cau cuu ho mau...")
        for i in range(20):
            customer = random.choice(customers)
            vehicle = next(v for v in vehicles if v.customer_id == customer.id)
            company = random.choice(companies)
            comp_services = [s for s in all_services if s.company_id == company.id]
            service = random.choice(comp_services)
            status = random.choice(statuses)
            
            created_at = datetime.utcnow() - timedelta(days=random.randint(0, 10), hours=random.randint(0, 23))
            
            req = RescueRequest(
                user_id=customer.id,
                company_id=company.id if status != RequestStatus.PENDING else None,
                vehicle_id=vehicle.id,
                latitude=company.latitude + random.uniform(-0.05, 0.05),
                longitude=company.longitude + random.uniform(-0.05, 0.05),
                address_description=f"Vị trí gần {company.address}",
                incident_type="Thủng lốp" if "lốp" in service.service_name else "Chết máy",
                description=f"Cần hỗ trợ: {service.service_name}",
                status=status.value,
                agreed_price=service.base_price,
                created_at=created_at,
                payment_status="paid" if status == RequestStatus.COMPLETED else "unpaid"
            )
            db.add(req)
            db.flush()
            
            # RequestService
            rs = RequestService(
                request_id=req.id,
                service_id=service.id,
                quantity=1,
                unit_price=service.base_price
            )
            db.add(rs)

            # Workflow timestamps & assignments
            if status in [RequestStatus.ASSIGNED, RequestStatus.ON_THE_WAY, RequestStatus.IN_PROGRESS, RequestStatus.COMPLETED]:
                req.company_id = company.id
                c_staff = [s for s in all_rescue_staff if s.company_id == company.id]
                c_veh = [v for v in all_rescue_vehicles if v.company_id == company.id]
                
                assign = ServiceAssignment(
                    request_id=req.id,
                    staff_id=random.choice(c_staff).id,
                    rescue_vehicle_id=random.choice(c_veh).id,
                    assigned_time=created_at + timedelta(minutes=5)
                )
                db.add(assign)
                
            if status == RequestStatus.COMPLETED:
                req.actual_arrival_time = created_at + timedelta(minutes=20)
                req.actual_completion_time = req.actual_arrival_time + timedelta(minutes=45)
                
                pay = Payment(
                    rescue_request_id=req.id,
                    amount=req.agreed_price,
                    payment_method="cash",
                    status="success",
                    paid_at=req.actual_completion_time + timedelta(minutes=5)
                )
                db.add(pay)
                
                if random.random() > 0.5:
                    rev = Review(
                        rescue_request_id=req.id,
                        user_id=customer.id,
                        company_id=company.id,
                        rating=random.randint(4, 5),
                        comment="Dịch vụ tốt"
                    )
                    db.add(rev)

            # Chat & Notification
            if status != RequestStatus.PENDING:
                msg = Message(
                    request_id=req.id,
                    sender_id=customer.id,
                    receiver_id=company.owner_id,
                    sender_type="Customer",
                    content="Xin chào, tôi cần hỗ trợ gấp"
                )
                db.add(msg)
                
                notif = Notification(
                    receiver_id=customer.id,
                    request_id=req.id,
                    title="Cập nhật yêu cầu",
                    content=f"Yêu cầu của bạn đã chuyển sang trạng thái {status}"
                )
                db.add(notif)

        # 6. Community
        print("INFO: Dang tao du lieu cong dong...")
        post = CommunityPost(
            user_id=customers[0].id,
            title="Xe KIA Morning không nổ máy",
            content="Mọi người cho em hỏi xe em đề không nổ, đèn vẫn sáng thì bị sao ạ?",
            incident_type="Chết máy",
            is_closed=False
        )
        db.add(post)
        db.flush()
        
        reply = CommunityReply(
            post_id=post.id,
            user_id=customers[1].id,
            content="Khả năng là hết bình ắc quy, bác mượn ai cái bình kích thử xem.",
            is_helpful=True
        )
        db.add(reply)

        db.commit()
        print("SUCCESS: Khoi tao du lieu mau thanh cong!")

    except Exception as e:
        db.rollback()
        print(f"ERROR: Loi khi tao du lieu: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
