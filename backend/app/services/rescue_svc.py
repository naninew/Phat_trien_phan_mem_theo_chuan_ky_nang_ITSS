"""
Rescue service business logic.
Handles: nearby search (Haversine), request lifecycle, vehicles, services, reviews.
"""
from __future__ import annotations

import math
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.company import RescueCompany
from app.models.request import RescueRequest, RequestStatus, RequestService, ServiceAssignment
from app.models.review import Review
from app.models.service import Service
from app.models.vehicle import RescueVehicle, Vehicle
from app.models.staff import RescueStaff, StaffStatus
from app.schemas.rescue import (
    RescueRequestCreate, ServiceCreate, 
    RescueVehicleCreate, CustomerVehicleCreate, CustomerVehicleUpdate,
    RescueStaffCreate, RescueStaffUpdate, ServiceAssignmentCreate, PaymentCreate,
    RescueCompanyCreate
)

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────
EARTH_RADIUS_KM = 6371.0
PRICE_PER_KM = 10_000.0      # VND per km
AVG_SPEED_KMH = 40.0         # km/h for ETA estimate


# ──────────────────────────────────────────────────────────────────────────────
# Utility
# ──────────────────────────────────────────────────────────────────────────────
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km between two GPS points."""
    rl1, rl2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rl1) * math.cos(rl2) * math.sin(dlon / 2) ** 2
    return EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def estimate_price(base_price: float, distance_km: float) -> float:
    return round(base_price + distance_km * PRICE_PER_KM, 0)


def estimate_eta(distance_km: float) -> int:
    return max(5, int((distance_km / AVG_SPEED_KMH) * 60))


# ──────────────────────────────────────────────────────────────────────────────
# Company queries
# ──────────────────────────────────────────────────────────────────────────────
def get_company_by_id(db: Session, company_id: int) -> Optional[RescueCompany]:
    return db.query(RescueCompany).filter(RescueCompany.id == company_id).first()


def get_company_by_owner_id(db: Session, owner_id: int) -> Optional[RescueCompany]:
    return db.query(RescueCompany).filter(RescueCompany.owner_id == owner_id).first()


def get_all_companies(db: Session, status_filter: Optional[str] = None) -> List[RescueCompany]:
    q = db.query(RescueCompany)
    if status_filter and status_filter != "all":
        q = q.filter(RescueCompany.status == status_filter)
    return q.order_by(RescueCompany.created_at.desc()).all()


def create_company_profile(db: Session, owner_id: int, data: RescueCompanyCreate) -> RescueCompany:
    """Tạo profile công ty mới cho owner."""
    company = RescueCompany(
        owner_id=owner_id,
        company_name=data.company_name,
        address=data.address,
        hotline=data.hotline,
        business_license=data.business_license or f"LIC-{owner_id}",
        operating_area=data.operating_area,
        description=data.description,
        latitude=data.latitude,
        longitude=data.longitude,
        service_radius_km=data.service_radius_km or 20.0,
        status="pending",
        is_verified=False
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def find_nearby_companies(
    db: Session,
    latitude: float,
    longitude: float,
    service_ids: List[int],
    radius_km: float = 50.0,
) -> List[Tuple[RescueCompany, float, List[Service]]]:
    """
    Tìm các công ty cứu hộ gần vị trí người dùng có cung cấp tất cả các dịch vụ yêu cầu.
    """
    companies = db.query(RescueCompany).filter(
        RescueCompany.status == "active",
        RescueCompany.is_verified == True,
        RescueCompany.latitude.isnot(None),
        RescueCompany.longitude.isnot(None),
    ).all()

    results = []
    for company in companies:
        distance = haversine(latitude, longitude, company.latitude, company.longitude)
        if distance > radius_km:
            continue

        # Lấy tất cả services của công ty
        company_services = db.query(Service).filter(
            Service.company_id == company.id,
            Service.is_active == True,
        ).all()
        company_service_ids = {s.id for s in company_services}

        # Nếu công ty có đủ các services được yêu cầu
        if all(sid in company_service_ids for sid in service_ids):
            matched_services = [s for s in company_services if s.id in service_ids]
            results.append((company, distance, matched_services))

    results.sort(key=lambda x: x[1])
    return results


# ──────────────────────────────────────────────────────────────────────────────
# Service (loại dịch vụ) queries
# ──────────────────────────────────────────────────────────────────────────────
def get_all_services(db: Session) -> List[Service]:
    """Lấy tất cả dịch vụ đang active (để hiển thị dropdown)."""
    return db.query(Service).filter(Service.is_active == True).all()


def get_services_by_company(db: Session, company_id: int) -> List[Service]:
    return db.query(Service).filter(Service.company_id == company_id).all()


def create_service(db: Session, company_id: int, service_data: ServiceCreate) -> Service:
    svc = Service(
        service_name=service_data.service_name,
        base_price=service_data.base_price,
        estimated_duration=service_data.estimated_duration,
        description=service_data.description,
        company_id=company_id,
        is_active=True,
    )
    db.add(svc)
    db.commit()
    db.refresh(svc)
    return svc

def update_service(db: Session, company_id: int, service_id: int, data: dict) -> Optional[Service]:
    svc = db.query(Service).filter(Service.id == service_id, Service.company_id == company_id).first()
    if not svc:
        return None
    if "service_name" in data: svc.service_name = data["service_name"]
    if "base_price" in data: svc.base_price = data["base_price"]
    if "estimated_duration" in data: svc.estimated_duration = data["estimated_duration"]
    if "description" in data: svc.description = data["description"]
    db.commit()
    db.refresh(svc)
    return svc


def delete_service(db: Session, service_id: int, company_id: int) -> bool:
    svc = db.query(Service).filter(Service.id == service_id, Service.company_id == company_id).first()
    if not svc:
        return False
    db.delete(svc)
    db.commit()
    return True


# ──────────────────────────────────────────────────────────────────────────────
# Rescue Request lifecycle
# ──────────────────────────────────────────────────────────────────────────────
def create_rescue_request(
    db: Session,
    user_id: int,
    request_data: RescueRequestCreate,
) -> RescueRequest:
    req = RescueRequest(
        #service_id=request_data.service_ids[0],
        user_id=user_id,
        vehicle_id=request_data.vehicle_id,
        company_id=request_data.company_id,
        latitude=request_data.latitude,
        longitude=request_data.longitude,
        address_description=request_data.address_description,
        incident_type = request_data.incident_type,
        description=request_data.description,
        images=request_data.images or [],
        status=RequestStatus.PENDING,
        payment_method=request_data.payment_method or "cash",
        #agreed_price = request_data.agreed_price,
    )
    db.add(req)
    db.flush() # Để lấy id cho req
    print("===== REQUEST =====")
    print(req)
    #Tạo các RequestService
    services = db.query(Service).filter(Service.id.in_(request_data.service_ids)).all()
    for s in services:
        rs = RequestService(
            request_id=req.id,
            service_id=s.id,
            quantity=1,
            unit_price=s.base_price
        )
        db.add(rs)

    db.commit()
    db.refresh(req)
    return req


def get_request_by_id(db: Session, request_id: int) -> Optional[RescueRequest]:
    return db.query(RescueRequest).filter(RescueRequest.id == request_id).first()


def get_user_requests(db: Session, user_id: int) -> List[RescueRequest]:
    return (
        db.query(RescueRequest)
        .filter(RescueRequest.user_id == user_id)
        .order_by(RescueRequest.created_at.desc())
        .all()
    )


def get_company_queue(
    db: Session,
    company_id: int,
    status_filter: Optional[str] = None,
) -> List[RescueRequest]:
    """Lấy danh sách requests của một công ty (queue)."""
    q = db.query(RescueRequest).filter(RescueRequest.company_id == company_id)
    if status_filter and status_filter != "all":
        q = q.filter(RescueRequest.status == status_filter)
    return q.order_by(RescueRequest.created_at.desc()).all()


def get_pending_requests(db: Session) -> List[RescueRequest]:
    """Lấy tất cả requests đang chờ tiếp nhận (chưa có company)."""
    return (
        db.query(RescueRequest)
        .filter(RescueRequest.status == RequestStatus.PENDING)
        .order_by(RescueRequest.created_at.asc())
        .all()
    )


def accept_request(
    db: Session,
    request_id: int,
    company_id: int,
    eta_minutes: int,
) -> Optional[RescueRequest]:
    """Công ty tiếp nhận request: gán company, ETA, chuyển trạng thái ACCEPTED."""
    req = get_request_by_id(db, request_id)
    if not req or req.status != RequestStatus.PENDING:
        return None

    req.company_id = company_id
    req.eta_minutes = eta_minutes
    req.status = RequestStatus.ACCEPTED

    db.commit()
    db.refresh(req)
    return req

def reject_request(
    db: Session,
    request_id: int,
    company_id: int,
) -> Optional[RescueRequest]:
    """Công ty từ chối request."""
    req = get_request_by_id(db, request_id)
    if not req or req.status != RequestStatus.PENDING:
        return None
    req.status = RequestStatus.REJECTED
    req.company_id = None
    db.commit()
    db.refresh(req)
    return req

def assign_request(
    db: Session,
    request_id: int,
    company_id: int,
    assignment_data: ServiceAssignmentCreate
) -> Optional[RescueRequest]:
    """Phân công nhân viên và xe cho request."""
    req = get_request_by_id(db, request_id)
    if not req or req.company_id != company_id or req.status != RequestStatus.ACCEPTED:
        return None
    
    assignment = ServiceAssignment(
        request_id=req.id,
        staff_id=assignment_data.staff_id,
        rescue_vehicle_id=assignment_data.rescue_vehicle_id,
        notes=assignment_data.notes
    )
    db.add(assignment)
    req.status = RequestStatus.ASSIGNED
    
    _set_vehicle_status(db, assignment_data.rescue_vehicle_id, "on_mission")
    
    staff = db.query(RescueStaff).filter(RescueStaff.id == assignment_data.staff_id).first()
    if staff:
        staff.status = StaffStatus.BUSY
        
    db.commit()
    db.refresh(req)
    return req


def update_request_status(
    db: Session,
    request_id: int,
    status: str,
    eta_minutes: Optional[int] = None,
    agreed_price: Optional[float] = None,
) -> Optional[RescueRequest]:
    req = get_request_by_id(db, request_id)
    if not req:
        return None

    req.status = status

    if eta_minutes is not None:
        req.eta_minutes = eta_minutes
    if agreed_price is not None:
        req.agreed_price = agreed_price

    if status == RequestStatus.ON_THE_WAY:
        # Tùy chọn logic thêm khi đang trên đường
        pass
    elif status == RequestStatus.IN_PROGRESS:
        req.actual_arrival_time = datetime.utcnow()
    elif status == RequestStatus.COMPLETED:
        req.actual_completion_time = datetime.utcnow()
        # Giải phóng xe và nhân viên
        if req.assignment:
            _set_vehicle_status(db, req.assignment.rescue_vehicle_id, "available")
            staff = db.query(RescueStaff).filter(RescueStaff.id == req.assignment.staff_id).first()
            if staff:
                staff.status = StaffStatus.AVAILABLE

    db.commit()
    db.refresh(req)
    return req


def cancel_request(db: Session, request_id: int, user_id: int) -> Optional[RescueRequest]:
    """Hủy request – chỉ cho phép khi status là pending hoặc accepted."""
    req = get_request_by_id(db, request_id)
    if not req or req.user_id != user_id:
        return None
    if req.status not in (RequestStatus.PENDING, RequestStatus.ACCEPTED):
        return None

    req.status = RequestStatus.CANCELLED
    if req.assignment:
        _set_vehicle_status(db, req.assignment.rescue_vehicle_id, "available")
        staff = db.query(RescueStaff).filter(RescueStaff.id == req.assignment.staff_id).first()
        if staff:
            staff.status = StaffStatus.AVAILABLE
    db.commit()
    db.refresh(req)
    return req


# ──────────────────────────────────────────────────────────────────────────────
# Review
# ──────────────────────────────────────────────────────────────────────────────
def submit_review(
    db: Session,
    request_id: int,
    user_id: int,
    rating: int,
    comment: Optional[str] = None,
) -> Optional[Review]:
    """Gửi đánh giá sau khi hoàn thành dịch vụ."""
    req = get_request_by_id(db, request_id)
    if not req or req.user_id != user_id or req.status != RequestStatus.COMPLETED:
        return None
    if not req.company_id:
        return None

    # Kiểm tra đã review chưa
    existing = db.query(Review).filter(Review.rescue_request_id == request_id).first()
    if existing:
        return existing

    review = Review(
        rescue_request_id=request_id,
        user_id=user_id,
        company_id=req.company_id,
        rating=rating,
        comment=comment,
    )
    db.add(review)

    # Cập nhật rating_avg của công ty
    company = get_company_by_id(db, req.company_id)
    if company:
        company.rating_count = (company.rating_count or 0) + 1
        # Tính lại trung bình
        all_ratings = db.query(func.avg(Review.rating)).filter(
            Review.company_id == req.company_id
        ).scalar()
        company.rating_avg = round(float(all_ratings or rating), 2)

    db.commit()
    db.refresh(review)
    return review

# ──────────────────────────────────────────────────────────────────────────────
# Payment
# ──────────────────────────────────────────────────────────────────────────────
def process_payment(
    db: Session,
    request_id: int,
    user_id: int,
    payment_data: PaymentCreate
) -> Optional[RescueRequest]:
    from app.models.payment import Payment
    req = get_request_by_id(db, request_id)
    if not req or req.user_id != user_id or req.status != RequestStatus.COMPLETED:
        return None
    
    payment = Payment(
        rescue_request_id=request_id,
        amount=payment_data.amount,
        payment_method=payment_data.payment_method,
        transaction_id=payment_data.transaction_id,
        status="success"
    )
    db.add(payment)
    
    req.payment_status = "paid"
    req.payment_method = payment_data.payment_method
    
    db.commit()
    db.refresh(req)
    return req


# ──────────────────────────────────────────────────────────────────────────────
# Vehicle
# ──────────────────────────────────────────────────────────────────────────────
def get_company_vehicles(db: Session, company_id: int) -> List[RescueVehicle]:
    return db.query(RescueVehicle).filter(RescueVehicle.company_id == company_id).all()


def create_vehicle(db: Session, company_id: int, vehicle_data: RescueVehicleCreate) -> RescueVehicle:
    v = RescueVehicle(
        plate_number=vehicle_data.plate_number,
        vehicle_type=vehicle_data.vehicle_type,
        capacity=vehicle_data.capacity,
        company_id=company_id,
        status="available",
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def update_vehicle_status(db: Session, vehicle_id: int, status: str, company_id: int) -> Optional[RescueVehicle]:
    v = db.query(RescueVehicle).filter(
        RescueVehicle.id == vehicle_id,
        RescueVehicle.company_id == company_id,
    ).first()
    if not v:
        return None
    if v.status == "on_mission" and status != "on_mission":
        # Không cho phép đổi trạng thái xe đang làm nhiệm vụ trừ khi là hệ thống
        pass
    v.status = status
    db.commit()
    db.refresh(v)
    return v


def delete_vehicle(db: Session, vehicle_id: int, company_id: int) -> bool:
    v = db.query(RescueVehicle).filter(
        RescueVehicle.id == vehicle_id,
        RescueVehicle.company_id == company_id,
    ).first()
    if not v or v.status == "on_mission":
        return False
    db.delete(v)
    db.commit()
    return True


def _set_vehicle_status(db: Session, vehicle_id: int, status: str) -> None:
    """Internal helper – không kiểm tra ownership."""
    v = db.query(RescueVehicle).filter(RescueVehicle.id == vehicle_id).first()
    if v:
        v.status = status
        db.commit()

# ──────────────────────────────────────────────────────────────────────────────
# Customer Vehicle
# ──────────────────────────────────────────────────────────────────────────────
def get_customer_vehicles(db: Session, customer_id: int) -> List[Vehicle]:
    return db.query(Vehicle).filter(Vehicle.customer_id == customer_id).all()

def create_customer_vehicle(db: Session, customer_id: int, vehicle_data: CustomerVehicleCreate) -> Vehicle:
    v = Vehicle(
        customer_id=customer_id,
        license_plate=vehicle_data.license_plate,
        brand=vehicle_data.brand,
        model=vehicle_data.model,
        year=vehicle_data.year,
        fuel_type=vehicle_data.fuel_type
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v

def update_customer_vehicle(db: Session, customer_id: int, vehicle_id: int, vehicle_data: CustomerVehicleUpdate) -> Optional[Vehicle]:
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id, Vehicle.customer_id == customer_id).first()
    if not v:
        return None
    if vehicle_data.brand is not None: v.brand = vehicle_data.brand
    if vehicle_data.model is not None: v.model = vehicle_data.model
    if vehicle_data.year is not None: v.year = vehicle_data.year
    if vehicle_data.fuel_type is not None: v.fuel_type = vehicle_data.fuel_type
    db.commit()
    db.refresh(v)
    return v

def delete_customer_vehicle(db: Session, customer_id: int, vehicle_id: int) -> bool:
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id, Vehicle.customer_id == customer_id).first()
    if not v:
        return False
    db.delete(v)
    db.commit()
    return True

# ──────────────────────────────────────────────────────────────────────────────
# Rescue Staff
# ──────────────────────────────────────────────────────────────────────────────
def get_company_staff(db: Session, company_id: int) -> List[RescueStaff]:
    return db.query(RescueStaff).filter(RescueStaff.company_id == company_id).all()

def create_staff(db: Session, company_id: int, staff_data: RescueStaffCreate) -> RescueStaff:
    staff = RescueStaff(
        company_id=company_id,
        skill_level=staff_data.skill_level,
        status=StaffStatus.AVAILABLE
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff

def update_staff(db: Session, company_id: int, staff_id: int, staff_data: RescueStaffUpdate) -> Optional[RescueStaff]:
    staff = db.query(RescueStaff).filter(RescueStaff.id == staff_id, RescueStaff.company_id == company_id).first()
    if not staff:
        return None
    if staff_data.skill_level is not None: staff.skill_level = staff_data.skill_level
    if staff_data.status is not None: staff.status = StaffStatus(staff_data.status)
    db.commit()
    db.refresh(staff)
    return staff

def delete_staff(db: Session, company_id: int, staff_id: int) -> bool:
    staff = db.query(RescueStaff).filter(RescueStaff.id == staff_id, RescueStaff.company_id == company_id).first()
    if not staff:
        return False
    db.delete(staff)
    db.commit()
    return True


# ──────────────────────────────────────────────────────────────────────────────
# Admin stats
# ──────────────────────────────────────────────────────────────────────────────
def get_admin_stats(db: Session) -> dict:
    from app.models.user import User
    total_users = db.query(func.count(User.id)).scalar()
    active_companies = db.query(func.count(RescueCompany.id)).filter(
        RescueCompany.status == "active"
    ).scalar()
    total_requests = db.query(func.count(RescueRequest.id)).scalar()
    pending_requests = db.query(func.count(RescueRequest.id)).filter(
        RescueRequest.status == RequestStatus.PENDING
    ).scalar()
    completed_requests = db.query(func.count(RescueRequest.id)).filter(
        RescueRequest.status == RequestStatus.COMPLETED
    ).scalar()

    return {
        "total_users": total_users,
        "active_companies": active_companies,
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "completed_requests": completed_requests,
    }
