"""
Admin routes – quản lý users, companies và thống kê hệ thống.
Tất cả endpoints yêu cầu role=admin.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services import auth_svc, rescue_svc, report_svc
from app.models.user import User
from app.models.company import RescueCompany
from app.utils.response import success_response

router = APIRouter(prefix="/admin", tags=["Admin"])


def _require_admin(current_user: dict):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Chỉ admin mới có quyền truy cập")


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


@router.get("/reports/export")
def export_reports(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    data = report_svc.get_requests_for_export(db)
    return success_response(data=data, message="Success")


# ──────────────────────────────────────────────────────────────────────────────
# Content Moderation
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/reviews")
def list_reviews(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    from app.models.review import Review
    reviews = db.query(Review).order_by(Review.created_at.desc()).all()
    return success_response(
        data=[
            {
                "id": r.id,
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    from app.models.review import Review
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Không tìm thấy đánh giá")
    
    # Update company average rating before deleting
    company = review.company
    db.delete(review)
    db.commit()
    
    # Recalculate average
    new_avg = db.query(func.avg(Review.rating)).filter(Review.company_id == company.id).scalar() or 0
    new_count = db.query(func.count(Review.id)).filter(Review.company_id == company.id).scalar()
    company.rating_avg = round(float(new_avg), 1)
    company.rating_count = new_count
    db.commit()
    
    return success_response(data={}, message="Đã xóa đánh giá")


@router.get("/community/posts")
def list_community_posts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    from app.models.community import CommunityPost
    posts = db.query(CommunityPost).order_by(CommunityPost.created_at.desc()).all()
    return success_response(
        data=[
            {
                "id": p.id,
                "user_name": p.user.full_name,
                "title": p.title,
                "content": p.content,
                "incident_type": p.incident_type,
                "created_at": p.created_at.isoformat(),
            }
            for p in posts
        ],
        message="Success",
    )


@router.delete("/community/posts/{post_id}")
def delete_community_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    from app.models.community import CommunityPost
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài đăng")
    
    db.delete(post)
    db.commit()
    return success_response(data={}, message="Đã xóa bài đăng")


# ──────────────────────────────────────────────────────────────────────────────
# Users
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/users")
def list_users(
    role_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    q = db.query(User)
    if role_filter and role_filter != "all":
        q = q.filter(User.role == role_filter)
    if search:
        q = q.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )
    users = q.order_by(User.created_at.desc()).all()
    return success_response(
        data=[
            {
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name,
                "email": u.email,
                "phone": u.phone,
                "role": u.role.value,
                "status": u.status.value,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ],
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


@router.put("/users/{user_id}/status")
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    user = auth_svc.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy user")
    if user.id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Không thể tự khóa tài khoản mình")

    from app.models.user import AccountStatus
    new_status = AccountStatus.SUSPENDED if user.status == AccountStatus.ACTIVE else AccountStatus.ACTIVE
    updated = auth_svc.update_user_status(db, user_id, new_status)
    return success_response(
        data={"id": updated.id, "status": updated.status.value},
        message="Đã cập nhật trạng thái user",
    )


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
@router.get("/companies")
def list_companies(
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    companies = rescue_svc.get_all_companies(db, status_filter)
    return success_response(
        data=[
            {
                "id": c.id,
                "company_name": c.company_name,
                "address": c.address,
                "hotline": c.hotline,
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
            for c in companies
        ],
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

    company.is_verified = True
    company.status = "active"
    db.commit()
    return success_response(
        data={"id": company.id, "is_verified": True, "status": "active"},
        message="Đã duyệt công ty",
    )


@router.put("/companies/{company_id}/suspend")
def suspend_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    _require_admin(current_user)
    company = db.query(RescueCompany).filter(RescueCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    company.status = "suspended"
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
            "total_cost": r.total_cost,
            "payment_status": r.payment_status,
            "created_at": r.created_at.isoformat(),
        })
    return success_response(data=data, message="Success")
