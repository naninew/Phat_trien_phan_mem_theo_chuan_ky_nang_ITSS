"""
Admin routes – quản lý users, companies và thống kê hệ thống.
Tất cả endpoints yêu cầu role=admin.
"""
from datetime import datetime, time

import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services import auth_svc, rescue_svc, report_svc, notification_svc
from app.models.user import User
from app.models.company import RescueCompany
from app.utils.response import success_response

router = APIRouter(prefix="/admin", tags=["Admin"])


def _require_admin(current_user: dict):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Chỉ admin mới có quyền truy cập")


def _company_representative_name(company: RescueCompany) -> str:
    if company.representative_name:
        return company.representative_name
    if company.owner:
        return company.owner.full_name
    return "N/A"


# ──────────────────────────────────────────────────────────────────────────────
# Stats
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    stats = report_svc.get_admin_stats(db)
    return success_response(data=stats, message="Success")


@router.get("/stats/charts")
def get_stats_charts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    charts = report_svc.get_chart_stats(db)
    return success_response(data=charts, message="Success")


@router.get("/stats/daily")
def get_stats_daily(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    daily_stats = report_svc.get_daily_request_stats(db, days)
    return success_response(data=daily_stats, message="Success")


@router.get("/reports/export")
def export_reports(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    data = report_svc.get_requests_for_export(db)
    return success_response(data=data, message="Success")


@router.get("/reports/requests")
def get_reports_requests(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    company_id: Optional[int] = Query(None),
    incident_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    data = report_svc.get_request_report(
        db,
        from_date=_parse_date_param(from_date),
        to_date=_parse_date_param(to_date, end_of_day=True),
        company_id=company_id,
        incident_type=incident_type,
        status=status,
    )
    return success_response(data=data, message="Success")


@router.get("/reports/revenue")
def get_reports_revenue(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    data = report_svc.get_revenue_report(
        db,
        from_date=_parse_date_param(from_date),
        to_date=_parse_date_param(to_date, end_of_day=True),
    )
    return success_response(data=data, message="Success")


@router.get("/reports/satisfaction")
def get_reports_satisfaction(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    data = report_svc.get_satisfaction_report(
        db,
        from_date=_parse_date_param(from_date),
        to_date=_parse_date_param(to_date, end_of_day=True),
    )
    return success_response(data=data, message="Success")


def _validate_report_type(report_type: str) -> str:
    allowed = {"requests", "revenue", "satisfaction"}
    if report_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"report_type phải là một trong: {', '.join(sorted(allowed))}",
        )
    return report_type


@router.get("/reports/export/excel")
def export_reports_excel(
    report_type: str = Query(..., alias="report_type"),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    company_id: Optional[int] = Query(None),
    incident_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    report_type = _validate_report_type(report_type)
    content = report_svc.build_excel_report(
        db,
        report_type,
        from_date=_parse_date_param(from_date),
        to_date=_parse_date_param(to_date, end_of_day=True),
        company_id=company_id,
        incident_type=incident_type,
        status=status,
    )
    filename = f"bao_cao_{report_type}.xlsx"
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/reports/export/pdf")
def export_reports_pdf(
    report_type: str = Query(..., alias="report_type"),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    company_id: Optional[int] = Query(None),
    incident_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    report_type = _validate_report_type(report_type)
    content = report_svc.build_pdf_report(
        db,
        report_type,
        from_date=_parse_date_param(from_date),
        to_date=_parse_date_param(to_date, end_of_day=True),
        company_id=company_id,
        incident_type=incident_type,
        status=status,
    )
    filename = f"bao_cao_{report_type}.pdf"
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Content Moderation
# ──────────────────────────────────────────────────────────────────────────────
class DeleteReasonRequest(BaseModel):
    reason: str


def _parse_date_param(value: Optional[str], end_of_day: bool = False) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Định dạng ngày không hợp lệ: {value}")
    if end_of_day and parsed.time() == time.min:
        return datetime.combine(parsed.date(), time.max)
    return parsed


def _community_post_status(post) -> str:
    if not post.is_approved:
        return "DELETED"
    if post.is_closed:
        return "CLOSED"
    return "OPEN"


@router.get("/reviews")
def list_reviews(
    star_filter: Optional[int] = Query(None, ge=1, le=5),
    company_id: Optional[int] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    from app.models.review import Review

    query = db.query(Review)
    if star_filter is not None:
        query = query.filter(Review.rating == star_filter)
    if company_id is not None:
        query = query.filter(Review.company_id == company_id)
    if search:
        query = query.filter(Review.comment.ilike(f"%{search}%"))
    parsed_from = _parse_date_param(from_date)
    parsed_to = _parse_date_param(to_date, end_of_day=True)
    if parsed_from is not None:
        query = query.filter(Review.created_at >= parsed_from)
    if parsed_to is not None:
        query = query.filter(Review.created_at <= parsed_to)

    reviews = query.order_by(Review.created_at.desc()).all()
    return success_response(
        data=[
            {
                "id": r.id,
                "company_id": r.company_id,
                "customer_name": r.user.full_name,
                "company_name": r.company.company_name,
                "rating": r.rating,
                "comment": r.comment,
                "created_at": r.created_at.isoformat(),
            }
            for r in reviews
        ],
        message="Success",
    )


@router.delete("/reviews/{review_id}")
def delete_review(
    review_id: int,
    data: DeleteReasonRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    from app.models.review import Review

    reason = (data.reason or "").strip()
    if not reason:
        raise HTTPException(status_code=422, detail="Lý do xóa là bắt buộc")

    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Không tìm thấy đánh giá")

    user_id = review.user_id
    company = review.company
    db.delete(review)
    db.flush()

    new_avg = db.query(func.avg(Review.rating)).filter(Review.company_id == company.id).scalar() or 0
    new_count = db.query(func.count(Review.id)).filter(Review.company_id == company.id).scalar()
    company.rating_avg = round(float(new_avg), 1)
    company.rating_count = new_count

    notification_svc.send_notification(
        db,
        user_id,
        f"Đánh giá của bạn đã bị xóa vì {reason}",
        notification_type=notification_svc.NotificationType.REVIEW_DELETED,
    )
    db.commit()

    return success_response(data={}, message="Đã xóa đánh giá")


@router.get("/community/posts")
def list_community_posts(
    status_filter: Optional[str] = Query(None),
    incident_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    from app.models.community import CommunityPost

    query = db.query(CommunityPost)
    if status_filter:
        status_upper = status_filter.upper()
        if status_upper == "OPEN":
            query = query.filter(CommunityPost.is_closed.is_(False), CommunityPost.is_approved.is_(True))
        elif status_upper == "CLOSED":
            query = query.filter(CommunityPost.is_closed.is_(True), CommunityPost.is_approved.is_(True))
        elif status_upper == "DELETED":
            query = query.filter(CommunityPost.is_approved.is_(False))
    if incident_type:
        query = query.filter(CommunityPost.incident_type == incident_type)

    posts = query.order_by(CommunityPost.created_at.desc()).all()
    return success_response(
        data=[
            {
                "id": p.id,
                "user_name": p.user.full_name,
                "title": p.title,
                "content": p.content,
                "incident_type": p.incident_type,
                "status": _community_post_status(p),
                "replies_count": len(p.replies),
                "created_at": p.created_at.isoformat(),
            }
            for p in posts
        ],
        message="Success",
    )


@router.delete("/community/posts/{post_id}")
def delete_community_post(
    post_id: int,
    data: DeleteReasonRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    from app.models.community import CommunityPost

    reason = (data.reason or "").strip()
    if not reason:
        raise HTTPException(status_code=422, detail="Lý do xóa là bắt buộc")

    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài đăng")

    user_id = post.user_id
    db.delete(post)
    notification_svc.send_notification(
        db,
        user_id,
        f"Bài đăng của bạn đã bị xóa vì {reason}",
        notification_type=notification_svc.NotificationType.POST_DELETED,
    )
    db.commit()
    return success_response(data={}, message="Đã xóa bài đăng")


# ──────────────────────────────────────────────────────────────────────────────
# Users
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/users")
def list_users(
    role_filter: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    from app.models.request import RescueRequest
    
    from app.models.company import RescueCompany

    # Subquery for counting requests
    req_count_subq = db.query(
        RescueRequest.user_id,
        func.count(RescueRequest.id).label('request_count')
    ).group_by(RescueRequest.user_id).subquery()
    
    q = db.query(
        User, 
        func.coalesce(req_count_subq.c.request_count, 0).label('request_count'),
        RescueCompany.company_name
    ).outerjoin(req_count_subq, User.id == req_count_subq.c.user_id)\
     .outerjoin(RescueCompany, User.id == RescueCompany.owner_id)
          
    if role_filter and role_filter != "all":
        q = q.filter(User.role == role_filter)
    if status_filter and status_filter != "all":
        q = q.filter(User.status == status_filter)
    if search:
        q = q.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.phone.ilike(f"%{search}%"))
        )
        
    total = q.count()
    users_with_count = q.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return success_response(
        data={
            "items": [
                {
                    "id": u.User.id,
                    "username": u.User.username,
                    "full_name": u.company_name if (u.User.role.value == "company_staff" and u.company_name) else u.User.full_name,
                    "email": u.User.email,
                    "phone": u.User.phone,
                    "role": u.User.role.value,
                    "status": u.User.status.value,
                    "created_at": u.User.created_at.isoformat(),
                    "request_count": u.request_count
                }
                for u in users_with_count
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        },
        message="Success",
    )


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    user_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    user = auth_svc.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy user")
    
    if "status" in user_data:
        from app.models.user import AccountStatus
        user.status = AccountStatus(user_data["status"])
    if "role" in user_data:
        user.role = user_data["role"]
    
    db.commit()
    return success_response(data={"id": user.id}, message="Đã cập nhật thông tin user")


@router.get("/users/{user_id}/detail")
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy user")
        
    from app.models.vehicle import Vehicle
    from app.models.request import RescueRequest
    from app.models.payment import Payment
    from app.models.review import Review
    from app.models.company import RescueCompany
    
    vehicles = db.query(Vehicle).filter(Vehicle.customer_id == user.id).all()
    requests = db.query(RescueRequest).filter(RescueRequest.user_id == user.id).order_by(RescueRequest.created_at.desc()).limit(5).all()
    
    # payments where request belongs to user
    payments = db.query(Payment).join(RescueRequest).filter(RescueRequest.user_id == user.id).order_by(Payment.created_at.desc()).all()
    
    reviews = db.query(Review).filter(Review.user_id == user.id).order_by(Review.created_at.desc()).all()
    
    recent_requests = []
    for r in requests:
        company = db.query(RescueCompany).filter(RescueCompany.id == r.company_id).first() if r.company_id else None
        recent_requests.append({
            "id": r.id,
            "status": r.status,
            "incident_type": r.incident_type,
            "created_at": r.created_at.isoformat(),
            "company_name": company.company_name if company else "Chưa tiếp nhận",
            "total_cost": r.agreed_price
        })
        
    payment_history = []
    for p in payments:
        payment_history.append({
            "request_id": p.rescue_request_id,
            "amount": p.amount,
            "method": p.payment_method,
            "status": p.status,
            "created_at": p.created_at.isoformat()
        })
        
    reviews_written = []
    for rv in reviews:
        company = db.query(RescueCompany).filter(RescueCompany.id == rv.company_id).first()
        reviews_written.append({
            "company_name": company.company_name if company else "N/A",
            "rating": rv.rating,
            "comment": rv.comment,
            "created_at": rv.created_at.isoformat()
        })
        
    return success_response(
        data={
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "address": user.address,
            "created_at": user.created_at.isoformat(),
            "status": user.status.value,
            "suspend_reason": user.suspend_reason,
            "vehicles": [
                {
                    "plate": v.license_plate,
                    "brand": v.brand,
                    "model": v.model,
                    "year": v.year
                } for v in vehicles
            ],
            "recent_requests": recent_requests,
            "payment_history": payment_history,
            "reviews_written": reviews_written
        },
        message="Success"
    )


class SuspendRequest(BaseModel):
    reason: str


class RejectRequest(BaseModel):
    reason: str

@router.put("/users/{user_id}/suspend")
def suspend_user(
    user_id: int,
    data: SuspendRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy user")
    if user.id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Không thể tự khóa tài khoản mình")
        
    if not data.reason or len(data.reason.strip()) == 0:
        raise HTTPException(status_code=400, detail="Lý do khóa tài khoản là bắt buộc")
        
    # Check if user has active requests
    from app.models.request import RescueRequest, RequestStatus
    active_requests = db.query(RescueRequest).filter(
        RescueRequest.user_id == user.id,
        RescueRequest.status.notin_([RequestStatus.COMPLETED.value, RequestStatus.CANCELLED.value, RequestStatus.REJECTED.value])
    ).first()
    
    if active_requests:
        raise HTTPException(status_code=400, detail="Không thể khóa tài khoản đang có yêu cầu chưa hoàn thành")
        
    from app.models.user import AccountStatus
    user.status = AccountStatus.SUSPENDED
    user.suspend_reason = data.reason
    notification_svc.send_notification(
        db,
        user.id,
        f"Tài khoản của bạn đã bị tạm khóa. Lý do: {data.reason.strip()}",
        notification_type=notification_svc.NotificationType.ACCOUNT_SUSPENDED,
    )
    db.commit()
    return success_response(data={"id": user.id, "status": user.status.value}, message="Đã khóa tài khoản")

@router.put("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy user")

    from app.models.user import AccountStatus
    user.status = AccountStatus.ACTIVE
    user.suspend_reason = None
    db.commit()
    return success_response(data={"id": user.id, "status": user.status.value}, message="Đã kích hoạt tài khoản")


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Không thể xóa tài khoản của chính mình")

    user = auth_svc.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy user")

    db.delete(user)
    db.commit()
    return success_response(data={}, message="Đã xóa user")


# ──────────────────────────────────────────────────────────────────────────────
# Companies
# ──────────────────────────────────────────────────────────────────────────────
def _company_list_item(c: RescueCompany) -> dict:
    return {
        "id": c.id,
        "company_name": c.company_name,
        "representative_name": _company_representative_name(c),
        "phone": c.hotline,
        "registered_at": c.created_at.isoformat(),
        "rating": c.rating_avg,
        "status_verified": c.is_verified,
        "address": c.address,
        "hotline": c.hotline,
        "area": c.operating_area,
        "business_license": c.business_license,
        "status": c.status,
        "is_verified": c.is_verified,
        "rating_avg": c.rating_avg,
        "rating_count": c.rating_count,
        "service_radius_km": c.service_radius_km,
        "latitude": c.latitude,
        "longitude": c.longitude,
        "created_at": c.created_at.isoformat(),
    }


@router.get("/companies")
def list_companies(
    status_filter: Optional[str] = Query(None),
    area: Optional[str] = Query(None),
    verified_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    companies = rescue_svc.get_all_companies(
        db,
        status_filter=status_filter,
        area=area,
        verified_filter=verified_filter,
        search=search,
    )
    return success_response(
        data=[_company_list_item(c) for c in companies],
        message="Success",
    )


@router.get("/companies/pending")
def list_pending_companies(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    companies = db.query(RescueCompany).filter(
        RescueCompany.is_verified == False,
        RescueCompany.status != "suspended"
    ).order_by(RescueCompany.created_at.desc()).all()
    
    return success_response(
        data=[
            {
                "id": c.id,
                "company_name": c.company_name,
                "representative_name": _company_representative_name(c),
                "phone": c.hotline,
                "business_license_url": c.business_license, # Reusing this field per requirement
                "registered_at": c.created_at.isoformat(),
            }
            for c in companies
        ],
        message="Success",
    )


@router.get("/companies/{company_id}/detail")
def get_company_detail(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    company = db.query(RescueCompany).filter(RescueCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    from app.models.request import RescueRequest
    from app.models.review import Review
    from app.models.user import User
    from app.models.service import Service
    from app.models.vehicle import RescueVehicle
    from app.models.staff import RescueStaff

    if company.status == "pending":
        services = []
        vehicles = []
        staff_list = []
        requests = []
        reviews = []
    else:
        services = db.query(Service).filter(Service.company_id == company.id).all()
        vehicles = db.query(RescueVehicle).filter(RescueVehicle.company_id == company.id).all()
        staff_list = db.query(RescueStaff).filter(RescueStaff.company_id == company.id).all()
        requests = (
            db.query(RescueRequest)
            .filter(RescueRequest.company_id == company.id)
            .order_by(RescueRequest.created_at.desc())
            .limit(10)
            .all()
        )
        reviews = (
            db.query(Review)
            .filter(Review.company_id == company.id)
            .order_by(Review.created_at.desc())
            .all()
        )

    recent_requests = []
    for r in requests:
        customer = db.query(User).filter(User.id == r.user_id).first()
        recent_requests.append({
            "id": r.id,
            "customer_name": customer.full_name if customer else "N/A",
            "status": r.status,
            "incident_type": r.incident_type,
            "created_at": r.created_at.isoformat(),
            "total_cost": r.agreed_price,
        })

    return success_response(
        data={
            "id": company.id,
            "company_name": company.company_name,
            "representative_name": _company_representative_name(company),
            "phone": company.hotline,
            "hotline": company.hotline,
            "address": company.address,
            "area": company.operating_area,
            "business_license": company.business_license,
            "is_verified": company.is_verified,
            "status": company.status,
            "rating_avg": company.rating_avg,
            "rating_count": company.rating_count,
            "created_at": company.created_at.isoformat(),
            "suspend_reason": company.suspend_reason,
            "services": [
                {
                    "name": s.service_name,
                    "price_range": f"{s.base_price:,.0f} đ",
                }
                for s in services
            ],
            "vehicles": [
                {
                    "plate": v.plate_number,
                    "type": v.vehicle_type,
                    "status": v.status,
                }
                for v in vehicles
            ],
            "staff": [
                {
                    "name": f"NV-{s.id}",
                    "role": s.skill_level,
                    "status": s.status.value if hasattr(s.status, "value") else s.status,
                }
                for s in staff_list
            ],
            "recent_requests": recent_requests,
            "reviews": [
                {
                    "customer_name": rv.user.full_name if rv.user else "N/A",
                    "rating": rv.rating,
                    "comment": rv.comment,
                    "created_at": rv.created_at.isoformat(),
                }
                for rv in reviews
            ],
        },
        message="Success",
    )


@router.put("/companies/{company_id}/approve")
def approve_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    company = db.query(RescueCompany).filter(RescueCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")
    if company.is_verified or company.status == "suspended":
        raise HTTPException(status_code=400, detail="Công ty không ở trạng thái chờ xác minh")

    company.is_verified = True
    company.status = "active"
    company.suspend_reason = None
    notification_svc.send_notification_to_company(
        db,
        company.id,
        "Tài khoản đã được xác minh, bạn có thể bắt đầu nhận yêu cầu",
        notification_type=notification_svc.NotificationType.ACCOUNT_VERIFIED,
    )
    db.commit()
    return success_response(
        data={"id": company.id, "is_verified": True, "status": "active"},
        message="Đã duyệt công ty",
    )


@router.put("/companies/{company_id}/reject")
def reject_company(
    company_id: int,
    data: RejectRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    company = db.query(RescueCompany).filter(RescueCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")
    if not data.reason or len(data.reason.strip()) == 0:
        raise HTTPException(status_code=400, detail="Lý do từ chối là bắt buộc")

    company.is_verified = False
    company.status = "suspended"
    company.suspend_reason = data.reason.strip()
    notification_svc.send_notification_to_company(
        db,
        company.id,
        f"Yêu cầu xác minh tài khoản đã bị từ chối. Lý do: {data.reason.strip()}",
        notification_type=notification_svc.NotificationType.ACCOUNT_REJECTED,
    )
    db.commit()
    return success_response(
        data={"id": company.id, "is_verified": False, "status": "suspended"},
        message="Đã từ chối xác minh công ty",
    )


@router.put("/companies/{company_id}/suspend")
def suspend_company(
    company_id: int,
    data: SuspendRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    company = db.query(RescueCompany).filter(RescueCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")
    if not data.reason or len(data.reason.strip()) == 0:
        raise HTTPException(status_code=400, detail="Lý do khóa tài khoản là bắt buộc")
    if rescue_svc.company_has_active_requests(db, company.id):
        raise HTTPException(
            status_code=400,
            detail="Không thể khóa công ty đang có yêu cầu chưa hoàn thành",
        )

    company.status = "suspended"
    company.suspend_reason = data.reason.strip()
    notification_svc.send_notification_to_company(
        db,
        company.id,
        f"Tài khoản công ty đã bị tạm khóa. Lý do: {data.reason.strip()}",
        notification_type=notification_svc.NotificationType.ACCOUNT_SUSPENDED,
    )
    db.commit()
    return success_response(
        data={"id": company.id, "status": "suspended"},
        message="Đã tạm dừng công ty",
    )


@router.put("/companies/{company_id}/activate")
def activate_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    company = db.query(RescueCompany).filter(RescueCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    company.status = "active"
    company.suspend_reason = None
    db.commit()
    return success_response(
        data={"id": company.id, "status": "active"},
        message="Đã kích hoạt công ty",
    )
@router.put("/companies/{company_id}/status")
def update_company_status(
    company_id: int,
    status: str = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    company = db.query(RescueCompany).filter(RescueCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    if status not in ["active", "pending", "suspended"]:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")
        
    company.status = status
    if status == "active":
        company.is_verified = True
    db.commit()
    return success_response(
        data={"id": company.id, "status": company.status},
        message=f"Đã chuyển trạng thái sang {status}",
    )


# ──────────────────────────────────────────────────────────────────────────────
# All Requests (System-wide)
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/requests")
def list_all_requests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    from app.models.request import RescueRequest
    from app.models.user import User
    from app.models.company import RescueCompany
    
    requests = db.query(RescueRequest).order_by(RescueRequest.created_at.desc()).all()
    data = []
    for r in requests:
        customer = db.query(User).filter(User.id == r.user_id).first()
        company = db.query(RescueCompany).filter(RescueCompany.id == r.company_id).first() if r.company_id else None
        data.append({
            "id": r.id,
            "status": r.status,
            "customer_name": customer.full_name if customer else "N/A",
            "company_name": company.company_name if company else "Chưa tiếp nhận",
            "total_cost": r.agreed_price,
            "payment_status": r.payment_status,
            "created_at": r.created_at.isoformat(),
        })
    return success_response(data=data, message="Success")
