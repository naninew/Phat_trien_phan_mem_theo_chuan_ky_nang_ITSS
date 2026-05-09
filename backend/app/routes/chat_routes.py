"""
Chat routes for managing communication between customer and company staff.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any
from datetime import datetime

from app.database import get_db
from app.models.chat import ChatMessage
from app.models.request import RescueRequest
from app.services import auth_svc, rescue_svc
from app.utils.response import success_response

router = APIRouter(prefix="/chat", tags=["Chat & Communication"])

@router.get("/{request_id}", response_model=dict)
def get_chat_history(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Get chat history for a specific rescue request."""
    user_id = current_user["user_id"]
    
    # Check if request exists and user has access
    req = rescue_svc.get_request_by_id(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")
    
    # Check authorization
    role = current_user.get("role")
    if role == "customer" and req.user_id != user_id:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập chat này")
    if role == "company_staff":
        company = rescue_svc.get_company_by_owner_id(db, user_id)
        if not company or req.company_id != company.id:
            raise HTTPException(status_code=403, detail="Không có quyền truy cập chat này")
            
    messages = db.query(ChatMessage).filter(ChatMessage.rescue_request_id == request_id).order_by(ChatMessage.created_at.asc()).all()
    
    return success_response(
        data=[
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "sender_name": m.sender.full_name,
                "message": m.message,
                "created_at": m.created_at.isoformat(),
                "is_me": m.sender_id == user_id
            }
            for m in messages
        ],
        message="Success"
    )

@router.post("/{request_id}", response_model=dict)
def send_message(
    request_id: int,
    message: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Send a new message in a rescue request chat."""
    user_id = current_user["user_id"]
    
    req = rescue_svc.get_request_by_id(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")
    
    # Check authorization (similar to GET)
    role = current_user.get("role")
    if role == "customer" and req.user_id != user_id:
        raise HTTPException(status_code=403, detail="Không có quyền gửi tin nhắn")
    if role == "company_staff":
        company = rescue_svc.get_company_by_owner_id(db, user_id)
        if not company or req.company_id != company.id:
            raise HTTPException(status_code=403, detail="Không có quyền gửi tin nhắn")

    new_msg = ChatMessage(
        rescue_request_id=request_id,
        sender_id=user_id,
        message=message,
        created_at=datetime.utcnow()
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    
    return success_response(
        data={
            "id": new_msg.id,
            "message": new_msg.message,
            "created_at": new_msg.created_at.isoformat()
        },
        message="Message sent"
    )
