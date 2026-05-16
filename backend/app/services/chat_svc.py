from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime

from app.models.communication import Message, Notification
from app.schemas.chat import MessageCreate

def send_message(db: Session, sender_id: int, msg_data: MessageCreate) -> Message:
    new_msg = Message(
        request_id=msg_data.request_id,
        sender_id=sender_id,
        receiver_id=msg_data.receiver_id,
        sender_type=msg_data.sender_type,
        content=msg_data.content,
        sent_time=datetime.utcnow()
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg

def get_messages_by_request(db: Session, request_id: int) -> List[Message]:
    return db.query(Message).filter(Message.request_id == request_id).order_by(Message.sent_time.asc()).all()

def create_notification(db: Session, receiver_id: int, title: str, content: str, request_id: Optional[int] = None) -> Notification:
    notif = Notification(
        receiver_id=receiver_id,
        request_id=request_id,
        title=title,
        content=content,
        sent_time=datetime.utcnow()
    )
    db.add(notif)
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
