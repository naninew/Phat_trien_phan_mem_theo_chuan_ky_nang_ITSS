"""
Chat and Notification routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.chat import MessageCreate, MessageResponse, NotificationResponse
from app.services import auth_svc, chat_svc, rescue_svc
from app.utils.response import success_response

router = APIRouter(prefix="/chat", tags=["Chat & Communication"])

# ──────────────────────────────────────────────────────────────────────────────
# Messages
# ──────────────────────────────────────────────────────────────────────────────

async def _broadcast_ws_message(request_id: int, msg):
    try:
        from app.routes.ws_routes import manager, _get_sender_display_name
        from datetime import timedelta
        local_time = msg.sent_time + timedelta(hours=7)
        created_at_str = local_time.strftime("%H:%M %d/%m")
        sender_name = _get_sender_display_name(msg)
        await manager.broadcast_chat_message(
            request_id=request_id,
            message_id=msg.id,
            content=msg.content,
            sender_id=msg.sender_id,
            sender_name=sender_name,
            created_at=created_at_str,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to broadcast WS chat message: {e}", exc_info=True)


@router.post("/messages", response_model=dict)
async def send_message(
    msg_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Gửi tin nhắn mới trong một yêu cầu cứu hộ."""
    # Check authorization (user must be either customer or company owner of the request)
    req = rescue_svc.get_request_by_id(db, msg_data.request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")
    
    user_id = current_user["user_id"]
    role = current_user.get("role")
    
    if role == "customer" and req.user_id != user_id:
        raise HTTPException(status_code=403, detail="Không có quyền gửi tin nhắn")
    if role == "company_staff":
        company = rescue_svc.get_company_by_owner_id(db, user_id)
        if not company or req.company_id != company.id:
            raise HTTPException(status_code=403, detail="Không có quyền gửi tin nhắn")

    msg = chat_svc.send_message(db, user_id, msg_data)
    await _broadcast_ws_message(msg_data.request_id, msg)
    return success_response(data=MessageResponse.from_orm(msg), message="Đã gửi tin nhắn")

@router.get("/messages/{request_id}", response_model=dict)
def get_messages(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Lấy lịch sử tin nhắn của một yêu cầu cứu hộ."""
    req = rescue_svc.get_request_by_id(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")
    
    user_id = current_user["user_id"]
    role = current_user.get("role")
    
    if role == "customer" and req.user_id != user_id:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập chat")
    if role == "company_staff":
        company = rescue_svc.get_company_by_owner_id(db, user_id)
        if not company or req.company_id != company.id:
            raise HTTPException(status_code=403, detail="Không có quyền truy cập chat")

    messages = chat_svc.get_messages_by_request(db, request_id)
    return success_response(data=[MessageResponse.from_orm(m) for m in messages])

@router.get("/{request_id}", response_model=dict)
def get_chat_by_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """API shortcut: Lấy tin nhắn của yêu cầu (match frontend call)."""
    req = rescue_svc.get_request_by_id(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")
    
    user_id = current_user["user_id"]
    role = current_user.get("role")
    
    if role == "customer" and req.user_id != user_id:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập chat")
    if role == "company_staff":
        company = rescue_svc.get_company_by_owner_id(db, user_id)
        if not company or req.company_id != company.id:
            raise HTTPException(status_code=403, detail="Không có quyền truy cập chat")

    messages = chat_svc.get_messages_by_request(db, request_id)
    result = []
    from datetime import timedelta
    for m in messages:
        msg_dict = MessageResponse.from_orm(m).dict()
        msg_dict["is_me"] = m.sender_id == user_id
        msg_dict["message"] = m.content
        local_time = m.sent_time + timedelta(hours=7)
        msg_dict["created_at"] = local_time.strftime("%H:%M %d/%m")
        result.append(msg_dict)
    return success_response(data=result)

@router.post("/{request_id}", response_model=dict)
async def send_chat_by_request(
    request_id: int,
    message: str = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """API shortcut: Gửi tin nhắn (match frontend call)."""
    req = rescue_svc.get_request_by_id(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")
    
    user_id = current_user["user_id"]
    role = current_user.get("role")
    
    if role == "customer" and req.user_id != user_id:
        raise HTTPException(status_code=403, detail="Không có quyền gửi tin nhắn")
    if role == "company_staff":
        company = rescue_svc.get_company_by_owner_id(db, user_id)
        if not company or req.company_id != company.id:
            raise HTTPException(status_code=403, detail="Không có quyền gửi tin nhắn")

    # Determine receiver - frontend doesn't know receiver_id, so we use 0
    sender_type = "customer" if role == "customer" else "company"
    
    msg_data = MessageCreate(
        request_id=request_id,
        receiver_id=0,  # Will be processed by backend logic
        sender_type=sender_type,
        content=message
    )
    msg = chat_svc.send_message(db, user_id, msg_data)
    await _broadcast_ws_message(request_id, msg)
    return success_response(data=MessageResponse.from_orm(msg).dict(), message="Đã gửi tin nhắn")

# ──────────────────────────────────────────────────────────────────────────────
# Notifications
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/notifications", response_model=dict)
def get_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Lấy danh sách thông báo của người dùng hiện tại."""
    notifications = chat_svc.get_notifications_by_user(db, current_user["user_id"], unread_only)
    return success_response(data=[NotificationResponse.from_orm(n) for n in notifications])

@router.put("/notifications/{notification_id}/read", response_model=dict)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
):
    """Đánh dấu thông báo đã đọc."""
    ok = chat_svc.mark_notification_as_read(db, notification_id, current_user["user_id"])
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông báo")
    return success_response(data={}, message="Đã đánh dấu đã đọc")

