"""
Rescue routes – đầy đủ endpoints cho customer, company staff và admin.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.rescue import (
    RescueRequestCreate,
    RescueRequestUpdate,
    ServiceCreate,
    VehicleCreate,
)
from app.services import rescue_svc, auth_svc
from app.utils.response import success_response
from app.models.company import RescueCompany
from app.models.service import Service


router = APIRouter(prefix="/rescue", tags=["Rescue Services"])


# ──────────────────────────────────────────────────────────────────────────────
# Services (loại dịch vụ)
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/services")
def list_services(db: Session = Depends(get_db)):
    """Lấy danh sách các tên dịch vụ độc nhất (để hiển thị dropdown)."""
    services = db.query(Service.service_name).filter(Service.is_active == True).distinct().all()
    return success_response(
        data=[s.service_name for s in services],
        message="Success",
    )


@router.post("/services")
def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Tạo dịch vụ mới cho công ty (chỉ company_staff)."""
    if current_user.get("role") not in ("company_staff", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ company staff mới có thể thêm dịch vụ")

    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    svc = rescue_svc.create_service(db, company.id, service_data)
    return success_response(
        data={"id": svc.id, "service_name": svc.service_name},
        message="Tạo dịch vụ thành công",
    )


@router.delete("/services/{service_id}")
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    ok = rescue_svc.delete_service(db, service_id, company.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy dịch vụ")
    return success_response(data={}, message="Đã xóa dịch vụ")


# ──────────────────────────────────────────────────────────────────────────────
# Nearby companies
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/companies/nearby")
def find_nearby_companies(
    latitude: float,
    longitude: float,
    service_name: str,
    radius_km: float = 50.0,
    db: Session = Depends(get_db),
):
    """Tìm công ty cứu hộ gần vị trí người dùng, có dịch vụ khớp tên."""
    results = rescue_svc.find_nearby_companies(db, latitude, longitude, service_name, radius_km)

    data = []
    for company, distance, services in results:
        # Tìm dịch vụ cụ thể có tên khớp để lấy giá
        matched = next((s for s in services if s.service_name.lower() == service_name.lower()), services[0] if services else None)
        base_price = matched.base_price if matched else 0
        data.append({
            "id": company.id,
            "company_name": company.company_name,
            "address": company.address,
            "hotline": company.hotline,
            "rating_avg": company.rating_avg,
            "rating_count": company.rating_count,
            "distance_km": round(distance, 2),
            "estimated_price": rescue_svc.estimate_price(base_price, distance),
            "eta_minutes": rescue_svc.estimate_eta(distance),
            "service_radius_km": company.service_radius_km,
            "latitude": company.latitude,
            "longitude": company.longitude,
            "services": [
                {"id": s.id, "service_name": s.service_name, "base_price": s.base_price}
                for s in services
            ],
        })

    return success_response(data=data, message=f"Tìm thấy {len(data)} công ty")


# ──────────────────────────────────────────────────────────────────────────────
# Rescue Requests – Customer
# ──────────────────────────────────────────────────────────────────────────────
@router.post("/requests")
def create_rescue_request(
    request_data: RescueRequestCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Khách hàng gửi yêu cầu cứu hộ."""
    req = rescue_svc.create_rescue_request(db, current_user["user_id"], request_data)

    from app.models.service import Service
    service_obj = db.query(Service).filter(Service.id == req.service_id).first()

    return success_response(
        data={
            "id": req.id,
            "status": req.status,
            "service_id": req.service_id,
            "service_name": service_obj.service_name if service_obj else "N/A",
            "company_id": req.company_id,
            "address_description": req.address_description,
            "created_at": req.created_at.isoformat(),
        },
        message="Đã gửi yêu cầu cứu hộ thành công",
    )


@router.get("/requests")
def get_my_requests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Lấy danh sách requests của customer hiện tại."""
    from app.models.service import Service
    from app.models.company import RescueCompany

    requests = rescue_svc.get_user_requests(db, current_user["user_id"])
    data = []
    for r in requests:
        svc = db.query(Service).filter(Service.id == r.service_id).first()
        company = db.query(RescueCompany).filter(RescueCompany.id == r.company_id).first() if r.company_id else None
        data.append({
            "id": r.id,
            "status": r.status,
            "service_id": r.service_id,
            "service_name": svc.service_name if svc else "N/A",
            "company_id": r.company_id,
            "company_name": company.company_name if company else None,
            "company_hotline": company.hotline if company else None,
            "address_description": r.address_description,
            "car_issue_detail": r.car_issue_detail,
            "eta_minutes": r.eta_minutes,
            "total_cost": r.total_cost,
            "payment_method": r.payment_method,
            "rating": r.rating,
            "feedback": r.feedback,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
        })
    return success_response(data=data, message="Success")


@router.get("/requests/{request_id}")
def get_request_detail(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Chi tiết một request."""
    from app.models.service import Service
    from app.models.company import RescueCompany
    from app.models.vehicle import RescueVehicle
    from app.models.review import Review

    req = rescue_svc.get_request_by_id(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")

    # Kiểm tra quyền: customer chỉ xem request của mình, company_staff xem request của công ty
    uid = current_user["user_id"]
    role = current_user.get("role", "customer")
    if role == "customer" and req.user_id != uid:
        raise HTTPException(status_code=403, detail="Không có quyền xem yêu cầu này")
    if role == "company_staff":
        company = rescue_svc.get_company_by_owner_id(db, uid)
        if not company or req.company_id != company.id:
            raise HTTPException(status_code=403, detail="Không có quyền xem yêu cầu này")

    svc = db.query(Service).filter(Service.id == req.service_id).first()
    company = db.query(RescueCompany).filter(RescueCompany.id == req.company_id).first() if req.company_id else None
    vehicle = db.query(RescueVehicle).filter(RescueVehicle.id == req.vehicle_id).first() if req.vehicle_id else None
    review = db.query(Review).filter(Review.rescue_request_id == request_id).first()

    return success_response(
        data={
            "id": req.id,
            "user_id": req.user_id,
            "status": req.status,
            "service_id": req.service_id,
            "service_name": svc.service_name if svc else "N/A",
            "company_id": req.company_id,
            "company_name": company.company_name if company else None,
            "company_hotline": company.hotline if company else None,
            "company_latitude": company.latitude if company else None,
            "company_longitude": company.longitude if company else None,
            "company_radius_km": company.service_radius_km if company else None,
            "vehicle_id": req.vehicle_id,
            "vehicle_plate": vehicle.license_plate if vehicle else None,
            "vehicle_type": vehicle.vehicle_type if vehicle else None,
            "latitude": req.latitude,
            "longitude": req.longitude,
            "address_description": req.address_description,
            "car_issue_detail": req.car_issue_detail,
            "images": req.images or [],
            "eta_minutes": req.eta_minutes,
            "total_cost": req.total_cost,
            "payment_method": req.payment_method,
            "payment_status": req.payment_status,
            "actual_arrival_time": req.actual_arrival_time.isoformat() if req.actual_arrival_time else None,
            "actual_completion_time": req.actual_completion_time.isoformat() if req.actual_completion_time else None,
            "has_review": review is not None,
            "rating": review.rating if review else None,
            "feedback": review.comment if review else None,
            "created_at": req.created_at.isoformat(),
            "updated_at": req.updated_at.isoformat(),
        },
        message="Success",
    )


@router.post("/requests/{request_id}/cancel")
def cancel_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Hủy yêu cầu (chỉ customer, khi còn pending/accepted)."""
    req = rescue_svc.cancel_request(db, request_id, current_user["user_id"])
    if not req:
        raise HTTPException(
            status_code=400,
            detail="Không thể hủy yêu cầu – đã được xử lý hoặc không tồn tại",
        )
    return success_response(data={"id": req.id, "status": req.status}, message="Đã hủy yêu cầu")


@router.post("/requests/{request_id}/review")
def submit_review(
    request_id: int,
    rating: int,
    comment: str = "",
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Gửi đánh giá sau khi dịch vụ hoàn thành."""
    if not (1 <= rating <= 5):
        raise HTTPException(status_code=400, detail="Rating phải từ 1 đến 5")

    review = rescue_svc.submit_review(db, request_id, current_user["user_id"], rating, comment or None)
    if not review:
        raise HTTPException(
            status_code=400,
            detail="Không thể đánh giá – yêu cầu chưa hoàn thành hoặc không hợp lệ",
        )
    return success_response(
        data={"review_id": review.id, "rating": review.rating},
        message="Cảm ơn đánh giá của bạn!",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Queue – Company staff
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/queue")
def get_company_queue(
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Lấy queue requests của công ty hiện tại."""
    if current_user.get("role") not in ("company_staff", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ company staff mới có quyền xem queue")

    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    from app.models.service import Service
    from app.models.user import User
    from app.models.vehicle import RescueVehicle

    requests = rescue_svc.get_company_queue(db, company.id, status_filter)
    data = []
    for r in requests:
        customer = db.query(User).filter(User.id == r.user_id).first()
        svc = db.query(Service).filter(Service.id == r.service_id).first()
        vehicle = db.query(RescueVehicle).filter(RescueVehicle.id == r.vehicle_id).first() if r.vehicle_id else None
        data.append({
            "id": r.id,
            "status": r.status,
            "customer_name": customer.full_name if customer else "N/A",
            "customer_phone": customer.phone if customer else "N/A",
            "service_name": svc.service_name if svc else "N/A",
            "address_description": r.address_description,
            "car_issue_detail": r.car_issue_detail,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "eta_minutes": r.eta_minutes,
            "total_cost": r.total_cost,
            "vehicle_plate": vehicle.license_plate if vehicle else None,
            "payment_method": r.payment_method,
            "created_at": r.created_at.isoformat(),
        })
    return success_response(data=data, message="Success")


@router.post("/requests/{request_id}/accept")
def accept_request(
    request_id: int,
    eta_minutes: int,
    vehicle_id: Optional[int] = None,
    total_cost: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Công ty tiếp nhận yêu cầu cứu hộ."""
    if current_user.get("role") not in ("company_staff", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ company staff mới có quyền tiếp nhận")

    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    req = rescue_svc.accept_request(db, request_id, company.id, eta_minutes, vehicle_id)
    if not req:
        raise HTTPException(status_code=400, detail="Không thể tiếp nhận yêu cầu")

    if total_cost:
        req.total_cost = total_cost
        db.commit()
        db.refresh(req)

    return success_response(
        data={"id": req.id, "status": req.status, "eta_minutes": req.eta_minutes},
        message="Đã tiếp nhận yêu cầu",
    )


@router.put("/requests/{request_id}/status")
def update_request_status(
    request_id: int,
    status_update: RescueRequestUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Cập nhật trạng thái yêu cầu (company staff)."""
    if current_user.get("role") not in ("company_staff", "admin"):
        raise HTTPException(status_code=403, detail="Không có quyền cập nhật trạng thái")

    req = rescue_svc.update_request_status(
        db,
        request_id,
        status_update.status,
        status_update.vehicle_id,
        status_update.eta_minutes,
    )
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")

    return success_response(
        data={"id": req.id, "status": req.status},
        message="Cập nhật trạng thái thành công",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Vehicles – Company staff
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/vehicles")
def get_my_vehicles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Lấy danh sách xe của công ty hiện tại."""
    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    vehicles = rescue_svc.get_company_vehicles(db, company.id)
    return success_response(
        data=[
            {
                "id": v.id,
                "license_plate": v.license_plate,
                "vehicle_type": v.vehicle_type,
                "capacity": v.capacity,
                "status": v.status,
            }
            for v in vehicles
        ],
        message="Success",
    )


@router.post("/vehicles")
def add_vehicle(
    vehicle_data: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    vehicle = rescue_svc.create_vehicle(db, company.id, vehicle_data)
    return success_response(
        data={"id": vehicle.id, "license_plate": vehicle.license_plate},
        message="Đã thêm phương tiện",
    )


@router.put("/vehicles/{vehicle_id}/status")
def update_vehicle_status(
    vehicle_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    v = rescue_svc.update_vehicle_status(db, vehicle_id, new_status, company.id)
    if not v:
        raise HTTPException(status_code=400, detail="Không thể cập nhật trạng thái xe")
    return success_response(data={"id": v.id, "status": v.status}, message="Đã cập nhật trạng thái xe")


@router.delete("/vehicles/{vehicle_id}")
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    ok = rescue_svc.delete_vehicle(db, vehicle_id, company.id)
    if not ok:
        raise HTTPException(status_code=400, detail="Không thể xóa xe (đang làm nhiệm vụ hoặc không tồn tại)")
    return success_response(data={}, message="Đã xóa phương tiện")


# ──────────────────────────────────────────────────────────────────────────────
# Company vehicles by ID (for admin/customer view)
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/companies")
def list_all_companies(db: Session = Depends(get_db)):
    """Lấy danh sách tất cả các công ty cứu hộ đang active."""
    companies = db.query(RescueCompany).filter(RescueCompany.status == "active").all()
    return success_response(
        data=[
            {
                "id": c.id,
                "company_name": c.company_name,
                "address": c.address,
                "hotline": c.hotline,
                "rating_avg": c.rating_avg,
                "rating_count": c.rating_count,
                "service_radius_km": c.service_radius_km,
                "latitude": c.latitude,
                "longitude": c.longitude,
            }
            for c in companies
        ],
        message="Success"
    )


@router.get("/companies/{company_id}/full-details")
def get_company_full_details(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """
    Lấy thông tin chi tiết công ty, bao gồm các đánh giá 
    và lịch sử dịch vụ của chính khách hàng này với công ty đó.
    """
    from app.models.review import Review
    from app.models.request import RescueRequest
    from app.models.user import User
    from app.models.service import Service

    company = db.query(RescueCompany).filter(RescueCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    # Reviews with Service Info
    reviews_data = []
    reviews = db.query(Review, User, Service).join(
        User, Review.user_id == User.id
    ).join(
        RescueRequest, Review.rescue_request_id == RescueRequest.id
    ).join(
        Service, RescueRequest.service_id == Service.id
    ).filter(Review.company_id == company_id).order_by(Review.created_at.desc()).all()

    for rev, u, svc in reviews:
        reviews_data.append({
            "customer_name": u.full_name,
            "rating": rev.rating,
            "comment": rev.comment,
            "service_name": svc.service_name,
            "created_at": rev.created_at.isoformat()
        })
    
    # My history with this company
    user_id = current_user["user_id"]
    my_history = db.query(RescueRequest, Service).join(Service, RescueRequest.service_id == Service.id).filter(
        RescueRequest.company_id == company_id,
        RescueRequest.user_id == user_id
    ).order_by(RescueRequest.created_at.desc()).all()

    return success_response(
        data={
            "id": company.id,
            "company_name": company.company_name,
            "address": company.address,
            "hotline": company.hotline,
            "description": company.description,
            "rating_avg": company.rating_avg,
            "rating_count": company.rating_count,
            "latitude": company.latitude,
            "longitude": company.longitude,
            "service_radius_km": company.service_radius_km,
            "reviews": reviews_data,
            "my_history": [
                {
                    "id": req.id,
                    "service_name": svc.service_name,
                    "total_cost": req.total_cost,
                    "created_at": req.created_at.isoformat(),
                    "status": req.status
                }
                for req, svc in my_history
            ]
        },
        message="Success"
    )
