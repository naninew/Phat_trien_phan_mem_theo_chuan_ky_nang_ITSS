from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Dict, Any

from app.models.user import User
from app.models.company import RescueCompany
from app.models.request import RescueRequest
from app.models.payment import Payment

def get_admin_stats(db: Session) -> Dict[str, Any]:
    total_users = db.query(func.count(User.id)).scalar()
    total_companies = db.query(func.count(RescueCompany.id)).scalar()
    active_companies = db.query(func.count(RescueCompany.id)).filter(RescueCompany.status == "active").scalar()
    total_requests = db.query(func.count(RescueRequest.id)).scalar()
    pending_requests = db.query(func.count(RescueRequest.id)).filter(RescueRequest.status == "PENDING").scalar()
    total_revenue = db.query(func.sum(Payment.amount)).filter(Payment.status == "success").scalar() or 0
    
    return {
        "total_users": total_users,
        "total_companies": total_companies,
        "active_companies": active_companies,
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "total_revenue": float(total_revenue)
    }

def get_chart_stats(db: Session) -> Dict[str, Any]:
    # 1. Doanh thu theo tháng (6 tháng gần nhất)
    # Vì dùng SQLite nên xử lý format ngày hơi khác một chút
    revenue_data = db.query(
        func.strftime('%Y-%m', Payment.created_at).label('month'),
        func.sum(Payment.amount).label('total')
    ).filter(Payment.status == "success").group_by('month').order_by('month').limit(6).all()
    
    revenue_chart = {
        "labels": [r.month for r in revenue_data],
        "values": [float(r.total) for r in revenue_data]
    }

    # 2. Phân bổ trạng thái yêu cầu
    status_data = db.query(
        RescueRequest.status,
        func.count(RescueRequest.id)
    ).group_by(RescueRequest.status).all()
    
    status_chart = [
        {"name": s[0], "value": s[1]} for s in status_data
    ]

    # 3. Loại sự cố phổ biến
    incident_data = db.query(
        RescueRequest.incident_type,
        func.count(RescueRequest.id)
    ).group_by(RescueRequest.incident_type).all()
    
    incident_chart = {
        "labels": [i[0] for i in incident_data],
        "values": [i[1] for i in incident_data]
    }

    return {
        "revenue_chart": revenue_chart,
        "status_chart": status_chart,
        "incident_chart": incident_chart
    }

def get_company_stats(db: Session, company_id: int) -> Dict[str, Any]:
    total_requests = db.query(func.count(RescueRequest.id)).filter(RescueRequest.company_id == company_id).scalar()
    completed_requests = db.query(func.count(RescueRequest.id)).filter(
        RescueRequest.company_id == company_id, 
        RescueRequest.status == "COMPLETED"
    ).scalar()
    
    # Simple revenue calculation for company
    company_revenue = db.query(func.sum(Payment.amount)).join(RescueRequest).filter(
        RescueRequest.company_id == company_id,
        Payment.status == "success"
    ).scalar() or 0
    
    return {
        "total_requests": total_requests,
        "completed_requests": completed_requests,
        "revenue": float(company_revenue)
    }

def get_requests_for_export(db: Session):
    from app.models.user import User
    from app.models.company import RescueCompany
    
    results = db.query(
        RescueRequest.id,
        RescueRequest.created_at,
        User.full_name.label("customer"),
        RescueCompany.company_name.label("company"),
        RescueRequest.incident_type,
        RescueRequest.status,
        RescueRequest.agreed_price
    ).join(User, RescueRequest.user_id == User.id)\
     .outerjoin(RescueCompany, RescueRequest.company_id == RescueCompany.id)\
     .order_by(RescueRequest.created_at.desc()).all()
    
    return [
        {
            "ID": r.id,
            "Ngày tạo": r.created_at.strftime("%Y-%m-%d %H:%M"),
            "Khách hàng": r.customer,
            "Công ty": r.company or "N/A",
            "Loại sự cố": r.incident_type,
            "Trạng thái": r.status,
            "Chi phí": r.agreed_price or 0
        } for r in results
    ]
