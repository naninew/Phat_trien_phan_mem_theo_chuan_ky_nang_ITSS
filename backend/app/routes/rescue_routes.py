"""
Rescue routes – đầy đủ endpoints cho customer, company staff và admin.
"""
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status, Query
# pyrefly: ignore [missing-import]
from sqlalchemy import func
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from app.database import get_db
from app.schemas.rescue import (
    RescueRequestCreate,
    RescueRequestUpdate,
    RescueServiceCreate,
    RescueServiceUpdate,
    RescueVehicleCreate,
    RescueVehicleUpdate,
    RescueStaffCreate,
    RescueStaffUpdate,
    ServiceAssignmentCreate,
    PaymentCreate,
    CustomerVehicleCreate,
    CustomerVehicleUpdate,
    CustomerVehicleResponse,
    RescueCompanyCreate,
)
from app.services import rescue_svc, auth_svc, chat_svc
from app.utils.response import success_response
from app.models.company import RescueCompany
from app.models.service import Service
from app.models.request import RequestService


router = APIRouter(prefix="/rescue", tags=["Rescue Services"])


STATUS_NOTIFICATION_LABELS = {
    "ACCEPTED": "đã được tiếp nhận",
    "ASSIGNED": "đã được phân công đội cứu hộ",
    "ON_THE_WAY": "đang được đội cứu hộ di chuyển tới",
    "IN_PROGRESS": "đang được xử lý tại hiện trường",
    "COMPLETED": "đã hoàn thành",
    "REJECTED": "đã bị từ chối",
    "CANCELLED": "đã bị hủy",
}


def _review_meta(req, review) -> dict:
    deadline = req.actual_completion_time + timedelta(days=7) if req.actual_completion_time else None
    return {
        "review_deadline": deadline.isoformat() if deadline else None,
        "can_review": (
            req.status == "COMPLETED"
            and deadline is not None
            and datetime.utcnow() <= deadline
        ),
    }


def _create_notification(
    db: Session,
    receiver_id: int,
    title: str,
    content: str,
    request_id: Optional[int] = None,
    request_status: Optional[str] = None,
):
    notif = chat_svc.create_notification(db, receiver_id, title, content, request_id)
    payload = {
        "type": "notification",
        "notification": {
            "id": notif.id,
            "receiver_id": notif.receiver_id,
            "request_id": notif.request_id,
            "title": notif.title,
            "content": notif.content,
            "is_read": notif.is_read,
            "sent_time": notif.sent_time.isoformat() if notif.sent_time else None,
            "event": "request_status_update" if request_status else "notification",
            "request_status": request_status,
        },
    }
    try:
        from app.routes.ws_routes import notification_manager
        notification_manager.send_to_user_nowait(receiver_id, payload)
    except Exception:
        pass
    return notif


# ──────────────────────────────────────────────────────────────────────────────
# Services (loại dịch vụ)
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/services")
def list_services(db: Session = Depends(get_db)):
    """Lấy danh sách các tên dịch vụ độc nhất (để hiển thị dropdown)."""

    service_names = [
        row[0]
        for row in db.query(func.trim(Service.service_name))
        .filter(Service.is_active == True)
        .distinct()
        .order_by(func.trim(Service.service_name).asc())
        .all()
        if row[0]
    ]
    return success_response(
        data=[
            {
                "id": name,
                "service_name": name,
            }
            for name in service_names
        ],
        message="Success",
    )


