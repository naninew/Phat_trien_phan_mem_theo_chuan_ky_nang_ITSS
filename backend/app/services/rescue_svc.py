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
from app.models.request import RescueRequest, RequestStatus
from app.models.review import Review
from app.models.service import Service
from app.models.vehicle import RescueVehicle
from app.schemas.rescue import RescueRequestCreate, ServiceCreate, VehicleCreate

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


def find_nearby_companies(
    db: Session,
    latitude: float,
    longitude: float,
    service_name: str,
    radius_km: float = 50.0,
) -> List[Tuple[RescueCompany, float, List[Service]]]:
    """
    Tìm các công ty cứu hộ gần vị trí người dùng có dịch vụ phù hợp (khớp theo tên).
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
        services = db.query(Service).filter(
            Service.company_id == company.id,
            Service.is_active == True,
        ).all()

        # Kiểm tra xem công ty có cung cấp dịch vụ có tên khớp không
        if not any(s.service_name.lower() == service_name.lower() for s in services):
            continue

        results.append((company, distance, services))

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
        description=service_data.description,
        company_id=company_id,
        is_active=True,
    )
    db.add(svc)
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
        user_id=user_id,
        service_id=request_data.service_id,
        company_id=request_data.company_id,
        latitude=request_data.latitude,
        longitude=request_data.longitude,
        address_description=request_data.address_description,
        car_issue_detail=request_data.car_issue_detail,
        images=request_data.images or [],
        status=RequestStatus.PENDING,
        payment_method=request_data.payment_method or "cash",
    )
    db.add(req)
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
    vehicle_id: Optional[int] = None,
) -> Optional[RescueRequest]:
    """Công ty tiếp nhận request: gán company, ETA, vehicle, chuyển trạng thái."""
    req = get_request_by_id(db, request_id)
    if not req or req.status != RequestStatus.PENDING:
        return None

    req.company_id = company_id
    req.eta_minutes = eta_minutes
    req.status = RequestStatus.ACCEPTED
    if vehicle_id:
        req.vehicle_id = vehicle_id
        # Đánh dấu xe đang làm nhiệm vụ
        _set_vehicle_status(db, vehicle_id, "on_mission")

    db.commit()
    db.refresh(req)
    return req


def update_request_status(
    db: Session,
    request_id: int,
    status: str,
    vehicle_id: Optional[int] = None,
    eta_minutes: Optional[int] = None,
    total_cost: Optional[float] = None,
) -> Optional[RescueRequest]:
    req = get_request_by_id(db, request_id)
    if not req:
        return None

    req.status = status

    if vehicle_id is not None:
        req.vehicle_id = vehicle_id
    if eta_minutes is not None:
        req.eta_minutes = eta_minutes
    if total_cost is not None:
        req.total_cost = total_cost

    if status == RequestStatus.ON_SITE:
        req.actual_arrival_time = datetime.utcnow()
    elif status == RequestStatus.COMPLETED:
        req.actual_completion_time = datetime.utcnow()
        # Giải phóng xe
        if req.vehicle_id:
            _set_vehicle_status(db, req.vehicle_id, "available")

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
    if req.vehicle_id:
        _set_vehicle_status(db, req.vehicle_id, "available")
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
# Vehicle
# ──────────────────────────────────────────────────────────────────────────────
def get_company_vehicles(db: Session, company_id: int) -> List[RescueVehicle]:
    return db.query(RescueVehicle).filter(RescueVehicle.company_id == company_id).all()


def create_vehicle(db: Session, company_id: int, vehicle_data: VehicleCreate) -> RescueVehicle:
    v = RescueVehicle(
        license_plate=vehicle_data.license_plate,
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
