from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime

from app.models.communication import Message, Notification
from app.models.company import RescueCompany
from app.models.request import RescueRequest
from app.schemas.chat import MessageCreate


def _resolve_receiver_id(db: Session, sender_id: int, msg_data: MessageCreate) -> int:
    if msg_data.receiver_id and msg_data.receiver_id > 0:
        return msg_data.receiver_id

    req = db.query(RescueRequest).filter(RescueRequest.id == msg_data.request_id).first()
    if not req:
        raise ValueError("Không tìm thấy yêu cầu cứu hộ")

    if sender_id == req.user_id:
        if not req.company_id:
            raise ValueError("Yêu cầu chưa có đơn vị cứu hộ để nhắn tin")
        company = db.query(RescueCompany).filter(RescueCompany.id == req.company_id).first()
        if not company:
            raise ValueError("Không tìm thấy đơn vị cứu hộ")
        return company.owner_id

    return req.user_id


def send_message(db: Session, sender_id: int, msg_data: MessageCreate) -> Message:
    receiver_id = _resolve_receiver_id(db, sender_id, msg_data)
    new_msg = Message(
        request_id=msg_data.request_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        sender_type=msg_data.sender_type,
        content=msg_data.content,
        sent_time=datetime.utcnow()
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg

def get_messages_by_request(db: Session, request_id: int) -> List[Message]:
    from sqlalchemy.orm import joinedload
    return (
        db.query(Message)
        .options(joinedload(Message.sender))
        .filter(Message.request_id == request_id)
        .order_by(Message.sent_time.asc())
        .all()
    )

def create_notification(db: Session, receiver_id: int, title: str, content: str, request_id: Optional[int] = None) -> Notification:
    from app.services import notification_svc

    notif = notification_svc.send_notification(
        db,
        receiver_id,
        content,
        notification_type=notification_svc.NotificationType.SYSTEM,
        title=title,
        request_id=request_id,
    )
    db.commit()
    db.refresh(notif)
    return notif

def get_notifications_by_user(db: Session, user_id: int, unread_only: bool = False) -> List[Notification]:
    query = db.query(Notification).filter(Notification.receiver_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    return query.order_by(Notification.sent_time.desc()).all()

def mark_notification_as_read(db: Session, notification_id: int, user_id: int) -> bool:
    notif = db.query(Notification).filter(Notification.id == notification_id, Notification.receiver_id == user_id).first()
    if notif:
        notif.is_read = True
        db.commit()
        return True
    return False

def mark_all_notifications_as_read(db: Session, user_id: int) -> int:
    updated = (
        db.query(Notification)
        .filter(Notification.receiver_id == user_id, Notification.is_read == False)
        .update({"is_read": True}, synchronize_session=False)
    )
    db.commit()
    return updated