@router.get("/company/services")
def list_company_services(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Lấy danh sách dịch vụ của công ty."""
    if current_user.get("role") not in ("company_staff", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ company staff mới có thể xem dịch vụ của công ty")
    
    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy profile công ty")
        
    services = rescue_svc.get_services_by_company(db, company.id)
    service_counts = dict(
        db.query(
            RequestService.service_id,
            func.coalesce(func.sum(RequestService.quantity), 0),
        )
        .join(Service, RequestService.service_id == Service.id)
        .filter(Service.company_id == company.id)
        .group_by(RequestService.service_id)
        .all()
    )
    return success_response(
        data=[
            {
                "service_id": s.id,
                "company_id": s.company_id,
                "service_name": s.service_name,
                "description": s.description,
                "base_price": s.base_price,
                "estimated_duration": s.estimated_duration,
                "is_active": s.is_active,
                "usage_count": int(service_counts.get(s.id, 0)),
                "request_count": int(service_counts.get(s.id, 0)),
            }
            for s in services
        ],
        message="Success"
    )

@router.get("/company/services/{service_id}")
def get_company_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    if current_user.get("role") not in ("company_staff", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ company staff mới có quyền này")
    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy profile công ty")
        
    svc = rescue_svc.get_service_by_id(db, service_id, company.id)
    if not svc:
        raise HTTPException(status_code=404, detail="Không tìm thấy dịch vụ")
        
    return success_response(
        data={
            "service_id": svc.id,
            "company_id": svc.company_id,
            "service_name": svc.service_name,
            "description": svc.description,
            "base_price": svc.base_price,
            "estimated_duration": svc.estimated_duration,
            "is_active": svc.is_active
        },
        message="Success"
    )

@router.post("/company/services")
def create_service(
    service_data: RescueServiceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Tạo dịch vụ mới cho công ty."""
    if current_user.get("role") not in ("company_staff", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ company staff mới có thể thêm dịch vụ")

    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    svc = rescue_svc.create_service(db, company.id, service_data)
    return success_response(
        data={"service_id": svc.id, "service_name": svc.service_name},
        message="Tạo dịch vụ thành công",
    )

@router.put("/company/services/{service_id}")
def update_service(
    service_id: int,
    service_data: RescueServiceUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    if current_user.get("role") not in ("company_staff", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ company staff mới có thể sửa dịch vụ")
    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")
        
    svc = rescue_svc.update_service(db, company.id, service_id, service_data)
    if not svc:
        raise HTTPException(status_code=404, detail="Không tìm thấy dịch vụ")
    return success_response(data={"service_id": svc.id, "service_name": svc.service_name}, message="Cập nhật thành công")

@router.delete("/company/services/{service_id}")
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

@router.patch("/company/services/{service_id}/activate")
def activate_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    svc = rescue_svc.set_service_active_status(db, service_id, company.id, True)
    if not svc:
        raise HTTPException(status_code=404, detail="Không tìm thấy dịch vụ")
    return success_response(data={"service_id": svc.id, "is_active": svc.is_active}, message="Đã kích hoạt dịch vụ")

@router.patch("/company/services/{service_id}/deactivate")
def deactivate_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    svc = rescue_svc.set_service_active_status(db, service_id, company.id, False)
    if not svc:
        raise HTTPException(status_code=404, detail="Không tìm thấy dịch vụ")
    return success_response(data={"service_id": svc.id, "is_active": svc.is_active}, message="Đã vô hiệu hóa dịch vụ")


@router.post("/company/profile")
def create_company_profile(
    profile_data: RescueCompanyCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Tạo profile công ty (chỉ cho role company_staff)."""
    if current_user.get("role") != "company_staff":
        raise HTTPException(status_code=403, detail="Chỉ tài khoản công ty mới có thể tạo profile")
    
    # Check if already has company
    existing = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if existing:
        raise HTTPException(status_code=400, detail="Tài khoản đã có profile công ty")
    
    company = rescue_svc.create_company_profile(db, current_user["user_id"], profile_data)
    return success_response(
        data={
            "id": company.id,
            "company_name": company.company_name,
            "status": company.status
        },
        message="Đã tạo profile công ty, vui lòng chờ Admin xác minh"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Nearby companies
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/companies/nearby")
def find_nearby_companies(
    latitude: float,
    longitude: float,
    service_id: Optional[int] = Query(None, description="Single service ID required"),
    service_ids: Optional[List[int]] = Query(None, description="List of service IDs required"),
    service_names: Optional[List[str]] = Query(None, description="List of service names required"),
    radius_km: float = 50.0,
    db: Session = Depends(get_db),
):
    """Tìm công ty cứu hộ gần vị trí người dùng, cung cấp đủ các dịch vụ yêu cầu."""
    requested_service_ids = list(service_ids or [])
    if service_id is not None:
        requested_service_ids.append(service_id)

    if not requested_service_ids and not service_names:
        raise HTTPException(status_code=400, detail="Vui lòng chọn ít nhất một dịch vụ")

    results = rescue_svc.find_nearby_companies(
        db,
        latitude,
        longitude,
        service_ids=requested_service_ids,
        service_names=service_names or [],
        radius_km=radius_km,
    )

    data = []
    for company, distance, services in results:
        base_price_total = sum(s.base_price for s in services)
        data.append({
            "id": company.id,
            "company_name": company.company_name,
            "address": company.address,
            "hotline": company.hotline,
            "rating_avg": company.rating_avg,
            "rating_count": company.rating_count,
            "distance_km": round(distance, 2),
            "estimated_price": rescue_svc.estimate_price(base_price_total, distance),
            "eta_minutes": rescue_svc.estimate_eta(distance),
            "service_radius_km": company.service_radius_km,
            "latitude": company.latitude,
            "longitude": company.longitude,
            "services": [
                {"id": s.id, "service_name": (s.service_name or "").strip(), "base_price": s.base_price}
                for s in services
            ],
        })
    data.sort(key=lambda item: item["estimated_price"])

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
    if req.company and req.company.owner_id:
        _create_notification(
            db,
            req.company.owner_id,
            "Yêu cầu cứu hộ mới",
            f"Khách hàng vừa gửi yêu cầu #{req.id} tại {req.address_description}.",
            req.id,
        )

    return success_response(
        data={
            "id": req.id,
            "status": req.status,
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

    user_id = current_user["user_id"]
    
    try:
        requests = rescue_svc.get_user_requests(db, user_id)
        
        data = []

        for r in requests:
            # Company đã được eager load, không cần query lại
            company = r.company

            services_data = []

            for rs in r.request_services:
                if rs.service:
                    services_data.append({
                        "id": rs.service.id,
                        "service_name": rs.service.service_name,
                        "price": rs.unit_price
                    })

            review = r.review
            review_meta = _review_meta(r, review)

            item = {
                "id": r.id,
                "status": r.status,
                "services": services_data,
                "company_id": r.company_id,
                "company_name": company.company_name if company else None,
                "company_hotline": company.hotline if company else None,
                "address_description": r.address_description,
                "incident_type": r.incident_type,
                "description": r.description,
                "eta_minutes": r.eta_minutes,
                "agreed_price": r.agreed_price,
                "invoice_description": r.invoice_description,
                "payment_method": r.payment_method,
                "payment_status": r.payment_status,
                "has_review": review is not None,
                "can_review": review_meta["can_review"],
                "review_deadline": review_meta["review_deadline"],
                "rating": review.rating if review else r.rating,
                "feedback": review.comment if review else r.feedback,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat(),
            }

            data.append(item)

        print(f"[get_my_requests] User {user_id}: {len(data)} requests")
        return success_response(
            data=data,
            message="Success"
        )
    except Exception as e:
        print(f"[get_my_requests] ERROR: {e}")
        raise

@router.get("/requests/{request_id}")
def get_request_detail(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Chi tiết một request."""
    from app.models.service import Service
    from app.models.company import RescueCompany
    from app.models.vehicle import RescueVehicle, Vehicle
    from app.models.review import Review
    from app.models.staff import RescueStaff

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

    # Company đã được eager load
    company = req.company
    
    # Xe của customer
    customer_vehicle = db.query(Vehicle).filter(Vehicle.id == req.vehicle_id).first() if req.vehicle_id else None
    
    review = req.review
    review_meta = _review_meta(req, review)
    
    services_data = []
    for rs in req.request_services:
        if rs.service:
            services_data.append({"id": rs.service.id, "service_name": rs.service.service_name, "price": rs.unit_price})

    assignment_data = None
    if req.assignment:
        staff = db.query(RescueStaff).filter(RescueStaff.id == req.assignment.staff_id).first()
        r_vehicle = db.query(RescueVehicle).filter(RescueVehicle.id == req.assignment.rescue_vehicle_id).first()
        staff_name = f"Nhân viên #{staff.id} - {staff.skill_level}" if staff else None
        assignment_data = {
            "staff_id": staff.id if staff else None,
            "staff_name": staff_name,
            "rescue_vehicle_id": r_vehicle.id if r_vehicle else None,
            "rescue_vehicle_plate": r_vehicle.plate_number if r_vehicle else None,
            "assigned_time": req.assignment.assigned_time.isoformat() if req.assignment.assigned_time else None
        }

    return success_response(
        data={
            "id": req.id,
            "user_id": req.user_id,
            "status": req.status,
            "services": services_data,
            "company_id": req.company_id,
            "company_name": company.company_name if company else None,
            "company_hotline": company.hotline if company else None,
            "company_latitude": company.latitude if company else None,
            "company_longitude": company.longitude if company else None,
            "company_radius_km": company.service_radius_km if company else None,
            "customer_vehicle_id": req.vehicle_id,
            "customer_vehicle_plate": customer_vehicle.license_plate if customer_vehicle else None,
            "latitude": req.latitude,
            "longitude": req.longitude,
            "address_description": req.address_description,
            "incident_type": req.incident_type,
            "description": req.description,
            "images": req.images or [],
            "eta_minutes": req.eta_minutes,
            "agreed_price": req.agreed_price,
            "invoice_description": req.invoice_description,
            "payment_method": req.payment_method,
            "payment_status": req.payment_status,
            "actual_arrival_time": req.actual_arrival_time.isoformat() if req.actual_arrival_time else None,
            "actual_completion_time": req.actual_completion_time.isoformat() if req.actual_completion_time else None,
            "has_review": review is not None,
            "can_review": review_meta["can_review"],
            "review_deadline": review_meta["review_deadline"],
            "rating": review.rating if review else None,
            "feedback": review.comment if review else None,
            "assignment": assignment_data,
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
    if comment and len(comment) > 500:
        raise HTTPException(status_code=400, detail="Nhận xét tối đa 500 ký tự")

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
        services_data = []
        for rs in r.request_services:
            if rs.service:
                services_data.append({"id": rs.service.id, "service_name": rs.service.service_name, "price": rs.unit_price})

        data.append({
            "id": r.id,
            "status": r.status,
            "customer_name": customer.full_name if customer else "N/A",
            "customer_phone": customer.phone if customer else "N/A",
            "services": services_data,
            "address_description": r.address_description,
            "incident_type": r.incident_type,
            "description": r.description,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "eta_minutes": r.eta_minutes,
            "agreed_price": r.agreed_price,
            "payment_method": r.payment_method,
            "payment_status": r.payment_status,
            "created_at": r.created_at.isoformat(),
        })
    return success_response(data=data, message="Success")


@router.put("/requests/{request_id}/accept")
def accept_request(
    request_id: int,
    eta_minutes: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Công ty tiếp nhận yêu cầu cứu hộ."""
    if current_user.get("role") not in ("company_staff", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ company staff mới có quyền tiếp nhận")

    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    req = rescue_svc.accept_request(db, request_id, company.id, eta_minutes)
    if not req:
        raise HTTPException(status_code=400, detail="Không thể tiếp nhận yêu cầu")
    _create_notification(
        db,
        req.user_id,
        "Yêu cầu đã được tiếp nhận",
        f"{company.company_name} đã tiếp nhận yêu cầu #{req.id}. ETA khoảng {req.eta_minutes or eta_minutes} phút.",
        req.id,
        req.status,
    )

    return success_response(
        data={"id": req.id, "status": req.status, "eta_minutes": req.eta_minutes},
        message="Đã tiếp nhận yêu cầu",
    )

@router.put("/requests/{request_id}/reject")
async def reject_request(
    request_id: int,
    reason: str = Query(..., description="Lý do từ chối"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Công ty từ chối yêu cầu cứu hộ."""
    if current_user.get("role") not in ("company_staff", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ company staff mới có quyền từ chối")

    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    req = rescue_svc.reject_request(db, request_id, company.id)
    if not req:
        raise HTTPException(status_code=400, detail="Không thể từ chối yêu cầu")
    
    # Send reason as a chat message
    from app.schemas.chat import MessageCreate
    from app.services import chat_svc
    msg_data = MessageCreate(
        request_id=request_id,
        receiver_id=req.user_id,
        sender_type="company",
        content=f"Chúng tôi rất tiếc phải từ chối yêu cầu của bạn. Lý do: {reason}"
    )
    try:
        msg = chat_svc.send_message(db, current_user["user_id"], msg_data)
        from app.routes.chat_routes import _broadcast_ws_message
        await _broadcast_ws_message(request_id, msg)
    except Exception as e:
        print(f"Failed to send reject chat message: {e}")

    _create_notification(
        db,
        req.user_id,
        "Yêu cầu đã bị từ chối",
        f"{company.company_name} đã từ chối yêu cầu #{req.id}. Bạn có thể chọn đơn vị cứu hộ khác.",
        req.id,
        req.status,
    )

    return success_response(
        data={"id": req.id, "status": req.status},
        message="Đã từ chối yêu cầu",
    )

@router.post("/requests/{request_id}/assign")
def assign_request(
    request_id: int,
    assignment_data: ServiceAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Công ty phân công nhân viên và xe cho yêu cầu."""
    if current_user.get("role") not in ("company_staff", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ company staff mới có quyền phân công")

    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    req = rescue_svc.assign_request(db, request_id, company.id, assignment_data)
    if not req:
        raise HTTPException(status_code=400, detail="Không thể phân công (yêu cầu chưa được accept hoặc không hợp lệ)")
    _create_notification(
        db,
        req.user_id,
        "Đã phân công đội cứu hộ",
        f"{company.company_name} đã phân công nhân sự và phương tiện cho yêu cầu #{req.id}.",
        req.id,
        req.status,
    )

    return success_response(
        data={"id": req.id, "status": req.status},
        message="Đã phân công thành công",
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
        status_update.eta_minutes,
        status_update.agreed_price,
        status_update.invoice_description,
    )
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")
    if status_update.status:
        label = STATUS_NOTIFICATION_LABELS.get(status_update.status, f"đã chuyển sang {status_update.status}")
        _create_notification(
            db,
            req.user_id,
            "Cập nhật trạng thái cứu hộ",
            f"Yêu cầu #{req.id} {label}.",
            req.id,
            req.status,
        )

    return success_response(
        data={"id": req.id, "status": req.status},
        message="Cập nhật trạng thái thành công",
    )


@router.post("/requests/{request_id}/complete")
def complete_request(
    request_id: int,
    update_data: RescueRequestUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Công ty hoàn thành yêu cầu cứu hộ."""
    if current_user.get("role") not in ("company_staff", "admin"):
        raise HTTPException(status_code=403, detail="Không có quyền hoàn thành yêu cầu")

    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    req = rescue_svc.update_request_status(
        db, request_id, "COMPLETED", agreed_price=update_data.agreed_price, invoice_description=update_data.invoice_description
    )
    if not req:
        raise HTTPException(status_code=400, detail="Không thể hoàn thành yêu cầu")
    _create_notification(
        db,
        req.user_id,
        "Yêu cầu đã hoàn thành",
        f"Yêu cầu #{req.id} đã hoàn thành. Bạn có thể đánh giá dịch vụ.",
        req.id,
        req.status,
    )

    return success_response(
        data={"id": req.id, "status": req.status, "agreed_price": req.agreed_price, "invoice_description": req.invoice_description},
        message="Yêu cầu đã hoàn thành",
    )


@router.post("/requests/{request_id}/payment")
def process_payment(
    request_id: int,
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Khách hàng thanh toán sau khi dịch vụ hoàn thành."""
    req = rescue_svc.process_payment(db, request_id, current_user["user_id"], payment_data)
    if not req:
        raise HTTPException(status_code=400, detail="Không thể thanh toán (chưa hoàn thành hoặc không hợp lệ)")
    if req.company and req.company.owner_id:
        _create_notification(
            db,
            req.company.owner_id,
            "Khách hàng đã thanh toán",
            f"Yêu cầu #{req.id} đã được thanh toán.",
            req.id,
            "PAYMENT_PAID",
        )
    
    return success_response(
        data={"id": req.id, "payment_status": req.payment_status},
        message="Thanh toán thành công",
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
                "plate_number": v.plate_number,
                "vehicle_type": v.vehicle_type,
                "capacity": v.capacity,
                "status": v.status,
            }
            for v in vehicles
        ],
        message="Success",
    )

@router.post("/staff")
def add_staff(
    staff_data: RescueStaffCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    staff = rescue_svc.create_staff(db, company.id, staff_data)
    return success_response(
        data={"id": staff.id, "skill_level": staff.skill_level},
        message="Đã thêm nhân viên"
    )


@router.post("/vehicles")
def add_vehicle(
    vehicle_data: RescueVehicleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    vehicle = rescue_svc.create_vehicle(db, company.id, vehicle_data)
    return success_response(
        data={"id": vehicle.id, "plate_number": vehicle.plate_number},
        message="Đã thêm phương tiện",
    )


@router.put("/vehicles/{vehicle_id}")
def update_vehicle(
    vehicle_id: int,
    vehicle_data: RescueVehicleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    vehicle = rescue_svc.update_vehicle(db, vehicle_id, company.id, vehicle_data)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Không tìm thấy phương tiện")

    return success_response(
        data={"id": vehicle.id, "plate_number": vehicle.plate_number},
        message="Đã cập nhật phương tiện",
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
# Customer Vehicles – Personal cars
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/customer/vehicles")
def list_customer_vehicles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Lấy danh sách xe cá nhân của khách hàng."""
    vehicles = rescue_svc.get_customer_vehicles(db, current_user["user_id"])
    return success_response(
        data=[
            {
                "id": v.id,
                "license_plate": v.license_plate,
                "brand": v.brand,
                "model": v.model,
                "year": v.year,
                "fuel_type": v.fuel_type,
            }
            for v in vehicles
        ],
        message="Success",
    )


@router.post("/customer/vehicles")
def add_customer_vehicle(
    vehicle_data: CustomerVehicleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Thêm xe cá nhân mới."""
    vehicle = rescue_svc.create_customer_vehicle(db, current_user["user_id"], vehicle_data)
    return success_response(
        data={"id": vehicle.id, "license_plate": vehicle.license_plate},
        message="Đã thêm xe cá nhân",
    )


@router.put("/customer/vehicles/{vehicle_id}")
def update_customer_vehicle(
    vehicle_id: int,
    vehicle_data: CustomerVehicleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Cập nhật thông tin xe cá nhân."""
    v = rescue_svc.update_customer_vehicle(db, current_user["user_id"], vehicle_id, vehicle_data)
    if not v:
        raise HTTPException(status_code=404, detail="Không tìm thấy xe cá nhân")
    return success_response(data={"id": v.id}, message="Đã cập nhật thông tin xe")


@router.delete("/customer/vehicles/{vehicle_id}")
def delete_customer_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Xóa xe cá nhân."""
    if rescue_svc.customer_vehicle_has_unfinished_requests(db, current_user["user_id"], vehicle_id):
        raise HTTPException(
            status_code=400,
            detail="Không thể xóa xe đang có yêu cầu cứu hộ chưa hoàn thành",
        )
    ok = rescue_svc.delete_customer_vehicle(db, current_user["user_id"], vehicle_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy xe để xóa")
    return success_response(data={}, message="Đã xóa xe cá nhân")


# ──────────────────────────────────────────────────────────────────────────────
# Staff – Company staff
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/staff")
def list_company_staff(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")
    staff = rescue_svc.get_company_staff(db, company.id)
    return success_response(
        data=[
            {
                "id": s.id,
                "skill_level": s.skill_level,
                "status": s.status.value,
            } for s in staff
        ],
        message="Success"
    )

@router.post("/staff")
def add_company_staff(
    staff_data: RescueStaffCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")
    staff = rescue_svc.create_staff(db, company.id, staff_data)
    return success_response(data={"id": staff.id, "skill_level": staff.skill_level}, message="Đã thêm nhân viên")

@router.put("/staff/{staff_id}")
def update_company_staff(
    staff_id: int,
    staff_data: RescueStaffUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")
    staff = rescue_svc.update_staff(db, company.id, staff_id, staff_data)
    if not staff:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
    return success_response(data={"id": staff.id, "status": staff.status.value}, message="Cập nhật thành công")

@router.delete("/staff/{staff_id}")
def delete_company_staff(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    company = rescue_svc.get_company_by_owner_id(db, current_user["user_id"])
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")
    ok = rescue_svc.delete_staff(db, company.id, staff_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
    return success_response(data={}, message="Đã xóa nhân viên")

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

    # Reviews
    reviews_data = []
    reviews = db.query(Review).filter(Review.company_id == company_id).order_by(Review.created_at.desc()).all()

    for rev in reviews:
        reviews_data.append({
            "customer_name": rev.user.full_name,
            "customer_avatar_url": rev.user.avatar_url,
            "rating": rev.rating,
            "comment": rev.comment,
            "created_at": rev.created_at.isoformat()
        })
    
    # My history with this company
    user_id = current_user["user_id"]
    my_history = db.query(RescueRequest).filter(
        RescueRequest.company_id == company_id,
        RescueRequest.user_id == user_id
    ).order_by(RescueRequest.created_at.desc()).all()

    my_history_data = []
    for req in my_history:
        services_names = [rs.service.service_name for rs in req.request_services if rs.service]
        my_history_data.append({
            "id": req.id,
            "services": services_names,
            "total_cost": req.agreed_price or 0,
            "created_at": req.created_at.isoformat(),
            "status": req.status
        })

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
            "my_history": my_history_data
        },
        message="Success"
    )
